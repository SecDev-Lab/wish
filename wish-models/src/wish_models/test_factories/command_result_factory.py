import factory

from wish_models import CommandResult, CommandState
from wish_models.test_factories.command_factory import BashCommandFactory
from wish_models.test_factories.log_files_factory import LogFilesFactory
from wish_models.test_factories.utc_datetime_factory import UtcDatetimeFactory


class CommandResultSuccessFactory(factory.Factory):
    class Meta:
        model = CommandResult

    num = factory.Faker("random_int", min=1)
    command = factory.SubFactory(BashCommandFactory)
    state = CommandState.SUCCESS
    timeout_sec = 60
    exit_code = 0
    log_summary = factory.Faker("sentence")
    log_files = factory.SubFactory(LogFilesFactory)
    created_at = factory.SubFactory(UtcDatetimeFactory)
    finished_at = factory.SubFactory(UtcDatetimeFactory)


class CommandResultDoingFactory(factory.Factory):
    class Meta:
        model = CommandResult

    num = factory.Faker("random_int", min=1)
    command = factory.SubFactory(BashCommandFactory)
    state = CommandState.DOING
    timeout_sec = 60
    log_files = factory.SubFactory(LogFilesFactory)
    created_at = factory.SubFactory(UtcDatetimeFactory)
