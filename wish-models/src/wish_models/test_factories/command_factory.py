"""Factory class for Command model."""

import factory

from wish_models.command_result.command import Command, CommandType


class CommandFactory(factory.Factory):
    """Factory for creating Command objects."""
    
    class Meta:
        model = Command
    
    command = factory.Faker("sentence")
    tool_type = CommandType.BASH
    tool_parameters = factory.Dict({"timeout": 300})


class BashCommandFactory(CommandFactory):
    """Factory for creating bash commands."""
    
    tool_type = CommandType.BASH
    tool_parameters = factory.Dict({
        "timeout": 300,
        "category": factory.Faker("random_element", elements=["network", "file", "process", "system"])
    })


class MsfconsoleCommandFactory(CommandFactory):
    """Factory for creating msfconsole commands."""
    
    tool_type = CommandType.MSFCONSOLE
    tool_parameters = factory.Dict({
        "module": factory.Faker("file_path"),
        "rhosts": factory.Faker("ipv4"),
        "lhost": factory.Faker("ipv4")
    })