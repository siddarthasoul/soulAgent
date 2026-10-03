from fastapi import FastAPI
from app.router.agent import router
from app.router.visualization import router as visualization_router


app = FastAPI();

app.include_router(
    router,
    prefix="/api/v1/agent",
    tags=["Agent"],
)

app.include_router(
    visualization_router,
    prefix="/api/v1/visualizations",
    tags=["Visualizations"],
)

app.get("/health", tags=["Health"])(lambda: {"status": "ok"})