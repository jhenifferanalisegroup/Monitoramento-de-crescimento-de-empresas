import pyodbc
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

DSN = os.getenv("ODBC_DSN")
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")


def get_connection():
    """
    Cria conexão com banco da Betha/Domínio
    """

    try:
        conn = pyodbc.connect(
            f"DSN={DSN};UID={USER};PWD={PASSWORD}",
            timeout=10,
            autocommit=True
        )
        return conn

    except Exception as e:
        raise Exception(f"Erro ao conectar no banco Betha: {e}")


def consultar_quantidade_empregados():
    """
    Consulta a quantidade de empregados ativos por empresa
    """

    query = """
        SELECT
            e.codi_emp,
            g.nome_emp,
            g.cgce_emp AS cnpj,
            COUNT(*) AS total_empregados_ativos
        FROM bethadba.foempregados e
        JOIN bethadba.geempre g
            ON g.codi_emp = e.codi_emp
        WHERE NOT EXISTS (
            SELECT 1
            FROM bethadba.foafastamentos fa
            WHERE fa.codi_emp = e.codi_emp
            AND fa.i_empregados = e.i_empregados
            AND fa.i_afastamentos = 8
        )
        GROUP BY
            e.codi_emp,
            g.nome_emp,
            g.cgce_emp
        ORDER BY total_empregados_ativos DESC
    """

    conn = get_connection()

    try:

        df = pd.read_sql(query, conn)

        if df.empty:
            print("Nenhum empregado encontrado.")
            return df

        print(f"{len(df)} empresas consultadas.")

        return df

    except Exception as e:
        raise Exception(f"Erro na consulta de empregados: {e}")

    finally:
        conn.close()