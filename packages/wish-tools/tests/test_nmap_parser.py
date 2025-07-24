"""
Tests for NmapParser implementation
"""

import pytest

from wish_tools.parsers.nmap import NmapParser


class TestNmapParser:
    """Test cases for NmapParser"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = NmapParser()

    def test_tool_name(self):
        """Test tool name property"""
        assert self.parser.tool_name == "nmap"

    def test_supported_formats(self):
        """Test supported formats"""
        formats = self.parser.supported_formats
        assert "xml" in formats
        assert "gnmap" in formats
        assert "normal" in formats

    def test_can_parse_xml(self):
        """Test XML format detection"""
        xml_output = '<?xml version="1.0"?><nmaprun></nmaprun>'
        assert self.parser.can_parse(xml_output, "xml")
        assert self.parser.can_parse(xml_output)  # Auto-detect

    def test_can_parse_gnmap(self):
        """Test grepable format detection"""
        gnmap_output = "# Nmap 7.94 scan\nHost: 192.168.1.1 () Status: Up"
        assert self.parser.can_parse(gnmap_output, "gnmap")
        assert self.parser.can_parse(gnmap_output)  # Auto-detect

    def test_can_parse_normal(self):
        """Test normal format detection"""
        normal_output = "Starting Nmap 7.94\nNmap scan report for 192.168.1.1"
        assert self.parser.can_parse(normal_output, "normal")
        assert self.parser.can_parse(normal_output)  # Auto-detect

    def test_cannot_parse_invalid(self):
        """Test rejection of invalid output"""
        invalid_output = "This is not nmap output"
        assert not self.parser.can_parse(invalid_output)

    def test_parse_xml_simple_host(self):
        """Test parsing simple XML host"""
        xml_output = """<?xml version="1.0"?>
<nmaprun start="1640995200">
    <host>
        <status state="up"/>
        <address addr="192.168.1.100" addrtype="ipv4"/>
        <hostnames>
            <hostname name="test.local"/>
        </hostnames>
        <ports>
            <port protocol="tcp" portid="22">
                <state state="open"/>
                <service name="ssh" product="OpenSSH" version="8.2"/>
            </port>
            <port protocol="tcp" portid="80">
                <state state="open"/>
                <service name="http" product="Apache" version="2.4.41"/>
            </port>
        </ports>
    </host>
</nmaprun>"""

        hosts = self.parser.parse_hosts(xml_output, "xml")
        assert len(hosts) == 1

        host = hosts[0]
        assert host.ip_address == "192.168.1.100"
        assert host.status == "up"
        assert "test.local" in host.hostnames
        assert len(host.services) == 2

        # Check SSH service
        ssh_service = next((s for s in host.services if s.port == 22), None)
        assert ssh_service is not None
        assert ssh_service.protocol == "tcp"
        assert ssh_service.state == "open"
        assert ssh_service.service_name == "ssh"
        assert ssh_service.product == "OpenSSH"
        assert ssh_service.version == "8.2"

        # Check HTTP service
        http_service = next((s for s in host.services if s.port == 80), None)
        assert http_service is not None
        assert http_service.service_name == "http"
        assert http_service.product == "Apache"

    def test_parse_xml_with_os_detection(self):
        """Test parsing XML with OS detection"""
        xml_output = """<?xml version="1.0"?>
<nmaprun start="1640995200">
    <host>
        <status state="up"/>
        <address addr="192.168.1.100" addrtype="ipv4"/>
        <address addr="00:11:22:33:44:55" addrtype="mac"/>
        <os>
            <osmatch name="Linux 5.4" accuracy="95"/>
        </os>
        <ports>
            <port protocol="tcp" portid="22">
                <state state="open"/>
                <service name="ssh" conf="10"/>
            </port>
        </ports>
    </host>
</nmaprun>"""

        hosts = self.parser.parse_hosts(xml_output, "xml")
        assert len(hosts) == 1

        host = hosts[0]
        assert host.os_info == "Linux 5.4"
        assert host.os_confidence == 0.95
        assert host.mac_address == "00:11:22:33:44:55"

        # Check service confidence
        service = host.services[0]
        assert service.confidence == 1.0  # conf="10" maps to 1.0

    def test_parse_xml_empty(self):
        """Test parsing empty XML"""
        xml_output = '<?xml version="1.0"?><nmaprun></nmaprun>'
        hosts = self.parser.parse_hosts(xml_output, "xml")
        assert len(hosts) == 0

    def test_parse_xml_invalid(self):
        """Test parsing invalid XML"""
        xml_output = "<?xml version='1.0'?><invalid>broken"
        hosts = self.parser.parse_hosts(xml_output, "xml")
        assert len(hosts) == 0

    def test_parse_gnmap_simple(self):
        """Test parsing grepable output"""
        gnmap_output = """# Nmap 7.94 scan initiated
