from pydantic import BaseModel


class ConnectRequest(BaseModel):
    broker_address: str
    broker_port: int
    client_id: str
    username: str
    password: str
    last_will_topic: str
    last_will_message: str
    last_will_qos: int
    last_will_retain: bool = False