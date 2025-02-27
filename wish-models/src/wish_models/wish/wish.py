import uuid

from pydantic import BaseModel, Field

from wish_models.command_result.command_result import CommandResult
from wish_models.utc_datetime import UtcDatetime

from .wish_state import WishState


class Wish(BaseModel):
    id: str = Field(..., pattern=r"^[0-9a-f]{10}$")
    """ID of the wish."""

    wish: str
    """A `wish` the user has input."""

    state: WishState
    """State of the wish."""

    command_results: list[CommandResult]
    """Results of commands executed"""

    created_at: UtcDatetime
    """Time when the wish was created."""

    finished_at: UtcDatetime | None = None
    """Time when the wish was finished.

    It's None before the wish is finished.
    """

    @classmethod
    def create(cls, wish: str) -> "Wish":
        return cls(
            id=cls._gen_id(),
            wish=wish,
            state=WishState.DOING,
            command_results=[],
            created_at=UtcDatetime.now(),
        )

    @classmethod
    def from_json(cls, wish_json: str) -> "Wish":
        return cls.model_validate_json(wish_json)

    @classmethod
    def from_dict(cls, wish_dict: dict) -> "Wish":
        return cls.model_validate(wish_dict)

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def _gen_id(cls) -> str:
        return uuid.uuid4().hex[:10]

    def update_command_result(self, updated_result: CommandResult) -> None:
        """Update a command result in the command_results list.

        Args:
            updated_result: The updated CommandResult object

        This method finds the command result with the same num as the updated_result
        and replaces it with the updated_result.
        """
        for i, result in enumerate(self.command_results):
            if result.num == updated_result.num:
                self.command_results[i] = updated_result
                return

    def get_command_result_by_num(self, num: int) -> CommandResult | None:
        """Get a command result by its num.

        Args:
            num: The num of the command result to find

        Returns:
            The command result with the specified num, or None if not found
        """
        for result in self.command_results:
            if result.num == num:
                return result
        return None
