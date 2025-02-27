import factory

from wish_models.command_result.log_files import LogFiles


class LogFilesFactory(factory.Factory):
    class Meta:
        model = LogFiles

    stdout = factory.Faker("file_path", extension="log")
    stderr = factory.Faker("file_path", extension="log")
