from sqlalchemy.ext.asyncio import AsyncSession
from api.functions.open_finance_transactions import get_transactions_data
from api.schemas.chat import ChatRequestTransactions, ChatResponse, InsightsResponse, Insight, InsightType
from api.models.user import User
from api.models.account import Account
from sqlalchemy import select
from fastapi import HTTPException
from google import genai
import os
from api.models.transaction import Transaction
from dotenv import load_dotenv
import json

load_dotenv()

AI_API_KEY = os.getenv("AI_API_KEY")


async def request_chat_about_account(
    request: ChatRequestTransactions, db: AsyncSession, user: User
) -> ChatResponse:
    verify_accout = await db.execute(
        select(User)
        .where(User.id == user.id)
        .join(User.accounts)
        .where(Account.id == request.account_id)
    )
    if not verify_accout.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Account not found")

    result = await get_transactions_data(db=db, user=user, has_description=True)
    client = genai.Client(api_key=AI_API_KEY)

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=f"""
        Você é um assistente financeiro inteligente.

        Sua função é responder às perguntas do usuário utilizando EXCLUSIVAMENTE as transações fornecidas.

        Objetivos:
        - Responder de forma clara e objetiva.
        - Ajudar o usuário a entender seus gastos, receitas e hábitos financeiros.
        - Encontrar padrões, tendências e responder perguntas sobre movimentações.
        - Quando apropriado, fornecer insights e sugestões práticas para melhorar a organização financeira.

        Regras importantes:
        - Nunca invente informações.
        - Nunca assuma valores ou transações que não estejam presentes.
        - Caso a pergunta não possa ser respondida com as transações fornecidas, explique isso educadamente.
        - Se houver cálculos, faça-os corretamente antes de responder.
        - Se houver várias transações relacionadas ao assunto da pergunta, considere todas elas.
        - Seja breve em perguntas simples e mais detalhado quando o usuário pedir uma análise.
        - Utilize Markdown para organizar respostas longas.
        - Utilize emojis apenas quando fizer sentido.

        Exemplos de perguntas:
        - Quanto gastei com alimentação?
        - Qual foi minha maior compra?
        - Recebi salário este mês?
        - Quanto sobrou depois das despesas?
        - Em que estou gastando mais dinheiro?
        - Quais pagamentos são recorrentes?
        - Quanto gastei no supermercado?

        Transações:
        {result}

        Pergunta do usuário:
        {request.message}

        Resposta:
        """,
    )

    return ChatResponse(response=response.text)


async def resume_transactions(transactions: list[Transaction]) -> str:
    client = genai.Client(api_key=AI_API_KEY)

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=f"""
            Você é um assistente financeiro especializado em analisar movimentações bancárias.

            Sua tarefa é analisar as transações da última semana e produzir um resumo útil para o usuário.

            Considere os seguintes pontos:

            1. Faça um resumo geral da semana em 2 ou 3 frases.
            2. Informe:
            - Total de entradas (receitas)
            - Total de saídas (despesas)
            - Saldo líquido da semana
            3. Identifique as categorias ou tipos de gastos mais relevantes.
            4. Destaque gastos incomuns ou muito acima do padrão observado nas transações da semana.
            5. Identifique assinaturas, pagamentos recorrentes ou despesas frequentes, caso existam.
            6. Aponte possíveis oportunidades de economia, mas apenas quando houver evidências nas transações.
            7. Caso existam gastos muito concentrados em uma categoria (ex.: alimentação, transporte, lazer), mencione isso.
            8. Termine com uma breve conclusão contendo até 3 recomendações práticas para a próxima semana.

            Regras:
            - Não invente informações.
            - Não faça julgamentos sobre o usuário.
            - Caso algum dado não possa ser inferido das transações, simplesmente não mencione.
            - Utilize linguagem simples, amigável e objetiva.
            - Use Markdown para organizar a resposta.
            - Utilize emojis moderadamente para facilitar a leitura.

            Transações:
            {transactions}
            """,
    )

    return response.text


async def analyze_transactions_insights(db: AsyncSession, user: User) -> InsightsResponse:
    result = await get_transactions_data(db=db, user=user, has_description=True)
    if result.total == 0:
        return InsightsResponse(insights=[], summary="Nenhuma transação encontrada.", has_transactions=False)
    
    client = genai.Client(api_key=AI_API_KEY)

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=f"""
        Você é o BotFinance, um assistente financeiro inteligente especializado em analisar transações bancárias.

        Sua função é analisar as transações fornecidas e gerar insights objetivos e úteis sobre a situação financeira do usuário.

        Objetivos:
        - Identificar padrões de gastos e receitas
        - Detectar oportunidades de economia
        - Alertar sobre riscos financeiros
        - Fornecer sugestões práticas de melhoria
        - Identificar despesas recorrentes ou incomuns

        Tipos de insights que você deve gerar:
        1. ECONOMY_OPPORTUNITY: Oportunidades de economia (assinaturas duplicadas, gastos excessivos em categorias específicas, etc.)
        2. CASH_FLOW_RISK: Riscos de fluxo de caixa (saldo negativo previsto, gastos concentrados em curto período, etc.)
        3. SPENDING_PATTERN: Padrões de gastos (aumento progressivo de gastos, sazonalidade, etc.)
        4. RECURRING_EXPENSE: Despesas recorrentes (assinaturas, pagamentos fixos, etc.)
        5. ALERT: Alertas sobre situações perigosas (gastos acima da média, falta de controle, etc.)
        6. SUGGESTION: Sugestões de melhoria (otimizações, mudanças de hábito, etc.)

        Regras importantes:
        - NUNCA invente informações que não estejam nas transações
        - Seja objetivo e baseado apenas nos dados fornecidos
        - Não faça julgamentos morais sobre o usuário
        - Cada insight deve ter evidência clara nas transações
        - Classifique a severidade como LOW, MEDIUM ou HIGH quando apropriado
        - Indique se o insight é acionável (actionable: true/false)
        - Seja conciso e direto nas descrições
        - Máximo de 8 insights por análise
        - Priorize insights mais relevantes e impactantes
        - Dirija-se sempre ao usuário como "você"
        - "type" deve ser "OPORTUNIDADE_DE_ECONOMIA", "RISCO_DE_FLUXO_DE_CAIXA", "PADRAO_DE_GASTOS", "DESPESA_RECORRENTE", "ALERTA" ou "SUGESTAO"

        Formato de resposta JSON:
        {{
            "insights": [
                {{
                    "type": "OPORTUNIDADE_DE_ECONOMIA",
                    "title": "Título curto e descritivo",
                    "description": "Descrição detalhada do insight com evidências das transações",
                    "severity": "MEDIUM",
                    "actionable": true,
                    "icon": "💡"
                }}
            ],
            "summary": "Resumo geral da situação financeira em 2-3 frases"
        }}

        Transações:
        {result}

        Responda APENAS com o JSON válido, sem texto adicional.
        """,
    )

    try:
        insights_data = json.loads(response.text)
        return InsightsResponse(**insights_data)
    except json.JSONDecodeError:
        return InsightsResponse(
            insights=[],
            has_transactions=False,
            summary="Não foi possível gerar insights neste momento. Tente novamente mais tarde."
        )



