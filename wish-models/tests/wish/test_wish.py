import pytest
from pydantic import ValidationError

from wish_models.test_factories.command_result_factory import CommandResultSuccessFactory
from wish_models.test_factories.wish_factory import WishDoneFactory
from wish_models.utc_datetime import UtcDatetime
from wish_models.wish.wish import Wish
from wish_models.wish.wish_state import WishState


class TestWish:
    def test_wish_creation_valid(self):
        now = UtcDatetime.now()
        wish_data = {
            "id": "abcdef1234",
            "wish": "Test wish",
            "state": WishState.DONE.value,
            "command_results": [CommandResultSuccessFactory.create()],
            "created_at": str(now),
            "finished_at": str(now),
        }
        wish = Wish.from_dict(wish_data)
        assert wish.id == "abcdef1234"
        assert wish.wish == "Test wish"
        assert wish.state == WishState.DONE
        assert len(wish.command_results) == 1
        assert isinstance(wish.created_at, UtcDatetime)
        assert isinstance(wish.finished_at, UtcDatetime)

    def test_wish_invalid_id(self):
        now = UtcDatetime.now()
        wish_data = {
            "id": "invalid_id",  # Does not match 10 hex digits
            "wish": "Invalid id wish",
            "state": WishState.DONE.value,
            "command_results": [],
            "created_at": str(now),
            "finished_at": str(now),
        }
        with pytest.raises(ValidationError):
            Wish.model_validate(wish_data)

    def test_wish_serde(self):
        wish = WishDoneFactory.create()
        wish_json = wish.to_json()
        wish2 = Wish.from_json(wish_json)
        assert wish == wish2

    def test_create(self):
        wish = Wish.create("Test wish")
        assert len(wish.id) == 10
        assert wish.wish == "Test wish"
        assert wish.state == WishState.DOING
        assert wish.command_results == []
        assert isinstance(wish.created_at, UtcDatetime)
        assert wish.finished_at is None
