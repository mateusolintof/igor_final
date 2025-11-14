#!/usr/bin/env python3
"""
Simulador de 10 conversas end-to-end usando uma LLM como "usuário" para
gerar mensagens adaptativas, integrando com:

- Kommo (criação de contato e lead)
- Webhook do n8n (orquestrador)
- Postgres (memória de chat do n8n) para coletar respostas do agente

Pré-requisitos:
- Python 3.9+
- pip install openai psycopg2-binary requests tenacity

Variáveis (podem ser sobrescritas via env):
- OPENAI_API_KEY
- KOMMO_API_BASE (default: https://api-c.kommo.com/api/v4)
- KOMMO_SUBDOMAIN (default: institutodrigor)
- KOMMO_API_KEY (default: valor fornecido no brief) — incluir o prefixo "Bearer "
- N8N_WEBHOOK_URL (default: https://flowhook.convert-saude.space/webhook/wa/orchestrator)
- POSTGRES_* (host, port, database, user, password)

Observações importantes:
- O formato do Webhook do n8n segue o "Normalize Input" do fluxo: chaves estilo
  message[add][0][text], element_id (lead_id), element_type ("leads"), contact_id, etc.
- O script tenta automaticamente localizar a tabela de memória do chat no Postgres
  (heurísticas para tabelas/colunas comuns) e extrair a última mensagem do agente
  para uma dada sessão. Como sessão, tentamos: lead_id, contact_id e phone.
"""

from __future__ import annotations

import json
import os
import random
import string
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from tenacity import retry, stop_after_attempt, wait_exponential


# -----------------------------
# Configurações com defaults
# -----------------------------

KOMMO_API_BASE = os.getenv("KOMMO_API_BASE", "https://api-c.kommo.com/api/v4")
KOMMO_SUBDOMAIN = os.getenv("KOMMO_SUBDOMAIN", "institutodrigor")
KOMMO_API_KEY = os.getenv(
    "KOMMO_API_KEY",
    os.getenv(
        "OMMO_API_KEY",
        "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImJiMTVkOTFlZWI3ODc3NWEwNDRmNjRjZDdiYmM2YWE2NTA0OTk3ZWU0M2ZlOTVhZGU3OTc5ZGQ0YzU4ZDUxNjY1MjM0OWY1ZTg5MjM1NmQzIn0.eyJhdWQiOiI5MDIyMGQ3NS01YTBiLTRiYjAtOGIxOS0xNmU3MDM2MjE4YzgiLCJqdGkiOiJiYjE1ZDkxZWViNzg3NzVhMDQ0ZjY0Y2Q3YmJjNmFhNjUwNDk5N2VlNDNmZTk1YWRlNzk3OWRkNGM1OGQ1MTY2NTIzNDlmNWU4OTIzNTZkMyIsImlhdCI6MTc1NzI3NzA2MywibmJmIjoxNzU3Mjc3MDYzLCJleHAiOjE4MzAyMTEyMDAsInN1YiI6IjEyNjk0NTExIiwiZ3JhbnRfdHlwZSI6IiIsImFjY291bnRfaWQiOjM0MTUzMTIzLCJiYXNlX2RvbWFpbiI6ImtvbW1vLmNvbSIsInZlcnNpb24iOjIsInNjb3BlcyI6WyJjcm0iLCJmaWxlcyIsImZpbGVzX2RlbGV0ZSIsIm5vdGlmaWNhdGlvbnMiLCJwdXNoX25vdGlmaWNhdGlvbnMiXSwidXNlcl9mbGFncyI6MCwiaGFzaF91dWlkIjoiNzc3ZTRjOTktNzFhMi00MTVlLWJmY2MtNmRjZTFmZjZmZjU1IiwiYXBpX2RvbWFpbiI6ImFwaS1jLmtvbW1vLmNvbSJ9.kF7xYsg9rHwsMOSKm8cmbkUtBiwBAg2GTFJ2qtJQfW1c3edQs8TM77K-AtH8TJisAkbxeAZAvgaQY9Ula7Fj8_exCZ0GQgod6XmBP_jG-rY3q-k9vq4yAylw90a8hxCGkVBuXHQkoIeEujxN9Z9jZCDJosZkoY_YdsKrUd87UYempxZBxUz-OLmrm4jrqSD7eEBthLN8kvSB-xH2jGsMZPDjTD0DQbsGT2aD-80P2CJ3clfTgj0uVuWwc6A19cuizgT9AbPoGumidKT-VyddMXLM7tQj4J9CaKer3HMJNx1RzxaqLgdbgZnzCnQHMgr_QHNODCpDnpyPYxl9lftJow",
    ),
)

