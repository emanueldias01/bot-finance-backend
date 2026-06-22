import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.auth import router as auth_router
from api.routes.open_finance_item import router as item_router
from api.routes.open_finance_account import router as account_router
from api.routes.open_finance_transactions import router as transactions_router
from api.routes.llm_chat import router as llm_chat_router
from api.routes.financial import router as financial_router
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from api.functions.email import trigger_pendings_job, trigger_weekly_report_job


@asynccontextmanager
async def lifespan(app: FastAPI):
    current_loop = asyncio.get_running_loop()
    scheduler = BackgroundScheduler()

    # JOB 1: Transações pendentes sem descrição
    scheduler.add_job(
        trigger_pendings_job, "cron", hour=9, minute=0, args=[current_loop]
    )

    # JOB 2: Relatório semanal financeiro
    scheduler.add_job(
        trigger_weekly_report_job,
        "cron",
        day_of_week="sun",
        hour=18,
        minute=0,
        args=[current_loop],
    )

    scheduler.start()

    yield

    scheduler.shutdown()


app = FastAPI(lifespan=lifespan, version="0.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["https://frontend-botfinance.onrender.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(item_router)
app.include_router(account_router)
app.include_router(transactions_router)
app.include_router(llm_chat_router)
app.include_router(financial_router)
