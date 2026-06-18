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
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
EMAIL = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


async def _send_batch_emails(tasks):
    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, Exception):
                print(f"Erro ao enviar e-mail: {res}")


# --- JOB 1: Transações Pendentes ---
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
        msg["From"] = f"BotFinance <{EMAIL}>"  # Melhor prática para o From
        msg["To"] = user.email
        msg.set_content(
            f"""
        <html>
            <body>
                <h1>BotFinance</h1>
                <p>Olá, <strong>{user.username}</strong>.</p>
                <p>Notamos que você possui transações recentes sem descrição.</p>
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

    await _send_batch_emails(tasks)


# --- JOB 2: Relatório Semanal ---
async def get_weekly_transactions(session: AsyncSession, user_id):
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)

    statement = (
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .where(Transaction.date >= start_date)
        .where(Transaction.date <= end_date)
        .order_by(Transaction.date.desc())
    )

    result = await session.execute(statement)
    return result.scalars().all()


async def send_weekly_reports():
    async with asynccontextmanager(get_session)() as session:
        users_stmt = select(User)
        users = (await session.execute(users_stmt)).scalars().all()

        tasks = []
        for user in users:
            report = await get_weekly_transactions(session, user.id)
            if not report:
                continue

            report_html = "<ul>"
            for t in report:
                desc = t.description if t.description else "Sem descrição"
                report_html += (
                    f"<li>{t.date.strftime('%d/%m')} - {desc}: R$ {t.value:.2f}</li>"
                )
            report_html += "</ul>"

            msg = EmailMessage()
            msg["Subject"] = "📊 Seu resumo financeiro da semana"
            msg["From"] = f"BotFinance <{EMAIL}>"
            msg["To"] = user.email
            msg.set_content(
                f"""
                <html>
                    <body>
                        <h1>Resumo Financeiro da Semana</h1>
                        <p>Olá, <strong>{user.username}</strong>!</p>
                        <p>Aqui está o resumo dos seus últimos 7 dias:</p>
                        {report_html}
                        <hr>
                        <p>Continue acompanhando suas finanças 🚀</p>
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

        await _send_batch_emails(tasks)


# --- CORREÇÃO DOS GATILHOS (TRIGGERS) ---
def trigger_pendings_job(loop):
    asyncio.run_coroutine_threadsafe(send_emails_description_pendings(), loop)


def trigger_weekly_report_job(loop):
    asyncio.run_coroutine_threadsafe(send_weekly_reports(), loop)
