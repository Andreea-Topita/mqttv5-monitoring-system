from typing import Optional

from pydantic import BaseModel

class DeviceTopicsResponse(BaseModel):
    status: str
    temperatura: str
    umiditate: str
    config: str


class DeviceStatusResponse(BaseModel):
    client_id: str
    status: str
    capabilities: list[str]
    last_seen: Optional[float] = None
    topics: DeviceTopicsResponse


class MonitorStatusResponse(BaseModel):
    connected: bool
    periodic_publishing: bool
    subscriptions: dict[str, int]
    devices: list[DeviceStatusResponse] = []

class MonitorStatusResponse(BaseModel):
    connected: bool
    periodic_publishing: bool
    subscriptions: dict[str, int]