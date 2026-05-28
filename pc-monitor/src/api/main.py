from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.dependencies.auth import get_current_user
from src.api.routes.auth import router as auth_router
from src.api.routes.connection import router as connection_router
from src.api.routes.subscription import router as subscription_router
from src.api.routes.publishing import router as publishing_router
from src.api.routes.messages import router as messages_router
from src.api.routes.sensor_measurements import router as sensor_measurements_router

from src.api.exception_handlers import register_exception_handlers
from src.infrastructure.database.connection import Base, engine
import src.infrastructure.models


app = FastAPI(title="MQTT Monitoring API")
register_exception_handlers(app)
Base.metadata.create_all(bind=engine)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

app.include_router(
    connection_router,
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    subscription_router,
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    publishing_router,
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    messages_router,
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    sensor_measurements_router,
    dependencies=[Depends(get_current_user)]
)


@app.get("/")
def root():
    return {"message": "MQTT Monitoring API is running."}