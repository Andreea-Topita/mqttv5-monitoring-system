from src.domain.entities.user_record import UserRecord
from src.infrastructure.models.user import User

# USER legat de sesiune SqlAlchemy, UserRecord legat de domeniu
def to_user_record(item: User) -> UserRecord:
    return UserRecord(
        id=item.id,
        username=item.username,
        email=item.email,
        password_hash=item.password_hash,
        created_at=item.created_at
    )