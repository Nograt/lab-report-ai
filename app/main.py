from fastapi import FastAPI


app = FastAPI(
    title="Lab Report AI"
)


@app.get("/health")
def health():
    return {"status": "ok"}