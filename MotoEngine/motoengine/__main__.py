from fastapi import FastAPI

from .config import settings
from .route import api_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.include_router(api_router)
    return app


def main() -> None:
    print(f"MotoEngine scaffold is ready. ENV: {settings.env_path}")
    print("Run with: uvicorn motoengine.__main__:create_app --factory")


if __name__ == "__main__":
    main()
