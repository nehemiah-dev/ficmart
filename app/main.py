from contextlib import asynccontextmanager

from routes import health
from routes import auth
from routes import catalog
from routes import cart
from routes import checkout
import webhook as webhook
from fastapi import FastAPI
from database import engine, Base


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # startup
    async with engine.begin() as conn:
        print("Starting database engine...")
        await conn.run_sync(Base.metadata.create_all)
    yield
    # shutdown
    print("Shutting down database engine")
    await engine.dispose()


version = "v1"
app = FastAPI(
    version=version,
    title="Ficmart",
    description="An E-commerce webAPI",
    lifespan=lifespan,
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(webhook.router, prefix="/api/webhook", tags=["webhook"])
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(catalog.router, prefix="/api/products", tags=["catalog"])
app.include_router(cart.router, prefix="/api/cart", tags=["Cart"])
app.include_router(checkout.router, prefix="/api/checkout", tags=["Checkout"])
