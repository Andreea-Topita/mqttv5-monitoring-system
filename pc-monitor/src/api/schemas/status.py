from pydantic import BaseModel


class MonitorStatusResponse(BaseModel):
    connected: bool
    periodic_publishing: bool
    subscriptions: dict[str, int]