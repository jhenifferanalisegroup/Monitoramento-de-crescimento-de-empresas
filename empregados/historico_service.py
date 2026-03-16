import os
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_URI = os.getenv("DATABASE_URL")

engine = create_engine(DB_URI)

def buscar_primeiro_snapshot(cnpj):
    """
    Retorna o último snapshot da empresa
    """

    query = text("""
        SELECT cnpj_empresa, total_ativos, data_snapshot
        FROM gestfiscal_snapshotempregados
        WHERE cnpj_empresa = :cnpj_empresa
        ORDER BY data_snapshot ASC
        LIMIT 1
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"cnpj_empresa": cnpj}).fetchone()

    if result is None:
        return None

    return {
        "cnpj_empresa": result.cnpj_empresa,
        "total_ativos": result.total_ativos,
        "data_snapshot": result.data_snapshot
    }


def buscar_ultimo_snapshot(cnpj):
    """
    Retorna o último snapshot da empresa
    """

    query = text("""
        SELECT cnpj_empresa, total_ativos, data_snapshot
        FROM gestfiscal_snapshotempregados
        WHERE cnpj_empresa = :cnpj_empresa
        ORDER BY data_snapshot DESC
        LIMIT 1
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"cnpj_empresa": cnpj}).fetchone()

    if result is None:
        return None

    return {
        "cnpj_empresa": result.cnpj_empresa,
        "total_ativos": result.total_ativos,
        "data_snapshot": result.data_snapshot
    }


def salvar_snapshot(cnpj, total_ativos):
    """
    Salva um novo snapshot no histórico
    """

    query = text("""
        INSERT INTO gestfiscal_snapshotempregados (cnpj_empresa, total_ativos, data_snapshot)
        VALUES (:cnpj_empresa, :total_ativos, :data_snapshot)
    """)

    with engine.begin() as conn:
        conn.execute(query, {
            "cnpj_empresa": cnpj,
            "total_ativos": total_ativos,
            "data_snapshot": datetime.now()
        })