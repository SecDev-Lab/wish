import pytest
from pydantic import ValidationError

from wish_models.command_result.command_state import CommandState
from wish_models.test_factories.command_result_factory import CommandResultSuccessFactory
from wish_models.test_factories.wish_factory import WishDoingFactory, WishDoneFactory
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

    def test_update_command_result(self):
        # Create a wish with a command result
        wish = WishDoingFactory.create()
        original_result = wish.command_results[0]
        original_num = original_result.num

        # Create an updated command result with the same num
        updated_result = CommandResultSuccessFactory.create(
            num=original_num,
            exit_code=0,
            state=CommandState.SUCCESS,
            log_summary="Updated log summary"
        )

        # Update the command result
        wish.update_command_result(updated_result)

        # Verify the command result was updated
        assert len(wish.command_results) == 1
        assert wish.command_results[0] == updated_result
        assert wish.command_results[0].state == CommandState.SUCCESS
        assert wish.command_results[0].log_summary == "Updated log summary"

    def test_update_command_result_nonexistent(self):
        # Create a wish with a command result
        wish = WishDoingFactory.create()
        original_result = wish.command_results[0]

        # Create a command result with a different num
        nonexistent_result = CommandResultSuccessFactory.create(
            num=original_result.num + 999,  # Different num
            state=CommandState.SUCCESS
        )

        # Try to update a non-existent command result
        wish.update_command_result(nonexistent_result)

        # Verify the command results were not changed
        assert len(wish.command_results) == 1
        assert wish.command_results[0] == original_result
        assert wish.command_results[0].state == CommandState.DOING

    def test_get_command_result_by_num(self):
        # Create a wish with multiple command results
        wish = WishDoingFactory.create()
        original_result = wish.command_results[0]
        original_num = original_result.num

        # Add another command result
        second_result = CommandResultSuccessFactory.create(
            num=original_num + 1,
            state=CommandState.SUCCESS
        )
        wish.command_results.append(second_result)

        # Test getting existing command results
        result1 = wish.get_command_result_by_num(original_num)
        assert result1 is not None
        assert result1 == original_result

        result2 = wish.get_command_result_by_num(original_num + 1)
        assert result2 is not None
        assert result2 == second_result

        # Test getting non-existent command result
        result3 = wish.get_command_result_by_num(999)
        assert result3 is None
