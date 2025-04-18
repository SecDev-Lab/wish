"""
CommandInput のファクトリクラス
"""

import factory

from wish_models.command_result import CommandInput


class CommandInputFactory(factory.Factory):
    class Meta:
        model = CommandInput

    command = factory.Faker("sentence")
    explanation = factory.Faker("paragraph")