N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL",
    "https://flowhook.convert-saude.space/webhook/wa/orchestrator",
)

PG_HOST = os.getenv("POSTGRES_HOST", "easypanel.convert-saude.space")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
PG_DB = os.getenv("POSTGRES_DATABASE", "igor")
PG_USER = os.getenv("POSTGRES_USER", "postgres")
PG_PASSWORD = os.getenv(
    "POSTGRES_PASSWORD",
    "5ciMwJEPAjuniKGcSyhmdfCL867kXbIR",
)


# -----------------------------
# OpenAI client (Responses API, com fallback para Chat Completions)
# -----------------------------

def openai_generate(system_prompt: str, user_prompt: str, model: str = "gpt-4.1-mini") -> str:
    """Gera texto via OpenAI Responses API (preferencial) e faz fallback para ChatCompletions.

    Requer OPENAI_API_KEY em env. Limita a 1-2 frases curtas no "usuário simulado".
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Defina OPENAI_API_KEY no ambiente.")

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        # Responses API (novo formato)
        resp = client.responses.create(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": [
                        {"type": "text", "text": system_prompt},
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                    ],
                },
            ],
            temperature=0.7,
            top_p=0.95,
            max_output_tokens=120,
        )
        # Extrair texto
        for out in resp.output:
            if out.type == "message":
                for c in out.message.content:
                    if c.type == "text":
                        return c.text.strip()
        # Fallback de parsing
        return getattr(resp, "output_text", "").strip() or ""
    except Exception:
        # Fallback para chat.completions
        import openai as _openai

        _openai.api_key = api_key
        r = _openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            top_p=0.95,
            max_tokens=120,
        )
        return r["choices"][0]["message"]["content"].strip()


# -----------------------------
# Utilitários
# -----------------------------

def _rand_phone() -> str:
    """Gera um telefone brasileiro fictício para testes (com DDI/DDD)."""
    return "+55" + "7" + "1" + "9" + "".join(random.choice(string.digits) for _ in range(7))


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def kommo_create_contact(name: str, phone: str) -> int:
    url = f"{KOMMO_API_BASE}/contacts"
    headers = {
        "Authorization": KOMMO_API_KEY,
        "Content-Type": "application/json",
    }
    payload = [
        {
            "name": name,
            "custom_fields_values": [
                {
                    "field_code": "PHONE",
                    "values": [
                        {"value": phone, "enum_code": "WORK"},
                    ],
                }
            ],
        }
    ]
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    contact = data.get("_embedded", {}).get("contacts", [{}])[0]
    return int(contact["id"])  # type: ignore[index]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def kommo_create_lead(name: str) -> int:
    url = f"{KOMMO_API_BASE}/leads"
    headers = {
        "Authorization": KOMMO_API_KEY,
        "Content-Type": "application/json",
    }
    payload = [
        {
            "name": name,
            # Pipeline e status podem ser ajustados se necessário
        }
    ]
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    lead = data.get("_embedded", {}).get("leads", [{}])[0]
    return int(lead["id"])  # type: ignore[index]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def kommo_link_lead_contact(lead_id: int, contact_id: int) -> None:
    url = f"{KOMMO_API_BASE}/leads/{lead_id}/link"
    headers = {
        "Authorization": KOMMO_API_KEY,
        "Content-Type": "application/json",
    }
    payload = [
        {"to_entity_id": contact_id, "to_entity_type": "contacts"}
    ]
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    # Alguns ambientes podem retornar 204 ou 200; considerar 2xx como sucesso
    if not str(r.status_code).startswith("2"):
        r.raise_for_status()


def n8n_send_message(text: str, lead_id: int, contact_id: int, created_at: Optional[int] = None) -> None:
    created_at = created_at or int(time.time())
    payload = {
        "account[subdomain]": KOMMO_SUBDOMAIN,
        "account[id]": 0,
        "message[add][0][contact_id]": contact_id,
        "message[add][0][text]": text,
        "message[add][0][element_id]": lead_id,
        "message[add][0][element_type]": "leads",
        "message[add][0][created_at]": created_at,
    }
    r = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=30)
    r.raise_for_status()


# -----------------------------
# Postgres: localizar e ler memória de chat
# -----------------------------

def _pg_conn():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
        cursor_factory=RealDictCursor,
    )


def _list_candidate_tables(cur) -> List[str]:
    cur.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema='public'
          AND (
            table_name ILIKE '%chat%'
            OR table_name ILIKE '%memory%'
            OR table_name ILIKE '%message%'
            OR table_name ILIKE '%conversation%'
          )
        ORDER BY table_name
        ;
        """
    )
    return [r["table_name"] for r in cur.fetchall()]


