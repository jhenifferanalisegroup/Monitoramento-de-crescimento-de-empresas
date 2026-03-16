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
        SELECT cnpj_empresa, total_entrada, data_snapshot
        FROM gestfiscal_snapshotentradas
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
        "total_entrada": result.total_entrada,
        "data_snapshot": result.data_snapshot
    }


def buscar_ultimo_snapshot(cnpj):
    """
    Retorna o último snapshot da empresa
    """

    query = text("""
        SELECT cnpj_empresa, total_entrada, data_snapshot
        FROM gestfiscal_snapshotentradas
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
        "total_entrada": result.total_entrada,
        "data_snapshot": result.data_snapshot
    }


def salvar_snapshot(cnpj, total_entrada):
    """
    Salva um novo snapshot no histórico.
    Só insere se o CNPJ existir na tabela cliente_cliente (restrição de FK).
    """

    # Verifica se o CNPJ existe na tabela de clientes (cliente_cliente)
    # A tabela possui apenas a coluna "cnpj" (sem cnpj_empresa)
    check_query = text("""
        SELECT 1
        FROM cliente_cliente
        WHERE cnpj = :cnpj
        LIMIT 1
    """)

    insert_query = text("""
        INSERT INTO gestfiscal_snapshotentradas (cnpj_empresa, total_entrada, data_snapshot)
        VALUES (:cnpj_empresa, :total_entrada, :data_snapshot)
    """)

    with engine.begin() as conn:
        exists = conn.execute(check_query, {"cnpj": cnpj}).fetchone()
        if not exists:
            # CNPJ não está cadastrado em cliente_cliente, não insere para evitar erro de FK
            return

        conn.execute(insert_query, {
            "cnpj_empresa": cnpj,
            "total_entrada": total_entrada,
            "data_snapshot": datetime.now()
        })