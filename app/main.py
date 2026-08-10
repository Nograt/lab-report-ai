from fastapi import FastAPI
from api.routes.reports import router as reports_router

app = FastAPI(
    title="Lab Report AI"
)
app.include_router(reports_router)

@app.get("/health")
def health():
    return {"status": "ok"}