from fastapi import FastAPI

from api.routes.profile import router as profile_router
from api.routes.reports import router as reports_router
from api.routes.subjects import router as subject_router


app = FastAPI(
    title="Lab Report AI",
)


app.include_router(reports_router)
app.include_router(subject_router)
app.include_router(profile_router)


@app.get("/health")
def health():
    return {"status": "ok"}