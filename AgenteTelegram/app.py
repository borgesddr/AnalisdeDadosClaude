"""Bot Telegram com Groq (tool use) para consultas ao e-commerce e relatório executivo.

Lê Supabase/Groq/Telegram credentials de .env na mesma pasta. Chat livre roda um loop
agêntico manual (API da Groq é compatível com o formato OpenAI de tool calling) com uma
tool de SQL somente-leitura contra o Postgres (DATABASE_URL); /relatorio roda queries
fixas e pede só a narrativa ao modelo.
"""

import asyncio
import json
import logging
import os
import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from groq import Groq
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
DATABASE_URL = os.environ["DATABASE_URL"]

MODEL = "openai/gpt-oss-120b"
MAX_HISTORY_MESSAGES = 20
MAX_TOOL_ITERATIONS = 5
TELEGRAM_MAX_LEN = 4096

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("agente_telegram")

groq_client = Groq(api_key=GROQ_API_KEY)

SCHEMA_REFERENCE_TEXT = """Schema (Postgres, schema public, acesso somente leitura):

- clientes (50 linhas): id_cliente (PK, text), nome_cliente, estado (UF), pais, data_cadastro.
- produtos (215 linhas): id_produto (PK, text), nome_produto, categoria (11 valores: Casa, \
Acessórios, Moda, Informática, Cozinha, Esporte, Games, Áudio, Tênis, Eletrônicos, Beleza), \
marca, preco_atual (numeric, preço de catálogo atual), data_criacao.
- preco_competidores (728 linhas): id (PK), id_produto (FK -> produtos), nome_concorrente \
(Shopee, Amazon, Magalu ou Mercado Livre), preco_concorrente (numeric), data_coleta (snapshot \
único, sem série temporal de preço de concorrente).
- vendas (3000 linhas, tabela fato): id_venda (PK), data_venda (13/dez/2025 a 11/jan/2026), \
id_cliente (FK -> clientes), id_produto (FK -> produtos), canal_venda ('ecommerce' ou \
'loja_fisica'), quantidade (integer), preco_unitario (numeric, preço praticado na venda).

Relacionamentos: vendas.id_cliente -> clientes.id_cliente; vendas.id_produto -> \
produtos.id_produto; preco_competidores.id_produto -> produtos.id_produto.
"""

BUSINESS_RULES_TEXT = f"""Você é o assistente de dados do e-commerce da Keyrus.

Regras de negócio:
- Responda sempre em português do Brasil, de forma direta e objetiva.
- Receita de uma venda = quantidade * preco_unitario. Nunca use produtos.preco_atual para \
receita histórica, pois esse é o preço de catálogo atual, não o praticado na venda.
- gap_frac de um produto = (preco_atual - avg_comp) / avg_comp, onde avg_comp é a média de \
preco_concorrente daquele produto. Um gap positivo significa que NOSSO PREÇO É MAIOR que o \
concorrente (ex.: gap de 1,0 = nosso preço é o dobro do concorrente); gap negativo significa \
que nosso preço é MENOR. No pricing, preço menor que o concorrente é positivo para o negócio \
— é o oposto da lógica normal de "receita maior é melhor".
- Não use Markdown pesado (sem tabelas, sem cabeçalhos ###) — a resposta vai para o Telegram \
em texto simples.

{SCHEMA_REFERENCE_TEXT}
"""

SYSTEM_PROMPT = f"""{BUSINESS_RULES_TEXT}
Além das regras acima, você tem acesso à tool `query_database`, que executa uma instrução SELECT \
no banco Postgres e aceita apenas instruções somente-leitura. Use apenas as tabelas/colunas \
descritas na referência acima. Prefira incluir LIMIT nas consultas quando não tiver certeza do \
tamanho do resultado. Se a tool retornar um erro de validação (query rejeitada), ajuste para um \
SELECT equivalente e tente de novo.
"""

