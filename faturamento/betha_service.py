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
data2 = "2026-01-30"
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


def consultar_saidas_empresa(empresa, data_ini, data_fim):
    """
    Consulta a quantidade de empregados ativos por empresa
    """

    query1 = """
    SELECT 
        efsaidas.ddoc_sai AS data,
        geempre.nome_emp,
        geempre.codi_emp,
        COUNT(DISTINCT efsaidas.codi_sai) AS quantidade_codi_sai,
        efsaidas.vcon_sai AS valor_contabil_sai
    FROM bethadba.efsaidas
    JOIN bethadba.geempre 
        ON geempre.codi_emp = efsaidas.codi_emp
    WHERE efsaidas.codi_emp = ?
    AND efsaidas.ddoc_sai BETWEEN ? AND ?
    GROUP BY 
        efsaidas.ddoc_sai,
        geempre.nome_emp,
        geempre.codi_emp
    ORDER BY 
        efsaidas.ddoc_sai
    """
    query = """
    SELECT 
        efsaidas.ddoc_sai AS data,
        geempre.nome_emp,
        geempre.codi_emp,
        efsaidas.codi_sai,
        efsaidas.vcon_sai AS valor_contabil_sai
    FROM bethadba.efsaidas
    JOIN bethadba.geempre 
        ON geempre.codi_emp = efsaidas.codi_emp
    WHERE efsaidas.codi_emp = ?
    AND efsaidas.ddoc_sai BETWEEN ? AND ?
    ORDER BY 
        efsaidas.ddoc_sai,
        efsaidas.codi_sai
    """

    conn = get_connection()

    try:

        df = pd.read_sql(query, conn, params=(empresa, data_ini, data_fim))

        if df.empty:
            print("Nenhum empregado encontrado.")
            return df

        print(f"{len(df)} empresas consultadas.")
        print(df)
        df.to_excel("resultado_consulta_saidas.xlsx", index=False)
        return df

    except Exception as e:
        raise Exception(f"Erro na consulta de empregados: {e}")

    finally:
        conn.close()

consultar_saidas_empresa(emp, data1, data2)