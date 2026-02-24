from fastapi import FastAPI

from app.api.routes.planner import router as planner_router

app = FastAPI(title="PVTV Social Ops API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(planner_router)