REPORT_PROMPT_TEMPLATE = """Gere um relatório executivo em português do Brasil para 3 diretores \
(Comercial, CS e Pricing), a partir destes KPIs já calculados no banco:

{kpis_json}

Regras para os números:
- Cada valor do relatório precisa vir de um campo do JSON acima — não invente nem combine campos \
(ex.: não some a receita de vários produtos/categorias, não crie uma razão que não esteja pronta \
no JSON).
- Você PODE e DEVE formatar os números para leitura humana: frações como 0.735 viram "73,5%" \
(multiplique por 100 e use vírgula decimal), valores monetários como 969837.27 viram \
"R$ 969.837,27", e arredonde para 1-2 casas decimais quando fizer sentido. Formatar não é \
"recalcular" — o valor numérico continua o mesmo, só a representação muda.

Estruture a resposta em exatamente 3 seções, uma por diretor (Comercial, CS, Pricing). Cada \
seção deve ter só 2 a 4 frases de insight acionável (não liste os KPIs brutos separadamente — \
incorpore os números diretamente dentro de cada insight). Não gere uma seção extra de "insights" \
no final; os insights já são o corpo de cada seção.

Formato de texto simples para Telegram: sem tabelas, sem cabeçalhos Markdown, sem negrito/itálico \
(nada de **, *, _ ou `), bullets com "-"."""


# --- Acesso ao banco (somente leitura) ---------------------------------------------------

class QueryValidationError(Exception):
    pass


_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|grant|revoke|create|copy|call|do|vacuum|reindex|refresh|merge)\b",
    re.IGNORECASE,
)


def _validate_select_only(sql: str) -> str:
    cleaned = sql.strip().rstrip(";").strip()
    if not cleaned:
        raise QueryValidationError("Query vazia.")
    if ";" in cleaned:
        raise QueryValidationError("Apenas uma única instrução é permitida (sem ';' no meio da query).")
    first_word_match = re.match(r"\s*(\w+)", cleaned)
    first_keyword = first_word_match.group(1).lower() if first_word_match else ""
    if first_keyword not in ("select", "with"):
        raise QueryValidationError("Apenas instruções SELECT são permitidas.")
    if _FORBIDDEN_KEYWORDS.search(cleaned):
        raise QueryValidationError("A query contém uma palavra-chave não permitida (acesso é somente leitura).")
    return cleaned


def _json_default(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Tipo não serializável: {type(obj)}")


def run_select_query(sql: str, row_limit: int = 200) -> list[dict]:
    cleaned = _validate_select_only(sql)
    if not re.search(r"\blimit\b", cleaned, re.IGNORECASE):
        cleaned = f"{cleaned} LIMIT {row_limit}"
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SET statement_timeout = 5000")
                cur.execute(cleaned)
                return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


QUERY_DATABASE_TOOL = {
    "type": "function",
    "function": {
        "name": "query_database",
        "description": (
            "Executa uma única instrução SELECT no banco Postgres do e-commerce e retorna "
            "as linhas encontradas."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": (
                        "Uma instrução SQL SELECT (PostgreSQL). Não é permitido INSERT, UPDATE, "
                        "DELETE, DROP, ALTER, CREATE ou múltiplas instruções separadas por ';'."
                    ),
                }
            },
            "required": ["sql"],
        },
    },
}


def execute_tool_call(name: str, arguments: dict) -> str:
    if name != "query_database":
        return json.dumps({"error": f"Tool desconhecida: {name}"}, ensure_ascii=False)
    try:
        rows = run_select_query(arguments.get("sql", ""))
    except QueryValidationError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)
    except Exception as exc:  # erro de execução no Postgres (coluna/tabela inexistente etc.)
        return json.dumps({"error": f"Erro ao executar a query: {exc}"}, ensure_ascii=False)
    return json.dumps(rows, default=_json_default, ensure_ascii=False)


# --- KPIs fixos para o /relatorio ---------------------------------------------------------

SQL_COMERCIAL_TOTAIS = """
    SELECT COUNT(*) AS total_vendas, SUM(quantidade*preco_unitario) AS receita_total,
           SUM(quantidade*preco_unitario)/COUNT(*) AS ticket_medio,
           SUM(quantidade) AS itens_vendidos, COUNT(DISTINCT id_cliente) AS clientes_ativos
    FROM vendas
"""

SQL_COMERCIAL_CANAL = """
    SELECT canal_venda, COUNT(*) AS total_vendas, SUM(quantidade*preco_unitario) AS receita,
           SUM(quantidade*preco_unitario)/COUNT(*) AS ticket_medio,
           SUM(quantidade*preco_unitario) / SUM(SUM(quantidade*preco_unitario)) OVER () AS pct_receita
    FROM vendas GROUP BY canal_venda
"""

