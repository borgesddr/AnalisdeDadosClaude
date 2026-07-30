"""Cliente Supabase compartilhado — mesmo par URL/chave anônima usado pelo dashboard React.

Lê SUPABASE_URL / SUPABASE_KEY do .env na raiz do projeto (não duplica credenciais).
Somente leitura: RLS do projeto libera SELECT anônimo nas 4 tabelas.
"""

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from supabase import Client, create_client

ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ROOT_ENV)


@st.cache_resource
def get_client() -> Client:
    import os

    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY") or os.environ.get("VITE_SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL/SUPABASE_KEY não encontrados. Confirme o arquivo .env na raiz do projeto."
        )
    return create_client(url, key)
