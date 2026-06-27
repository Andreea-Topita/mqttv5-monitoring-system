from typing import Optional

from sqlalchemy import func, select

from src.domain.entities.mqtt_message_record import MqttMessageRecord
from src.infrastructure.database.session_manager import session_scope
from src.infrastructure.mappers.mqtt_message_mapper import to_mqtt_message_record
from src.infrastructure.models.mqtt_message import MQTTMessage


class MQTTMessageRepository:
    def add_message(
        self,
        topic: str,
        payload: str,
        qos: int,
        direction: str,
        source_client_id: Optional[str] = None
    ) -> MqttMessageRecord:
        with session_scope() as db:
            item = MQTTMessage(
                topic=topic,
                payload=payload,
                qos=qos,
                direction=direction,
                source_client_id=source_client_id
            )
            # salvare mesaj mqtt original in baza de date
            db.add(item)
            db.flush()
            db.refresh(item)

            return to_mqtt_message_record(item)

    # returneaza tuplu de lista mesajelor din pagina curenta si nr total de mesaje
    def get_messages_paginated(
        self,
        topic: Optional[str] = None,
        direction: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[MqttMessageRecord], int]:
        with session_scope() as db:
            filters = []

            # filtre adaugate doar daca parametrul a fost primit
            if topic:
                filters.append(MQTTMessage.topic == topic)

            if direction:
                filters.append(MQTTMessage.direction == direction)

            # numar total de mesaje care respecta filtrele
            count_stmt = select(func.count()).select_from(MQTTMessage)
            if filters:
                count_stmt = count_stmt.where(*filters)

            # executie query si obtinere numar total de mesaje care respecta filtrele
            total_items = db.execute(count_stmt).scalar_one()

            # selectare pagina curenta de mesaje care respecta filtrele
            stmt = select(MQTTMessage)
            if filters:
                stmt = stmt.where(*filters)

            # cele mai recente mesaje care apar primele
            stmt = stmt.order_by(MQTTMessage.id.desc())
            # paginare, se sare peste mesajele din paginile anterioare si se limiteaza la nr de mesaje cerut
            stmt = stmt.offset((page - 1) * page_size).limit(page_size)

            # executie query si obtinere rezultate in lista
            items = db.execute(stmt).scalars().all()

            records = [
                to_mqtt_message_record(item)
                for item in items
            ]

            return records, total_items