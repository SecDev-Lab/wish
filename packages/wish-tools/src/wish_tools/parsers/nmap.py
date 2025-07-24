"""
Nmap output parser implementation
"""

import logging
import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from typing import Any, Literal

from wish_models import Finding, Host, Service

from .base import ToolParser

logger = logging.getLogger(__name__)


class NmapParser(ToolParser):
    """Parser for Nmap scan output in various formats"""

    @property
    def tool_name(self) -> str:
        return "nmap"

    @property
    def supported_formats(self) -> list[str]:
        return ["xml", "gnmap", "normal"]

    def can_parse(self, output: str, format_hint: str | None = None) -> bool:
        """Detect if the output is from Nmap"""
        if format_hint == "xml":
            return output.strip().startswith("<?xml") and "<nmaprun" in output
        elif format_hint == "gnmap":
            return "# Nmap" in output and ("Status: Up" in output or "Status: Down" in output)
        elif format_hint == "normal":
            return "Nmap scan report" in output or "Starting Nmap" in output
        else:
            # Auto-detect format
            return self.can_parse(output, "xml") or self.can_parse(output, "gnmap") or self.can_parse(output, "normal")

    def _detect_format(self, output: str) -> str:
        """Auto-detect the output format"""
        if self.can_parse(output, "xml"):
            return "xml"
        elif self.can_parse(output, "gnmap"):
            return "gnmap"
        elif self.can_parse(output, "normal"):
            return "normal"
        else:
            raise ValueError("Unable to detect Nmap output format")

    def parse_hosts(self, output: str, format_hint: str | None = None) -> list[Host]:
        """Parse hosts from Nmap output"""
        if not format_hint:
            format_hint = self._detect_format(output)

        if format_hint == "xml":
            return self._parse_hosts_xml(output)
        elif format_hint == "gnmap":
            return self._parse_hosts_gnmap(output)
        elif format_hint == "normal":
            return self._parse_hosts_normal(output)
        else:
            raise ValueError(f"Unsupported format: {format_hint}")

    def parse_services(self, output: str, format_hint: str | None = None) -> list[Service]:
        """Parse services from Nmap output"""
        hosts = self.parse_hosts(output, format_hint)
        services = []
        for host in hosts:
            services.extend(host.services)
        return services

    def parse_findings(self, output: str, format_hint: str | None = None) -> list[Finding]:
        """Parse security findings from Nmap script output"""
        if not format_hint:
            format_hint = self._detect_format(output)

        if format_hint == "xml":
            return self._parse_findings_xml(output)
        else:
            # Script output is mainly available in XML format
            return []

    def _parse_hosts_xml(self, xml_output: str) -> list[Host]:
        """Parse hosts from Nmap XML output"""
        try:
            root = ET.fromstring(xml_output)  # noqa: S314 - Nmap XML output is trusted
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML: {e}")
            return []

        hosts = []
        scan_time = self._get_scan_time(root)

        for host_elem in root.findall("host"):
            host = self._parse_host_xml(host_elem, scan_time)
            if host:
                hosts.append(host)

        return hosts

    def _parse_host_xml(self, host_elem: ET.Element, scan_time: datetime) -> Host | None:
        """Parse a single host from XML element"""
        # Get host address
        address_elem = host_elem.find("address[@addrtype='ipv4']")
        if address_elem is None:
            # Try IPv6
            address_elem = host_elem.find("address[@addrtype='ipv6']")
        if address_elem is None:
            logger.warning("No IP address found for host")
            return None

        ip_address = address_elem.get("addr", "")
        if not ip_address:
            return None

        # Get host status
        status_elem = host_elem.find("status")
        status: Literal["up", "down", "unknown"] = "unknown"
        if status_elem is not None:
            state = status_elem.get("state", "unknown")
            status = "up" if state == "up" else "down" if state == "down" else "unknown"

        # Get hostnames
        hostnames = []
        hostnames_elem = host_elem.find("hostnames")
        if hostnames_elem is not None:
            for hostname_elem in hostnames_elem.findall("hostname"):
                name = hostname_elem.get("name")
                if name:
                    hostnames.append(name)

        # Get OS information
        os_info = None
        os_confidence = None
        os_elem = host_elem.find("os")
        if os_elem is not None:
            osmatch_elem = os_elem.find("osmatch")
            if osmatch_elem is not None:
                os_info = osmatch_elem.get("name")
                accuracy = osmatch_elem.get("accuracy")
                if accuracy:
                    try:
                        os_confidence = float(accuracy) / 100.0
                    except ValueError:
                        pass

        # Get MAC address
        mac_address = None
        mac_elem = host_elem.find("address[@addrtype='mac']")
        if mac_elem is not None:
            mac_address = mac_elem.get("addr")

        # Create host object
        host = Host(
            ip_address=ip_address,
            hostnames=hostnames,
            status=status,
            os_info=os_info,
            os_confidence=os_confidence,
            mac_address=mac_address,
            discovered_by="nmap",
            discovered_at=scan_time,
            last_seen=scan_time,
            notes=None,
        )

        # Parse services
        ports_elem = host_elem.find("ports")
        if ports_elem is not None:
            for port_elem in ports_elem.findall("port"):
                service = self._parse_service_xml(port_elem, host.id, scan_time)
                if service:
                    host.add_service(service)

        return host

    def _parse_service_xml(self, port_elem: ET.Element, host_id: str, scan_time: datetime) -> Service | None:
        """Parse a single service from XML port element"""
        try:
            port = int(port_elem.get("portid", "0"))
            protocol_raw = port_elem.get("protocol", "tcp")

            if protocol_raw not in ["tcp", "udp"]:
                return None

            protocol: Literal["tcp", "udp"] = protocol_raw  # type: ignore[assignment]

            # Get port state
            state_elem = port_elem.find("state")
            if state_elem is None:
                return None

            state_raw = state_elem.get("state", "unknown")
            if state_raw not in ["open", "closed", "filtered"]:
                return None

            state: Literal["open", "closed", "filtered"] = state_raw  # type: ignore[assignment]

            # Get service information
            service_elem = port_elem.find("service")
            service_name = None
            product = None
            version = None
            extrainfo = None
            confidence = None
            banner = None

            if service_elem is not None:
                service_name = service_elem.get("name")
                product = service_elem.get("product")
                version = service_elem.get("version")
                extrainfo = service_elem.get("extrainfo")
                conf = service_elem.get("conf")
                if conf:
                    try:
                        confidence = float(conf) / 10.0  # Nmap confidence is 0-10
                    except ValueError:
                        pass

                # Construct banner from available info
                banner_parts = []
                if product:
                    banner_parts.append(product)
                if version:
                    banner_parts.append(version)
                if extrainfo:
                    banner_parts.append(f"({extrainfo})")
                if banner_parts:
                    banner = " ".join(banner_parts)

            return Service(
                host_id=host_id,
                port=port,
                protocol=protocol,
                service_name=service_name,
                product=product,
                version=version,
                extrainfo=extrainfo,
                state=state,
                confidence=confidence,
                discovered_by="nmap",
                discovered_at=scan_time,
                banner=banner,
                ssl_info=None,
            )

        except ValueError as e:
            logger.warning(f"Failed to parse service: {e}")
            return None

    def _parse_hosts_gnmap(self, gnmap_output: str) -> list[Host]:
        """Parse hosts from Nmap grepable output"""
        hosts = {}  # Use dict to merge host information
        scan_time = datetime.now(UTC)

        for line in gnmap_output.split("\n"):
            line = line.strip()
            if not line.startswith("Host:"):
                continue

            # Try to parse as status line first
            status_match = re.match(r"Host:\s+(\S+)\s+\(([^)]*)\)\s+Status:\s+(\w+)", line)
            if status_match:
                ip_address = status_match.group(1)
                hostname = status_match.group(2).strip()
                status_str = status_match.group(3).lower()

                status = "up" if status_str == "up" else "down" if status_str == "down" else "unknown"
                hostnames = [hostname] if hostname else []

                if ip_address not in hosts:
                    hosts[ip_address] = Host(
                        ip_address=ip_address,
                        hostnames=hostnames,
                        status=status,
                        discovered_by="nmap",
                        discovered_at=scan_time,
                        last_seen=scan_time,
                    )
                else:
                    hosts[ip_address].status = status
                    if hostname and hostname not in hosts[ip_address].hostnames:
                        hosts[ip_address].hostnames.append(hostname)

            # Try to parse as ports line
            ports_match = re.search(r"Host:\s+(\S+)\s+\(([^)]*)\)\s+Ports:\s+(.+?)(?:\s+Ignored|$)", line)
            if ports_match:
                ip_address = ports_match.group(1)
                hostname = ports_match.group(2).strip()
                ports_str = ports_match.group(3)

                # Ensure host exists
                if ip_address not in hosts:
                    hostnames = [hostname] if hostname else []
                    hosts[ip_address] = Host(
                        ip_address=ip_address,
                        hostnames=hostnames,
                        status="unknown",
                        discovered_by="nmap",
                        discovered_at=scan_time,
                        last_seen=scan_time,
                    )

                # Parse services
                for port_info in ports_str.split(", "):
                    service = self._parse_service_gnmap(port_info.strip(), hosts[ip_address].id, scan_time)
                    if service:
                        hosts[ip_address].add_service(service)

        return list(hosts.values())

    def _parse_service_gnmap(self, port_info: str, host_id: str, scan_time: datetime) -> Service | None:
        """Parse service from grepable port info"""
        # Example: 22/open/tcp//ssh///
        # Example: 80/open/tcp//http//Apache httpd 2.4.41/
        parts = port_info.split("/")
        if len(parts) < 6:  # At least 6 parts required for basic format
            return None

        try:
            port = int(parts[0])
            state = parts[1]
            protocol = parts[2]
            # parts[3] is usually empty
            service_name = parts[4] if parts[4] else None
            # parts[5] is usually empty
            product_version = parts[6] if len(parts) > 6 and parts[6] else None

            if protocol not in ["tcp", "udp"]:
                return None

            if state not in ["open", "closed", "filtered"]:
                return None

            # Parse product and version from combined field
            product = None
            version = None
            if product_version:
                # Try to extract version information
                version_match = re.search(r"(.+?)\s+([\d.]+)", product_version)
                if version_match:
                    product = version_match.group(1)
                    version = version_match.group(2)
                else:
                    product = product_version

            return Service(
                host_id=host_id,
                port=port,
                protocol=protocol,
                service_name=service_name,
                product=product,
                version=version,
                state=state,
                discovered_by="nmap",
                discovered_at=scan_time,
            )

        except (ValueError, IndexError):
            return None

    def _parse_hosts_normal(self, normal_output: str) -> list[Host]:
        """Parse hosts from Nmap normal output"""
        hosts = []
        scan_time = datetime.now(UTC)
        current_host = None

        for line in normal_output.split("\n"):
            line = line.strip()

            # New host section
            if line.startswith("Nmap scan report for"):
                if current_host:
                    hosts.append(current_host)

                current_host = self._parse_host_normal_header(line, scan_time)
                continue

            # Host status
            if current_host and line.startswith("Host is"):
                if "up" in line:
                    current_host.status = "up"
                elif "down" in line:
                    current_host.status = "down"
                continue

            # Port information
            if current_host and "/" in line and ("open" in line or "closed" in line or "filtered" in line):
                service = self._parse_service_normal(line, current_host.id, scan_time)
                if service:
                    current_host.add_service(service)

        # Add the last host
        if current_host:
            hosts.append(current_host)

        return hosts

    def _parse_host_normal_header(self, line: str, scan_time: datetime) -> Host:
        """Parse host information from normal output header"""
        # Example: Nmap scan report for 192.168.1.1
        # Example: Nmap scan report for router.local (192.168.1.1)
        ip_match = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
        hostname_match = re.search(r"for\s+([^\s(]+)", line)

        ip_address = ip_match.group(1) if ip_match else ""
        hostname_part = hostname_match.group(1) if hostname_match else ""

        # If hostname is not an IP, add it to hostnames list
        hostnames = []
        if hostname_part and hostname_part != ip_address:
            hostnames.append(hostname_part)

        return Host(
            ip_address=ip_address,
            hostnames=hostnames,
            status="unknown",
            discovered_by="nmap",
            discovered_at=scan_time,
            last_seen=scan_time,
        )

    def _parse_service_normal(self, line: str, host_id: str, scan_time: datetime) -> Service | None:
        """Parse service from normal output line"""
        # Example: 22/tcp   open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.2
        # Example: 80/tcp   open  http    Apache httpd 2.4.41
        match = re.match(r"(\d+)/(tcp|udp)\s+(open|closed|filtered)\s+(\S+)?(?:\s+(.+))?", line)
        if not match:
            return None

        try:
            port = int(match.group(1))
            protocol = match.group(2)
            state = match.group(3)
            service_name = match.group(4) if match.group(4) else None
            product_info = match.group(5) if match.group(5) else None

            # Parse product and version from product_info
            product = None
            version = None
            if product_info:
                # Try to extract version information
                version_match = re.search(r"(.+?)\s+([\d.]+)", product_info)
                if version_match:
                    product = version_match.group(1)
                    version = version_match.group(2)
                else:
                    product = product_info

            return Service(
                host_id=host_id,
                port=port,
                protocol=protocol,
                service_name=service_name,
                product=product,
                version=version,
                state=state,
                discovered_by="nmap",
                discovered_at=scan_time,
            )

        except ValueError:
            return None

    def _parse_findings_xml(self, xml_output: str) -> list[Finding]:
        """Parse security findings from Nmap XML script output"""
        try:
            root = ET.fromstring(xml_output)  # noqa: S314 - Nmap XML output is trusted
        except ET.ParseError:
            return []

        findings = []
        scan_time = self._get_scan_time(root)

        for host_elem in root.findall("host"):
            address_elem = host_elem.find("address[@addrtype='ipv4']")
            if address_elem is None:
                address_elem = host_elem.find("address[@addrtype='ipv6']")
            if address_elem is None:
                continue

            ip_address = address_elem.get("addr", "")

            # Parse script results
            for script_elem in host_elem.findall(".//script"):
                finding = self._parse_script_finding(script_elem, ip_address, scan_time)
                if finding:
                    findings.append(finding)

        return findings

    def _parse_script_finding(self, script_elem: ET.Element, ip_address: str, scan_time: datetime) -> Finding | None:
        """Parse a security finding from a script element"""
        script_id = script_elem.get("id", "")
        script_output = script_elem.get("output", "")

        if not script_output:
            return None

        # Determine severity based on script type
        severity = "info"
        if any(vuln in script_id for vuln in ["vuln", "exploit", "backdoor", "malware", "trojan", "dos", "injection"]):
            severity = "high"
        elif any(sec in script_id for sec in ["auth", "brute", "crack", "enum", "discovery"]):
            severity = "medium"

        # Determine category based on script type
        category = "other"
        if any(vuln in script_id for vuln in ["vuln", "exploit", "backdoor", "malware", "trojan", "dos", "injection"]):
            category = "vulnerability"
        elif any(sec in script_id for sec in ["auth", "brute", "crack"]):
            category = "weak_authentication"
        elif any(info in script_id for info in ["enum", "discovery", "info"]):
            category = "information_disclosure"

        # Create finding
        return Finding(
            title=f"Nmap Script: {script_id}",
            description=script_output,
            category=category,
            severity=severity,
            target_type="host",
            discovered_by="nmap",
            evidence=script_output,
            discovered_at=scan_time,
        )

    def _get_scan_time(self, root: ET.Element) -> datetime:
        """Extract scan start time from XML root"""
        start_time = root.get("start")
        if start_time:
            try:
                return datetime.fromtimestamp(int(start_time), tz=UTC)
            except (ValueError, OSError):
                pass
        return datetime.now(UTC)

    def get_metadata(self, output: str, format_hint: str | None = None) -> dict[str, Any]:
        """Extract scan metadata from Nmap output"""
        if not format_hint:
            format_hint = self._detect_format(output)

        metadata = {"tool": "nmap", "format": format_hint}

        if format_hint == "xml":
            try:
                root = ET.fromstring(output)  # noqa: S314 - Nmap XML output is trusted
                metadata.update(
                    {
                        "version": root.get("version") or "",
                        "args": root.get("args") or "",
                        "start_time": root.get("start") or "",
                        "version_info": root.get("xmloutputversion") or "",
                    }
                )

                # Get scan statistics
                runstats = root.find("runstats")
                if runstats is not None:
                    finished = runstats.find("finished")
                    if finished is not None:
                        metadata.update(
                            {
                                "end_time": finished.get("time") or "",
                                "elapsed": finished.get("elapsed") or "",
                                "summary": finished.get("summary") or "",
                            }
                        )

                    hosts_elem = runstats.find("hosts")
                    if hosts_elem is not None:
                        metadata.update(
                            {
                                "hosts_up": hosts_elem.get("up") or "",
                                "hosts_down": hosts_elem.get("down") or "",
                                "hosts_total": hosts_elem.get("total") or "",
                            }
                        )

            except ET.ParseError:
                pass

        return metadata
