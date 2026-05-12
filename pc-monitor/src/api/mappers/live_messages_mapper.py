from collections.abc import Sequence

from src.api.schemas.live_messages import (
    LiveMessageItemResponse,
    LiveMessagesResponse
)


def to_live_messages_response(rows: Sequence[dict]) -> LiveMessagesResponse:
    items = [
        LiveMessageItemResponse.model_validate(row)
        for row in rows
    ]

    return LiveMessagesResponse(
        success=True,
        messages=items
    )