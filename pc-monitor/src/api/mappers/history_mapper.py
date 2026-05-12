from collections.abc import Sequence

from src.api.schemas.history import (
    MessageHistoryDataResponse,
    MessageHistoryItemResponse,
    MessageHistoryResponse,
    PaginationResponse
)
from src.core.pagination import PaginationResult
from src.models.mqtt_message import MQTTMessage


def to_message_history_response(
    rows: Sequence[MQTTMessage],
    pagination: PaginationResult
) -> MessageHistoryResponse:
    items = [
        MessageHistoryItemResponse.model_validate(row)
        for row in rows
    ]

    return MessageHistoryResponse(
        success=True,
        data=MessageHistoryDataResponse(
            items=items,
            pagination=PaginationResponse(
                page=pagination.page,
                page_size=pagination.page_size,
                total_items=pagination.total_items,
                total_pages=pagination.total_pages,
                has_next=pagination.has_next,
                has_previous=pagination.has_previous
            )
        )
    )