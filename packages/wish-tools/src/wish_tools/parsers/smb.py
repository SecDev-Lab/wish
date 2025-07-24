"""
SMB tools output parsers (smbclient, enum4linux)
"""

import re
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from wish_models import Finding, Host, Service

from .base import ToolParser


class SmbclientParser(ToolParser):
    """Parser for smbclient output"""

    @property
    def tool_name(self) -> str:
        return "smbclient"

    @property
    def supported_formats(self) -> list[str]:
        return ["text"]

    def can_parse(self, output: str, format_hint: str | None = None) -> bool:
        """Check if this looks like smbclient output"""
        # Look for characteristic smbclient patterns
        indicators = [
            "Sharename",
            "Anonymous login successful",
            "SMB1 for workgroup listing",
            "Workgroup",
            "Server               Comment",
        ]
        return any(indicator in output for indicator in indicators)

    def parse_hosts(self, output: str, format_hint: str | None = None) -> list[Host]:
        """Extract host information from smbclient output"""
        hosts = []

        # Extract OS information from banner if available
        os_info = None
        for line in output.split("\n"):
            if "IPC Service" in line and "(" in line:
                # Extract OS info from IPC Service line
                match = re.search(r"\(([^)]+)\)", line)
                if match:
                    os_info = match.group(1)
                    break

        # Try to extract target IP from context
        target_ip = self._extract_target_ip(output)

        # Only create host if we have a valid IP address
        if target_ip and target_ip != "unknown":
            host = Host(
                id=str(uuid4()),
                ip_address=target_ip,
                status="up",
                discovered_by="smbclient",
                discovered_at=datetime.now(UTC),
                os_info=os_info,
            )
            hosts.append(host)

        return hosts

    def parse_services(self, output: str, format_hint: str | None = None) -> list[Service]:
        """Extract SMB service information"""
        services = []

        target_ip = self._extract_target_ip(output)
        if not target_ip:
            target_ip = "unknown"

        host_id = str(uuid4())

        # SMB service is running if we got any response
        if self.can_parse(output):
            # Add SMB service entries
            for port in [139, 445]:
                service = Service(
                    id=str(uuid4()),
                    host_id=host_id,
                    port=port,
                    protocol="tcp",
                    service_name="microsoft-ds" if port == 445 else "netbios-ssn",
                    state="open",
                    discovered_by="smbclient",
                    discovered_at=datetime.now(UTC),
                )
                services.append(service)

        return services

    def parse_findings(self, output: str, format_hint: str | None = None) -> list[Finding]:
        """Extract security findings from smbclient output"""
        findings = []
        target_ip = self._extract_target_ip(output)

        # Check for anonymous login success
        if "Anonymous login successful" in output:
            finding = Finding(
                id=str(uuid4()),
                title="SMB Anonymous Access Allowed",
                description="Anonymous (null session) access is allowed to SMB shares",
                category="vulnerability",
                severity="medium",
                target_type="host",
                discovered_by="smbclient",
                discovered_at=datetime.now(UTC),
                evidence="Anonymous login successful observed in smbclient output",
                host_id=target_ip,
                status="confirmed",
                recommendation="Disable anonymous access to SMB shares unless required for business purposes",
            )
            findings.append(finding)

        # Parse shares and identify potentially interesting ones
        shares = self._parse_shares(output)
        for share in shares:
            # Flag interesting shares
            if share["name"].lower() in ["tmp", "temp", "backup", "share", "public"]:
                finding = Finding(
                    id=str(uuid4()),
                    title=f"Potentially Interesting SMB Share: {share['name']}",
                    description=f"SMB share '{share['name']}' may contain sensitive information",
                    category="information_disclosure",
                    severity="low",
                    target_type="host",
                    discovered_by="smbclient",
                    discovered_at=datetime.now(UTC),
                    evidence=f"Share: {share['name']} ({share['type']}) - {share['comment']}",
                    host_id=target_ip,
                    status="investigating",
                    recommendation=f"Investigate the contents of the '{share['name']}' share for sensitive data",
                )
                findings.append(finding)

        return findings

    def get_metadata(self, output: str, format_hint: str | None = None) -> dict[str, Any]:
        """Extract metadata from smbclient output"""
        metadata = {
            "shares": self._parse_shares(output),
            "workgroup": self._parse_workgroup(output),
            "servers": self._parse_servers(output),
        }
        return metadata

    def _parse_shares(self, output: str) -> list[dict[str, Any]]:
        """Parse share information from output"""
        shares = []
        in_share_section = False

        for line in output.split("\n"):
            line = line.strip()

            # Check for share section start
            if "Sharename" in line and "Type" in line and "Comment" in line:
                in_share_section = True
                continue
            elif in_share_section and line.startswith("-"):
                continue
            elif in_share_section and not line:
                in_share_section = False
                continue
            elif in_share_section and ("Reconnecting" in line or "Server" in line):
                # End of share section
                in_share_section = False
                continue

            if in_share_section and line:
                # Parse share line using whitespace splitting carefully
                # Share lines look like: "sharename   type      comment"
                # Split on whitespace but preserve comment with spaces
                parts = line.split(None, 2)  # Split into max 3 parts
                if len(parts) >= 2:
                    share_name = parts[0]
                    share_type = parts[1]
                    comment = parts[2] if len(parts) > 2 else ""

                    shares.append(
                        {
                            "name": share_name,
                            "type": share_type,
                            "comment": comment,
                        }
                    )

        return shares

    def _parse_workgroup(self, output: str) -> str | None:
        """Parse workgroup information"""
        in_workgroup_section = False

        for line in output.split("\n"):
            line = line.strip()

            # Look for workgroup section header
            if "Workgroup" in line and "Master" in line:
                in_workgroup_section = True
                continue
            elif in_workgroup_section and line.startswith("-"):
                continue
            elif in_workgroup_section and not line:
                in_workgroup_section = False
                continue

            # Parse workgroup entries in the workgroup section
            if in_workgroup_section and line:
                parts = line.split()
                if len(parts) >= 2:
                    workgroup_name = parts[0]
                    # Skip if it looks like a share name
                    if workgroup_name not in ["IPC$", "ADMIN$", "print$"]:
                        return workgroup_name

        return None

    def _parse_servers(self, output: str) -> list[dict[str, str]]:
        """Parse server information"""
        servers = []
        in_server_section = False

        for line in output.split("\n"):
            line = line.strip()

            if "Server" in line and "Comment" in line:
                in_server_section = True
                continue
            elif in_server_section and line.startswith("-"):
                continue
            elif in_server_section and not line:
                in_server_section = False
                continue

            if in_server_section and line:
                parts = line.split(None, 1)  # Split into at most 2 parts
                if len(parts) >= 1:
                    server_name = parts[0]
                    comment = parts[1] if len(parts) > 1 else ""
                    servers.append(
                        {
                            "name": server_name,
                            "comment": comment,
                        }
                    )

        return servers

    def _extract_target_ip(self, output: str) -> str | None:
        """Try to extract target IP from output context"""
        # This is a basic implementation - in practice, the target IP
        # should be passed from the command execution context
        return None


