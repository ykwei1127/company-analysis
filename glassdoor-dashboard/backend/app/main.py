from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import overview, ratings, scraper, settings

app = FastAPI(title="Glassdoor Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(overview.router, prefix="/api")
app.include_router(ratings.router, prefix="/api")
app.include_router(scraper.router, prefix="/api")
app.include_router(settings.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