Host: 192.168.1.100 (test.local) Status: Up
Host: 192.168.1.100 (test.local) Ports: 22/open/tcp//ssh///, 80/open/tcp//http//Apache httpd 2.4.41/"""

        hosts = self.parser.parse_hosts(gnmap_output, "gnmap")
        assert len(hosts) == 1

        host = hosts[0]
        assert host.ip_address == "192.168.1.100"
        assert host.status == "up"
        assert "test.local" in host.hostnames
        assert len(host.services) == 2

        # Check services
        ssh_service = next((s for s in host.services if s.port == 22), None)
        assert ssh_service is not None
        assert ssh_service.service_name == "ssh"

        http_service = next((s for s in host.services if s.port == 80), None)
        assert http_service is not None
        assert http_service.service_name == "http"
        assert http_service.product == "Apache httpd"
        assert http_service.version == "2.4.41"

    def test_parse_normal_simple(self):
        """Test parsing normal output"""
        normal_output = """Starting Nmap 7.94
Nmap scan report for 192.168.1.100
Host is up (0.001s latency).

PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 8.2p1
80/tcp   open  http    Apache httpd 2.4.41
443/tcp  closed https

Nmap done: 1 IP address (1 host up) scanned"""

        hosts = self.parser.parse_hosts(normal_output, "normal")
        assert len(hosts) == 1

        host = hosts[0]
        assert host.ip_address == "192.168.1.100"
        assert host.status == "up"
        assert len(host.services) == 3

        # Check open services
        ssh_service = next((s for s in host.services if s.port == 22), None)
        assert ssh_service is not None
        assert ssh_service.state == "open"
        assert ssh_service.product == "OpenSSH"

        # Check closed service
        https_service = next((s for s in host.services if s.port == 443), None)
        assert https_service is not None
        assert https_service.state == "closed"

    def test_parse_normal_with_hostname(self):
        """Test parsing normal output with hostname resolution"""
        normal_output = """Nmap scan report for example.com (192.168.1.100)
Host is up.

PORT   STATE SERVICE
22/tcp open  ssh"""

        hosts = self.parser.parse_hosts(normal_output, "normal")
        assert len(hosts) == 1

        host = hosts[0]
        assert host.ip_address == "192.168.1.100"
        assert "example.com" in host.hostnames

    def test_parse_services(self):
        """Test parsing services extraction"""
        xml_output = """<?xml version="1.0"?>
<nmaprun>
    <host>
        <status state="up"/>
        <address addr="192.168.1.100" addrtype="ipv4"/>
        <ports>
            <port protocol="tcp" portid="22">
                <state state="open"/>
                <service name="ssh"/>
            </port>
        </ports>
    </host>
</nmaprun>"""

        services = self.parser.parse_services(xml_output, "xml")
        assert len(services) == 1
        assert services[0].port == 22
        assert services[0].service_name == "ssh"

    def test_parse_findings_xml(self):
        """Test parsing security findings from XML scripts"""
        xml_output = """<?xml version="1.0"?>
<nmaprun start="1640995200">
    <host>
        <address addr="192.168.1.100" addrtype="ipv4"/>
        <ports>
            <port protocol="tcp" portid="80">
                <state state="open"/>
                <script id="http-vuln-cve2017-5638" output="VULNERABLE: CVE-2017-5638"/>
                <script id="http-enum" output="Found /admin/ directory"/>
            </port>
        </ports>
    </host>
</nmaprun>"""

        findings = self.parser.parse_findings(xml_output, "xml")
        assert len(findings) == 2

        # Check vulnerability finding
        vuln_finding = next((f for f in findings if "vuln" in f.title.lower()), None)
        assert vuln_finding is not None
        assert vuln_finding.severity == "high"
        assert "CVE-2017-5638" in vuln_finding.description

        # Check enum finding
        enum_finding = next((f for f in findings if "enum" in f.title.lower()), None)
        assert enum_finding is not None
        assert enum_finding.severity == "medium"

    def test_parse_all(self):
        """Test parsing all information at once"""
        xml_output = """<?xml version="1.0"?>
<nmaprun>
    <host>
        <status state="up"/>
        <address addr="192.168.1.100" addrtype="ipv4"/>
        <ports>
            <port protocol="tcp" portid="22">
                <state state="open"/>
                <service name="ssh"/>
                <script id="ssh-auth-methods" output="Supported methods: publickey"/>
            </port>
        </ports>
    </host>
</nmaprun>"""

        result = self.parser.parse_all(xml_output, "xml")
        assert "hosts" in result
        assert "services" in result
        assert "findings" in result

        assert len(result["hosts"]) == 1
        assert len(result["services"]) == 1
        assert len(result["findings"]) == 1

    def test_get_metadata(self):
        """Test metadata extraction"""
        xml_output = """<?xml version="1.0"?>
<nmaprun scanner="nmap" args="nmap -sS target" start="1640995200" version="7.94">
    <runstats>
        <finished time="1640995300" elapsed="100.5"
                 summary="Nmap done at Fri Dec 31 12:35:00 2021; 1 IP address (1 host up) scanned in 100.50 seconds"/>
        <hosts up="1" down="0" total="1"/>
    </runstats>
</nmaprun>"""

        metadata = self.parser.get_metadata(xml_output, "xml")
        assert metadata["tool"] == "nmap"
        assert metadata["format"] == "xml"
        assert metadata["version"] == "7.94"
        assert metadata["args"] == "nmap -sS target"
        assert metadata["hosts_up"] == "1"
        assert metadata["hosts_total"] == "1"

    def test_detect_format_auto(self):
        """Test automatic format detection"""
        xml_output = '<?xml version="1.0"?><nmaprun></nmaprun>'
        assert self.parser._detect_format(xml_output) == "xml"

        gnmap_output = "# Nmap scan\nHost: 192.168.1.1 () Status: Up"
        assert self.parser._detect_format(gnmap_output) == "gnmap"

        normal_output = "Nmap scan report for 192.168.1.1"
        assert self.parser._detect_format(normal_output) == "normal"

    def test_detect_format_unknown(self):
        """Test format detection with unknown input"""
        with pytest.raises(ValueError, match="Unable to detect Nmap output format"):
            self.parser._detect_format("This is not nmap output")

    def test_parse_unsupported_format(self):
        """Test parsing with unsupported format"""
        with pytest.raises(ValueError, match="Unsupported format"):
            self.parser.parse_hosts("test", "unsupported")

    def test_parse_host_without_ip(self):
        """Test parsing host without IP address"""
        xml_output = """<?xml version="1.0"?>
<nmaprun>
    <host>
        <status state="up"/>
        <hostnames>
            <hostname name="test.local"/>
        </hostnames>
    </host>
</nmaprun>"""

        hosts = self.parser.parse_hosts(xml_output, "xml")
        assert len(hosts) == 0  # Host without IP should be skipped

    def test_parse_service_invalid_port(self):
        """Test parsing service with invalid port"""
        xml_output = """<?xml version="1.0"?>
<nmaprun>
    <host>
        <status state="up"/>
        <address addr="192.168.1.100" addrtype="ipv4"/>
        <ports>
            <port protocol="tcp" portid="invalid">
                <state state="open"/>
                <service name="ssh"/>
            </port>
        </ports>
    </host>
</nmaprun>"""

        hosts = self.parser.parse_hosts(xml_output, "xml")
        assert len(hosts) == 1
        assert len(hosts[0].services) == 0  # Invalid port should be skipped

    def test_parse_service_no_state(self):
        """Test parsing service without state information"""
        xml_output = """<?xml version="1.0"?>
<nmaprun>
    <host>
        <status state="up"/>
        <address addr="192.168.1.100" addrtype="ipv4"/>
        <ports>
            <port protocol="tcp" portid="22">
                <service name="ssh"/>
            </port>
        </ports>
    </host>
</nmaprun>"""

        hosts = self.parser.parse_hosts(xml_output, "xml")
        assert len(hosts) == 1
        assert len(hosts[0].services) == 0  # Service without state should be skipped
