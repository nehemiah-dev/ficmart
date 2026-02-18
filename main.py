from contextlib import asynccontextmanager

import auth
import catalog
import cart
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


app = FastAPI(lifespan=lifespan)


app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(catalog.router, prefix="/api/products", tags=["catalog"])
app.include_router(cart.router, prefix="/api/cart", tags=["Cart"])
