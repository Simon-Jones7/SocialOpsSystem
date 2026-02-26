from fastapi import FastAPI

from app.api.routes.planner import router as planner_router

from app.api.routes.approvals import router as approvals_router
from app.core.db import ensure_tables

app = FastAPI(title="PVTV Social Ops API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(planner_router)
app.include_router(approvals_router)

@app.on_event("startup")
def startup():
    ensure_tables()
