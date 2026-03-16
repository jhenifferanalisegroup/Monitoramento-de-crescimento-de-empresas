import pyodbc
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

DSN = os.getenv("ODBC_DSN")
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")

emp = 58
data1 = "2026-01-01"
data2 = "2026-01-31"
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


def consultar_entradas_empresa(data_ini, data_fim):
    """
    Consulta a quantidade de empregados ativos por empresa
    """

    query = """
    SELECT 
        YEAR(efentradas.ddoc_ent)  AS ano,
        MONTH(efentradas.ddoc_ent) AS mes,
        geempre.codi_emp,
        geempre.cida_emp AS cidade,
        geempre.cgce_emp AS cnpj,
        geempre.nome_emp AS empresa,
        SUM(efentradas.vcon_ent) AS valor_contabil
    FROM bethadba.efentradas
    JOIN bethadba.geempre 
        ON geempre.codi_emp = efentradas.codi_emp
    WHERE efentradas.ddoc_ent BETWEEN ? AND ?
    GROUP BY 
        YEAR(efentradas.ddoc_ent),
        MONTH(efentradas.ddoc_ent),
        geempre.codi_emp,
        geempre.cgce_emp,
        geempre.nome_emp,
        geempre.cida_emp
    ORDER BY 
        ano,
        mes,
        geempre.codi_emp
    """

    conn = get_connection()

    try:

        df = pd.read_sql(query, conn, params=(data_ini, data_fim))

        if df.empty:
            print("Nenhum empregado encontrado.")
            return df

        print(f"{len(df)} empresas consultadas.")
        print(df)
        df.to_excel("resultado_consulta_entradas.xlsx", index=False)
        return df

    except Exception as e:
        raise Exception(f"Erro na consulta de empregados: {e}")

    finally:
        conn.close()

consultar_entradas_empresa(data1, data2)