from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from src.database.connection import SessionLocal
from src.models.mqtt_message import MQTTMessage


class MQTTMessageRepository:
    def add_message(
        self,
        topic: str,
        payload: str,
        qos: int,
        direction: str,
        source_client_id: Optional[str] = None
    ) -> None:
        db = SessionLocal()
        try:
            item = MQTTMessage(
                topic=topic,
                payload=payload,
                qos=qos,
                direction=direction,
                source_client_id=source_client_id
            )
            db.add(item)
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise
        finally:
            db.close()

    def get_messages_paginated(
        self,
        topic: Optional[str] = None,
        direction: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        db = SessionLocal()
        try:
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

            rows = db.execute(stmt).scalars().all()

            items = [
                {
                    "id": row.id,
                    "topic": row.topic,
                    "payload": row.payload,
                    "qos": row.qos,
                    "direction": row.direction,
                    "source_client_id": row.source_client_id,
                    "created_at": row.created_at.isoformat() if row.created_at else None
                }
                for row in rows
            ]

            total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 0

            return {
                "items": items,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_previous": page > 1
                }
            }
        finally:
            db.close()