from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db
from routes.transactions import router as tx_router
from routes.summary import router as summary_router
from routes.ranking import router as ranking_router
from middleware.rate_limiter import RateLimiterMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Transaction Ranking API",
    description="Idempotent transaction processing with multi-factor fair ranking.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — tighten origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimiterMiddleware)

app.include_router(tx_router)
app.include_router(summary_router)
app.include_router(ranking_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