SQL_COMERCIAL_CATEGORIA = """
    SELECT p.categoria, SUM(v.quantidade*v.preco_unitario) AS receita
    FROM vendas v JOIN produtos p ON p.id_produto = v.id_produto
    GROUP BY p.categoria ORDER BY receita DESC
"""

SQL_COMERCIAL_TOP_PRODUTOS = """
    SELECT p.nome_produto, SUM(v.quantidade*v.preco_unitario) AS receita
    FROM vendas v JOIN produtos p ON p.id_produto = v.id_produto
    GROUP BY p.nome_produto ORDER BY receita DESC LIMIT 5
"""

SQL_CS_COBERTURA = """
    SELECT (SELECT count(*) FROM clientes) AS total_clientes,
           (SELECT count(DISTINCT id_cliente) FROM vendas) AS clientes_ativos,
           (SELECT sum(quantidade*preco_unitario) FROM vendas) AS receita_total,
           (SELECT count(DISTINCT estado) FROM clientes) AS estados
"""

SQL_CS_TICKET_FREQ = """
    WITH c AS (
        SELECT id_cliente, sum(quantidade*preco_unitario) AS rec, count(*) AS n
        FROM vendas GROUP BY id_cliente
    )
    SELECT avg(rec) AS receita_media_por_cliente, avg(rec/n) AS ticket_medio_cliente,
           avg(n) AS frequencia_media
    FROM c
"""

SQL_CS_TOP10 = """
    WITH c AS (SELECT id_cliente, sum(quantidade*preco_unitario) AS rec FROM vendas GROUP BY id_cliente),
         r AS (SELECT rec, row_number() OVER (ORDER BY rec DESC) AS rn FROM c)
    SELECT sum(rec) FILTER (WHERE rn<=10) / sum(rec) AS share_top10 FROM r
"""

SQL_CS_CANAL_PREFERIDO = """
    WITH por_cliente_canal AS (
        SELECT id_cliente, canal_venda, sum(quantidade*preco_unitario) AS receita
        FROM vendas GROUP BY id_cliente, canal_venda
    ),
    ranked AS (
        SELECT id_cliente, canal_venda,
               row_number() OVER (PARTITION BY id_cliente ORDER BY receita DESC) AS rn
        FROM por_cliente_canal
    )
    SELECT canal_venda AS canal_preferido, count(*) AS num_clientes
    FROM ranked WHERE rn = 1 GROUP BY canal_venda
"""

SQL_PRICING_GERAL = """
    WITH comp AS (
        SELECT id_produto, avg(preco_concorrente) AS avg_comp, min(preco_concorrente) AS min_comp
        FROM preco_competidores GROUP BY id_produto
    ),
    gap AS (
        SELECT p.id_produto, p.preco_atual, c.avg_comp, c.min_comp
        FROM produtos p JOIN comp c ON c.id_produto = p.id_produto
    )
    SELECT avg((preco_atual - avg_comp) / avg_comp) AS gap_medio,
           count(*) FILTER (WHERE preco_atual > avg_comp)::float / count(*) AS pct_acima_mercado,
           count(*) FILTER (WHERE preco_atual <= min_comp) AS lideres_preco,
           count(*) AS total_produtos
    FROM gap
"""

SQL_PRICING_CATEGORIA = """
    WITH comp AS (
        SELECT id_produto, avg(preco_concorrente) AS avg_comp
        FROM preco_competidores GROUP BY id_produto
    ),
    gap AS (
        SELECT p.categoria, (p.preco_atual - c.avg_comp) / c.avg_comp AS gap_frac
        FROM produtos p JOIN comp c ON c.id_produto = p.id_produto
    )
    SELECT categoria, avg(gap_frac) AS gap_medio_categoria
    FROM gap GROUP BY categoria ORDER BY gap_medio_categoria DESC
"""


