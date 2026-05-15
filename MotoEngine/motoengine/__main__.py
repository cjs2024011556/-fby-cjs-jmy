"""FastAPI 主应用"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from motoengine.route import api_router

app = FastAPI(
    title="摩托车发动机维修智能体 API",
    description="基于 LangChain 和 ChromaDB 的摩托车发动机维修智能助手 API",
    version="0.2.0",
    docs_url="/api-docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

base_path = Path(__file__).parent

manual_path = base_path / "templates" / "manual"
if manual_path.exists():
    app.mount("/manual", StaticFiles(directory=str(manual_path), html=True), name="manual")

agent_path = base_path / "templates" / "agent"
if agent_path.exists():
    app.mount("/agent", StaticFiles(directory=str(agent_path), html=True), name="agent")

admin_path = base_path / "templates" / "admin"
if admin_path.exists():
    app.mount("/admin", StaticFiles(directory=str(admin_path), html=True), name="admin")

docs_path = base_path.parent / "docs"
if docs_path.exists():
    app.mount("/docs", StaticFiles(directory=str(docs_path)), name="docs")


@app.get("/")
async def root():
    """根路径"""
    home_path = base_path / "templates" / "index.html"
    if home_path.exists():
        return FileResponse(str(home_path))
    return {
        "message": "摩托车发动机维修智能体 API",
        "version": "0.2.0",
        "docs": "/api-docs",
        "agent": "/agent/",
        "admin": "/admin/",
        "manual": "/manual/",
        "api_base": "/api/v2/chat",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
