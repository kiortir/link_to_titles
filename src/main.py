from fastapi import FastAPI

from src.titles.routes import router as titles_router


def init_routers(app: FastAPI) -> FastAPI:
    app.include_router(titles_router, tags=["titles"])
    return app


def get_app() -> FastAPI:
    app: FastAPI = FastAPI()
    init_routers(app)
    return app


app = get_app()
