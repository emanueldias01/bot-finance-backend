import asyncio
import os
import aiosmtplib
from contextlib import asynccontextmanager
from email.message import EmailMessage
from dotenv import load_dotenv
from sqlmodel import select
from api.database.config import get_session
from api.models.user import User
from api.models.transaction import Transaction

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
EMAIL = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


async def send_emails_description_pendings():
    async with asynccontextmanager(get_session)() as session:
        statement = (
            select(User)
            .join(Transaction)
            .where(Transaction.description == "")
            .distinct()
        )
        users = (await session.execute(statement)).scalars().all()

    tasks = []
    for user in users:
        msg = EmailMessage()
        msg["Subject"] = "Atenção: Transações pendentes no BotFinance"
        msg["From"] = "noreply@botfinance.com"
        msg["To"] = user.email
        msg.set_content(
            f"""
        <html>
            <body>
                <h1>BotFinance</h1>
                <p>Olá, <strong>{user.username}</strong>.</p>
                <p>Notamos que você possui transações recentes sem descrição.</p>
                <p>É muito importante que você descreva essas transações para mantermos suas finanças organizadas.</p>
                <p>Por favor, acesse a plataforma para atualizar as pendências.</p>
            </body>
        </html>
        """,
            subtype="html",
        )

        tasks.append(
            aiosmtplib.send(
                msg,
                hostname=SMTP_SERVER,
                port=SMTP_PORT,
                username=EMAIL,
                password=EMAIL_PASSWORD,
                use_tls=True,
            )
        )

    if tasks:
        await asyncio.gather(*tasks)


def triggers_async_job(loop):
    asyncio.run_coroutine_threadsafe(send_emails_description_pendings(), loop)