def build_report_kpis() -> dict:
    return {
        "comercial": {
            "totais": run_select_query(SQL_COMERCIAL_TOTAIS)[0],
            "por_canal": run_select_query(SQL_COMERCIAL_CANAL),
            "por_categoria": run_select_query(SQL_COMERCIAL_CATEGORIA),
            "top_produtos": run_select_query(SQL_COMERCIAL_TOP_PRODUTOS),
        },
        "cs": {
            "cobertura": run_select_query(SQL_CS_COBERTURA)[0],
            "ticket_e_frequencia": run_select_query(SQL_CS_TICKET_FREQ)[0],
            "concentracao_top10": run_select_query(SQL_CS_TOP10)[0],
            "canal_preferido": run_select_query(SQL_CS_CANAL_PREFERIDO),
        },
        "pricing": {
            "geral": run_select_query(SQL_PRICING_GERAL)[0],
            "por_categoria": run_select_query(SQL_PRICING_CATEGORIA),
        },
    }


# --- Chamadas ao modelo (Groq) --------------------------------------------------------------

def run_tool_loop(messages: list) -> str:
    """Loop agêntico manual: chama o modelo, executa tool_calls e repete até a resposta final.

    `messages` é mutado in-place (mensagens de assistant/tool são anexadas), então o histórico
    de conversa do chamador já fica pronto para o próximo turno.
    """
    for _ in range(MAX_TOOL_ITERATIONS):
        try:
            completion = groq_client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=[QUERY_DATABASE_TOOL],
                tool_choice="auto",
            )
        except Exception as exc:
            logger.exception("Erro na API da Groq durante o chat")
            return f"Erro ao consultar o modelo: {exc}"

        message = completion.choices[0].message
        tool_calls = message.tool_calls or []

        if not tool_calls:
            final_text = message.content or "Não consegui gerar uma resposta agora. Tente novamente."
            messages.append({"role": "assistant", "content": final_text})
            return final_text

        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in tool_calls
                ],
            }
        )
        for tc in tool_calls:
            try:
                arguments = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                arguments = {}
            result = execute_tool_call(tc.function.name, arguments)
            messages.append(
                {"role": "tool", "tool_call_id": tc.id, "name": tc.function.name, "content": result}
            )

    error_text = (
        "Não consegui concluir a consulta em tempo hábil (muitas chamadas à ferramenta). "
        "Tente reformular a pergunta."
    )
    messages.append({"role": "assistant", "content": error_text})
    return error_text


def _generate_report_text() -> str:
    try:
        kpis = build_report_kpis()
    except Exception as exc:
        logger.exception("Erro ao calcular os KPIs do relatório")
        return f"Erro ao consultar o banco para montar o relatório: {exc}"

    prompt = REPORT_PROMPT_TEMPLATE.format(
        kpis_json=json.dumps(kpis, ensure_ascii=False, indent=2, default=_json_default)
    )
    try:
        completion = groq_client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": BUSINESS_RULES_TEXT},
                {"role": "user", "content": prompt},
            ],
        )
    except Exception as exc:
        logger.exception("Erro na API da Groq durante o /relatorio")
        return f"Erro ao gerar o relatório: {exc}"
    return completion.choices[0].message.content or ""


# --- Telegram -------------------------------------------------------------------------------

chat_histories: dict[int, list] = {}


def _chunk_text(text: str, limit: int = TELEGRAM_MAX_LEN) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks = []
    current = ""
    for line in text.split("\n"):
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) > limit:
            if current:
                chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


async def send_long_message(update: Update, text: str) -> None:
    for chunk in _chunk_text(text):
        await update.message.reply_text(chunk)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Olá! Sou o assistente de dados do e-commerce. Pergunte livremente sobre vendas, "
        "clientes ou pricing, ou use /relatorio para o relatório executivo."
    )


async def cmd_relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Gerando relatório executivo, aguarde...")
    report_text = await asyncio.to_thread(_generate_report_text)
    await send_long_message(update, report_text or "Não foi possível gerar o relatório agora.")


async def handle_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    history = chat_histories.setdefault(chat_id, [{"role": "system", "content": SYSTEM_PROMPT}])
    history.append({"role": "user", "content": update.message.text})

    final_text = await asyncio.to_thread(run_tool_loop, history)

    if len(history) > MAX_HISTORY_MESSAGES + 1:
        history[:] = [history[0]] + history[-MAX_HISTORY_MESSAGES:]

    await send_long_message(update, final_text)


def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("relatorio", cmd_relatorio))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat))
    logger.info("Bot iniciado, aguardando mensagens...")
    application.run_polling()


if __name__ == "__main__":
    main()
