from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.auth import router as auth_router
from api.routes.open_finance_item import router as item_router
from api.routes.open_finance_account import router as account_router
from api.routes.open_finance_transactions import router as transactions_router
from api.routes.llm_chat import router as llm_chat_router
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from api.functions.email import triggers_async_job


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio

    current_loop = asyncio.get_running_loop()

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        triggers_async_job, "cron", hour=0, minute=0, args=[current_loop]
    )
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan, version="0.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(item_router)
app.include_router(account_router)
app.include_router(transactions_router)
app.include_router(llm_chat_router)
