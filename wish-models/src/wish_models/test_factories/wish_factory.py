import factory

from wish_models.test_factories.command_result_factory import CommandResultDoingFactory, CommandResultSuccessFactory
from wish_models.test_factories.utc_datetime_factory import UtcDatetimeFactory
from wish_models.wish.wish import Wish
from wish_models.wish.wish_state import WishState


class WishDoneFactory(factory.Factory):
    class Meta:
        model = Wish

    id = "abcdef1234"
    wish = factory.Faker("sentence")
    state = WishState.DONE
    command_results = factory.List([factory.SubFactory(CommandResultSuccessFactory)])
    created_at = factory.SubFactory(UtcDatetimeFactory)
    finished_at = factory.SubFactory(UtcDatetimeFactory)


class WishDoingFactory(factory.Factory):
    class Meta:
        model = Wish

    id = "abcdef1234"
    wish = factory.Faker("sentence")
    state = WishState.DOING
    command_results = factory.List([factory.SubFactory(CommandResultDoingFactory)])
    created_at = factory.SubFactory(UtcDatetimeFactory)
