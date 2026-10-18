import asyncio
import logging
import sqlite3
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from app.config import Settings
from app.database import Database
from app.services.parking import ParkingService
from app.routers.parking import router
from app.routers.realtime_gate import router as realtime_gate_router
from app.services.gate import GateController, GateError
from app.services.realtime import RealtimeHub


def create_app(settings=None, mqtt_factory=None):
    @asynccontextmanager
    async def lifespan(app):
        config = settings or Settings.from_env()
        database = Database(config.db_path)
        database.initialize()
        app.state.parking = ParkingService(database)
        app.state.mqtt = None
        app.state.settings = config
        app.state.realtime = RealtimeHub(app.state.parking, asyncio.get_running_loop())
        unsubscribe = app.state.parking.subscribe(app.state.realtime.publish)
        app.state.gate = GateController(app.state.parking, timeout=config.ack_timeout)
        app.state.gate.start()
        try:
            if config.mqtt_enabled:
                from app.services.mqtt_subscriber import MQTTSubscriber
                factory = mqtt_factory or MQTTSubscriber
                app.state.mqtt = factory(app.state.parking, config)
                app.state.mqtt.ingestor.gate_controller = app.state.gate
                app.state.gate.set_publisher(app.state.mqtt.publish_gate_command)
                app.state.mqtt.start()
            yield
        finally:
            try:
                if app.state.mqtt is not None:
                    await asyncio.to_thread(app.state.mqtt.stop)
            finally:
                await asyncio.to_thread(app.state.gate.stop)
                unsubscribe()
                await app.state.realtime.close()
                del app.state.parking

    config = settings or Settings.from_env()
    app = FastAPI(title='SmartParking Group 21 — Backend Core',version='0.4.0',lifespan=lifespan)
    app.add_middleware(CORSMiddleware,allow_origins=list(config.cors_origins),allow_methods=['GET','POST'],allow_headers=['Content-Type'])
    app.include_router(router)
    app.include_router(realtime_gate_router)

    @app.exception_handler(GateError)
    async def gate_error(request: Request, exc: GateError):
        return JSONResponse(status_code=exc.status,content={'error':{'code':exc.code,'message':exc.message,'command_id':exc.command_id}})

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422,content={'error':{'code':'INVALID_REQUEST','message':'Invalid request body or parameters','command_id':None}})


    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code,content={'error':{'code':'NOT_FOUND' if exc.status_code==404 else 'HTTP_ERROR','message':str(exc.detail),'command_id':None}})

    @app.exception_handler(sqlite3.Error)
    async def database_error(request: Request, exc: sqlite3.Error):
        logging.getLogger(__name__).exception('Database request failed')
        return JSONResponse(status_code=503,content={'error':{'code':'DATABASE_UNAVAILABLE','message':'Database unavailable','command_id':None}})

    return app

app = create_app()