class Enum4linuxParser(ToolParser):
    """Parser for enum4linux output"""

    @property
    def tool_name(self) -> str:
        return "enum4linux"

    @property
    def supported_formats(self) -> list[str]:
        return ["text"]

    def can_parse(self, output: str, format_hint: str | None = None) -> bool:
        """Check if this looks like enum4linux output"""
        indicators = [
            "enum4linux",
            "Enumerating",
            "SMB Dialect",
            "Domain Information",
            "Share Enumeration",
            "Password Policy Information",
        ]
        return any(indicator in output for indicator in indicators)

    def parse_hosts(self, output: str, format_hint: str | None = None) -> list[Host]:
        """Extract host information from enum4linux output"""
        hosts = []

        # Extract OS and domain information
        os_info = {}

        # Look for OS information
        for line in output.split("\n"):
            if "OS=" in line:
                os_match = re.search(r"OS=([^,\]]+)", line)
                if os_match:
                    os_info["os"] = os_match.group(1).strip()

            if "Domain=" in line:
                domain_match = re.search(r"Domain=([^,\]]+)", line)
                if domain_match:
                    os_info["domain"] = domain_match.group(1).strip()

        target_ip = self._extract_target_ip(output)

        if target_ip or os_info:
            host = Host(
                id=str(uuid4()),
                ip_address=target_ip or "unknown",
                status="up",
                discovered_by="enum4linux",
                discovered_at=datetime.now(UTC),
                os_info=os_info if os_info else None,
            )
            hosts.append(host)

        return hosts

    def parse_services(self, output: str, format_hint: str | None = None) -> list[Service]:
        """Extract service information from enum4linux output"""
        services = []

        target_ip = self._extract_target_ip(output)
        if not target_ip:
            target_ip = "unknown"

        host_id = str(uuid4())

        # enum4linux implies SMB services are available
        if self.can_parse(output):
            for port in [139, 445]:
                service = Service(
                    id=str(uuid4()),
                    host_id=host_id,
                    port=port,
                    protocol="tcp",
                    service_name="microsoft-ds" if port == 445 else "netbios-ssn",
                    state="open",
                    discovered_by="enum4linux",
                    discovered_at=datetime.now(UTC),
                )
                services.append(service)

        return services

    def parse_findings(self, output: str, format_hint: str | None = None) -> list[Finding]:
        """Extract security findings from enum4linux output"""
        findings = []
        target_ip = self._extract_target_ip(output)

        # Check for various security issues
        if "Got domain/workgroup name:" in output:
            workgroup_match = re.search(r"Got domain/workgroup name: ([^\n]+)", output)
            if workgroup_match:
                workgroup = workgroup_match.group(1).strip()
                finding = Finding(
                    id=str(uuid4()),
                    title=f"SMB Domain/Workgroup Information Disclosed: {workgroup}",
                    description="SMB domain/workgroup information was successfully enumerated",
                    category="information_disclosure",
                    severity="low",
                    target_type="host",
                    discovered_by="enum4linux",
                    discovered_at=datetime.now(UTC),
                    evidence=f"Domain/Workgroup: {workgroup}",
                    host_id=target_ip,
                    status="confirmed",
                    recommendation="Consider restricting anonymous access to SMB if not required",
                )
                findings.append(finding)

        # Check for user enumeration
        if "Users on" in output and ":" in output:
            finding = Finding(
                id=str(uuid4()),
                title="SMB User Enumeration Successful",
                description="User accounts were successfully enumerated via SMB",
                category="information_disclosure",
                severity="medium",
                target_type="host",
                discovered_by="enum4linux",
                discovered_at=datetime.now(UTC),
                evidence="User enumeration successful - check full enum4linux output for user list",
                host_id=target_ip,
                status="confirmed",
                recommendation="Restrict anonymous SMB access and disable user enumeration if not required",
            )
            findings.append(finding)

        # Check for share enumeration
        if "Enumerating shares" in output or "Share Enumeration" in output:
            finding = Finding(
                id=str(uuid4()),
                title="SMB Share Enumeration Successful",
                description="SMB shares were successfully enumerated",
                category="information_disclosure",
                severity="low",
                target_type="host",
                discovered_by="enum4linux",
                discovered_at=datetime.now(UTC),
                evidence="Share enumeration successful - check output for share details",
                host_id=target_ip,
                status="confirmed",
                recommendation="Review share permissions and disable unnecessary shares",
            )
            findings.append(finding)

        return findings

    def get_metadata(self, output: str, format_hint: str | None = None) -> dict[str, Any]:
        """Extract metadata from enum4linux output"""
        metadata = {
            "domain_info": self._parse_domain_info(output),
            "shares": self._parse_enum4linux_shares(output),
            "users": self._parse_users(output),
            "groups": self._parse_groups(output),
        }
        return metadata

    def _parse_domain_info(self, output: str) -> dict[str, str]:
        """Parse domain information"""
        domain_info = {}

        # Look for domain/workgroup information
        workgroup_match = re.search(r"Got domain/workgroup name: ([^\n]+)", output)
        if workgroup_match:
            domain_info["workgroup"] = workgroup_match.group(1).strip()

        # Look for OS information
        os_match = re.search(r"OS=([^,\]]+)", output)
        if os_match:
            domain_info["os"] = os_match.group(1).strip()

        return domain_info

    def _parse_enum4linux_shares(self, output: str) -> list[dict[str, str]]:
        """Parse share information from enum4linux output"""
        shares = []

        # This would need more sophisticated parsing based on enum4linux output format
        # For now, return empty list as enum4linux share parsing is complex

        return shares

    def _parse_users(self, output: str) -> list[str]:
        """Parse user information"""
        users = []

        # Look for user enumeration sections
        in_user_section = False
        for line in output.split("\n"):
            if "Users on" in line:
                in_user_section = True
                continue
            elif in_user_section and line.strip():
                # Simple user extraction - would need refinement
                if line.strip().startswith("user:"):
                    user = line.split(":", 1)[1].strip()
                    users.append(user)
            elif in_user_section and not line.strip():
                in_user_section = False

        return users

    def _parse_groups(self, output: str) -> list[str]:
        """Parse group information"""
        groups = []

        # Similar logic for groups
        in_group_section = False
        for line in output.split("\n"):
            if "Groups on" in line:
                in_group_section = True
                continue
            elif in_group_section and line.strip():
                if line.strip().startswith("group:"):
                    group = line.split(":", 1)[1].strip()
                    groups.append(group)
            elif in_group_section and not line.strip():
                in_group_section = False

        return groups

    def _extract_target_ip(self, output: str) -> str | None:
        """Try to extract target IP from output context"""
        # Look for target IP in enum4linux output
        target_match = re.search(r"Target Information for ([0-9.]+)", output)
        if target_match:
            return target_match.group(1)

        # Alternative patterns
        ip_pattern = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
        matches = re.findall(ip_pattern, output)
        if matches:
            return matches[0]  # Return first IP found

        return None