def _table_columns(cur, table: str) -> List[str]:
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name=%s
        ORDER BY ordinal_position
        ;
        """,
        (table,),
    )
    return [r["column_name"] for r in cur.fetchall()]


def _fetch_last_ai_message(
    cur,
    session_keys: List[str],
    since_ts: float,
    timeout_sec: int = 180,
) -> Optional[str]:
    """Heurística para encontrar a última mensagem do agente na memória do n8n.

    - Procura por tabelas candidatas.
    - Suporta schema "por linhas" (role/content) ou JSONB de mensagens por sessão.
    - Varre múltiplas chaves de sessão (lead_id, contact_id, phone).
    - Faz polling até timeout_sec.
    """
    deadline = time.time() + timeout_sec
    last_seen: Optional[str] = None

    while time.time() < deadline:
        tables = _list_candidate_tables(cur)
        for t in tables:
            cols = _table_columns(cur, t)
            lc = [c.lower() for c in cols]

            # Caso 1: colunas típicas por linha
            if {"session_id", "role", "content"}.issubset(set(lc)):
                cur.execute(
                    f"""
                    SELECT session_id, role, content, COALESCE(updated_at, created_at, NOW()) AS ts
                    FROM {t}
                    WHERE COALESCE(updated_at, created_at, NOW()) >= to_timestamp(%s)
                    ORDER BY ts DESC
                    LIMIT 200
                    """,
                    (since_ts,),
                )
                rows = cur.fetchall()
                for r in rows:
                    sid = str(r.get("session_id"))
                    if sid in session_keys and str(r.get("role", "")).lower() in ("assistant", "ai", "agent"):
                        content = r.get("content")
                        if content:
                            return str(content)

            # Caso 2: colunas típicas por sessão com JSON de mensagens
            elif {"session_id", "messages"}.issubset(set(lc)):
                cur.execute(
                    f"""
                    SELECT session_id, messages, COALESCE(updated_at, created_at, NOW()) AS ts
                    FROM {t}
                    WHERE COALESCE(updated_at, created_at, NOW()) >= to_timestamp(%s)
                    ORDER BY ts DESC
                    LIMIT 100
                    """,
                    (since_ts,),
                )
                rows = cur.fetchall()
                for r in rows:
                    sid = str(r.get("session_id"))
                    if sid in session_keys:
                        msgs = r.get("messages")
                        try:
                            arr = msgs if isinstance(msgs, list) else json.loads(msgs)
                            # procurar última mensagem do "assistant"
                            for m in reversed(arr):
                                role = (m.get("role") or m.get("author") or "").lower()
                                if role in ("assistant", "ai", "agent"):
                                    content = m.get("content") or m.get("text")
                                    if isinstance(content, list):
                                        # n8n/LC pode armazenar como [{type:"text", text:"..."}]
                                        for c in content:
                                            if isinstance(c, dict) and c.get("type") == "text" and c.get("text"):
                                                return str(c["text"]).strip()
                                    elif content:
                                        return str(content).strip()
                        except Exception:
                            pass

        time.sleep(3)

    return last_seen


# -----------------------------
# Cenários de teste (10)
# -----------------------------

SCENARIOS = [
    {
        "name": "ambigua_quero_consultar",
        "profile": "inicial_ambigua",
        "hint": "Primeiro contato ambíguo, não é prontidão real.",
    },
    {
        "name": "preco_no_inicio",
        "profile": "preco_sensivel",
        "hint": "Pergunta preço logo no início; depois informa objetivo curto.",
    },
    {
        "name": "objeção_preco",
        "profile": "preco_sensivel",
        "hint": "Expressa objeção de preço de forma cordial.",
    },
    {
        "name": "objetivo_emagrecimento",
        "profile": "qualificado_rapido",
        "hint": "Quer emagrecer rápido para um evento em 3 meses.",
    },
    {
        "name": "distancia_online",
        "profile": "online",
        "hint": "Mora fora de Feira e prefere online.",
    },
    {
        "name": "nutricionista_vs_nutrologo",
        "profile": "duvida_metodo",
        "hint": "Confunde nutricionista e nutrólogo; pede esclarecimento curto.",
    },
    {
        "name": "agendar_no_inicio",
        "profile": "quer_agendar_mas_quer_entender",
        "hint": "Diz que quer agendar logo no começo, mas quer entender antes.",
    },
    {
        "name": "metodo",
        "profile": "duvida_metodo",
        "hint": "Pergunta como funciona o método e cita objetivo de definição.",
    },
    {
        "name": "convenio",
        "profile": "convenio",
        "hint": "Pergunta sobre convênio e deixa interesse em aberto.",
    },
    {
        "name": "so_pesquisando",
        "profile": "so_pesquisando",
        "hint": "Diz que está só pesquisando por enquanto.",
    },
]


# -----------------------------
# Perfis (persona) do "usuário" simulado
# -----------------------------

PROFILE_PRESETS: Dict[str, Dict[str, Any]] = {
    "inicial_ambigua": {
        "traits": ["primeiro contato", "não é prontidão", "curto e cordial"],
        "facts": {"objetivo": None, "cidade": None, "orcamento": "neutro"},
    },
    "preco_sensivel": {
        "traits": ["sensível a preço", "cordial", "quer entender antes"],
        "facts": {"objetivo": None, "cidade": None, "orcamento": "apertado"},
    },
    "qualificado_rapido": {
        "traits": ["alta intenção", "contexto rico", "objetivo claro"],
        "facts": {"objetivo": "emagrecimento", "cidade": "Feira de Santana", "orcamento": "ok"},
    },
    "online": {
        "traits": ["mora longe", "prefere online"],
        "facts": {"objetivo": None, "cidade": "Salvador", "orcamento": "neutro"},
    },
    "duvida_metodo": {
        "traits": ["quer entender método", "curto e direto"],
        "facts": {"objetivo": None, "cidade": None, "orcamento": "neutro"},
    },
    "quer_agendar_mas_quer_entender": {
        "traits": ["diz que quer agendar", "ainda quer entender", "não é prontidão automática"],
        "facts": {"objetivo": None, "cidade": None, "orcamento": "ok"},
    },
    "convenio": {
        "traits": ["pergunta sobre convênio", "interesse aberto"],
        "facts": {"objetivo": None, "cidade": None, "orcamento": "neutro"},
    },
    "so_pesquisando": {
        "traits": ["baixa intenção", "pesquisando", "cordial"],
        "facts": {"objetivo": None, "cidade": None, "orcamento": "neutro"},
    },
}


def _random_name() -> str:
    first = random.choice(["João", "Maria", "Ana", "Paulo", "Carla", "Rafa", "Bruna", "Thiago", "Luana", "Renato"])  # noqa: E501
    last = random.choice(["Silva", "Santos", "Costa", "Oliveira", "Pereira", "Almeida"])  # noqa: E501
    return f"{first} {last}"


def build_persona_system_prompt(profile: str, state: Dict[str, Any]) -> str:
    p = PROFILE_PRESETS.get(profile, PROFILE_PRESETS["inicial_ambigua"])
    traits = ", ".join(p.get("traits", []))
    facts = {**p.get("facts", {}), **state}
    base = (
        "Você simula um lead humano no WhatsApp em PT-BR. Seja natural, 1–2 frases, "
        "sem emojis, sem formalismo. Não revele que é teste. Adapte-se ao que o agente diz."
    )
    facts_txt = "\n".join(
        [
            f"- Nome: {facts.get('nome')}",
            f"- Objetivo: {facts.get('objetivo')}",
            f"- Cidade: {facts.get('cidade')}",
            f"- Orçamento: {facts.get('orcamento')} (não force objeção; só manifeste se fizer sentido)",
        ]
    )
    rules = (
        "\nRegras principais:\n"
        "- Se o agente pedir nome/objetivo e você ainda não forneceu, forneça de forma natural.\n"
        "- Se já forneceu, não repita; avance no assunto.\n"
        "- Se disser que quer agendar, mas ainda tem dúvidas, peça um resumo curto antes de fechar.\n"
        "- Evite perguntas em cascata.\n"
    )
    return f"Perfil: {traits}\n{base}\n\nSeus dados:\n{facts_txt}{rules}"


def build_user_reply(system_prompt: str, last_agent_msg: str, history: List[Dict[str, str]]) -> str:
    # Compacta o histórico recente (últimos 6 turnos) para dar contexto ao LLM
    h = history[-6:]
    hist_txt = []
    for m in h:
        role = "Agente" if m["role"] == "assistant" else "Você"
        hist_txt.append(f"{role}: {m['content']}")
    history_block = "\n".join(hist_txt)

    guidance = (
        "Responda em 1–2 frases, mantendo coerência com o histórico. "
        "Forneça dados pedidos (nome/objetivo) se faltarem; caso contrário, avance o assunto."
    )
    user_prompt = (
        f"Histórico recente:\n{history_block}\n\n"
        f"Última mensagem do agente:\n{last_agent_msg}\n\n{guidance}"
    )
    return openai_generate(system_prompt, user_prompt)


def _generate_opener(system_prompt: str, hint: str) -> str:
    prompt = (
        "Gere a primeira mensagem desse lead conforme o perfil acima. "
        "Apenas 1–2 frases. Contexto: " + hint
    )
    return openai_generate(system_prompt, prompt)


def run_conversation(test_idx: int, scenario: Dict[str, str]) -> Dict[str, Any]:
    name = f"Teste {test_idx+1} - {scenario['name']}"
    phone = _rand_phone()
    persona_state = {
        "nome": _random_name(),
        "objetivo": None,
        "cidade": random.choice([None, "Feira de Santana", "Salvador", "Vitória da Conquista"]),
        "orcamento": random.choice(["ok", "apertado", "neutro"]),
    }
    system_profile = build_persona_system_prompt(scenario.get("profile", "inicial_ambigua"), persona_state)

    # 1) Criar contato e lead
    contact_id = kommo_create_contact(name=name, phone=phone)
    lead_id = kommo_create_lead(name=f"Lead {scenario['name']}")
    try:
        kommo_link_lead_contact(lead_id, contact_id)
    except Exception:
        pass  # não é crítico

    # 2) Enviar mensagem inicial ao Webhook
    history: List[Dict[str, str]] = []
    try:
        opener = _generate_opener(system_profile, scenario.get("hint", ""))
    except Exception:
        opener = "Oi, gostaria de entender melhor."
    n8n_send_message(opener, lead_id, contact_id)
    history.append({"role": "user", "content": opener})

    # 3) Aguardar até 180s pela resposta do agente
    start_ts = time.time()
    with _pg_conn() as conn:
        with conn.cursor() as cur:
            ai_msg = _fetch_last_ai_message(
                cur,
                session_keys=[str(lead_id), str(contact_id), phone],
                since_ts=start_ts - 5,
                timeout_sec=180,
            )
    if not ai_msg:
        return {
            "test": name,
            "lead_id": lead_id,
            "contact_id": contact_id,
            "phone": phone,
            "history": history,
            "status": "no_agent_response",
        }
    history.append({"role": "assistant", "content": ai_msg})

    # 4) Gerar próxima mensagem do "usuário" via LLM e iterar (máx. 5 turnos)
    for _ in range(4):
        user_reply = build_user_reply(system_profile, ai_msg, history)
        if not user_reply:
            break
        n8n_send_message(user_reply, lead_id, contact_id)
        history.append({"role": "user", "content": user_reply})

        turn_start = time.time()
        with _pg_conn() as conn:
            with conn.cursor() as cur:
                ai_msg = _fetch_last_ai_message(
                    cur,
                    session_keys=[str(lead_id), str(contact_id), phone],
                    since_ts=turn_start - 5,
                    timeout_sec=180,
                )
        if not ai_msg:
            break
        history.append({"role": "assistant", "content": ai_msg})

        # condição simples de parada: se agente indicar handoff/agendamento
        if any(k in ai_msg.lower() for k in ["transferir", "agendar", "agendamento", "atendente"]):
            break

    return {
        "test": name,
        "lead_id": lead_id,
        "contact_id": contact_id,
        "phone": phone,
        "history": history,
        "status": "ok",
    }


def main():
    os.makedirs("runs", exist_ok=True)
    results: List[Dict[str, Any]] = []
    for i, sc in enumerate(SCENARIOS):
        print(f"Iniciando {sc['name']}...")
        try:
            res = run_conversation(i, sc)
            results.append(res)
            print(f"Concluído: {res['status']} lead={res.get('lead_id')}")
            with open(f"runs/run_{i+1}_{sc['name']}.json", "w", encoding="utf-8") as f:
                json.dump(res, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro no teste {sc['name']}: {e}")
    # resumo geral
    with open("runs/results_summary.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Pronto. Resultados em runs/.")


if __name__ == "__main__":
    main()
