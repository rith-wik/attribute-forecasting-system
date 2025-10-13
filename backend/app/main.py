from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import forecasts, training, trends, uploads

app = FastAPI(title="AFS API", version="0.1.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(forecasts.router, prefix="/api/v1")
app.include_router(training.router, prefix="/api/v1")
app.include_router(trends.router, prefix="/api/v1")
app.include_router(uploads.router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "ok"}
