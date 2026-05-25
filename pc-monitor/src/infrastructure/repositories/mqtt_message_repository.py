from typing import Optional

from sqlalchemy import func, select

from src.infrastructure.database.session_manager import session_scope
from src.infrastructure.models.mqtt_message import MQTTMessage


class MQTTMessageRepository:
    def add_message(
        self,
        topic: str,
        payload: str,
        qos: int,
        direction: str,
        source_client_id: Optional[str] = None
    ) -> MQTTMessage:
        with session_scope() as db:
            item = MQTTMessage(
                topic=topic,
                payload=payload,
                qos=qos,
                direction=direction,
                source_client_id=source_client_id
            )
            db.add(item)
            db.flush()
            db.refresh(item)
            return item

    def get_messages_paginated(
        self,
        topic: Optional[str] = None,
        direction: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[MQTTMessage], int]:
        with session_scope() as db:
            filters = []

            if topic:
                filters.append(MQTTMessage.topic == topic)

            if direction:
                filters.append(MQTTMessage.direction == direction)

            count_stmt = select(func.count()).select_from(MQTTMessage)
            if filters:
                count_stmt = count_stmt.where(*filters)

            total_items = db.execute(count_stmt).scalar_one()

            stmt = select(MQTTMessage)
            if filters:
                stmt = stmt.where(*filters)

            stmt = stmt.order_by(MQTTMessage.id.desc())
            stmt = stmt.offset((page - 1) * page_size).limit(page_size)

            items = db.execute(stmt).scalars().all()

            return items, total_items