import factory

from wish_models.utc_datetime import UtcDatetime


class UtcDatetimeFactory(factory.Factory):
    class Meta:
        model = UtcDatetime

    v = factory.Faker("date_time_this_decade", tzinfo=None)
