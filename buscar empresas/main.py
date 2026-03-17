import pyodbc
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DSN = os.getenv("ODBC_DSN")
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")

DB_URI = os.getenv("DATABASE_URL")

engine = create_engine(DB_URI)

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

def consultar_empresas():
    """
    Consulta a quantidade de empregados ativos por empresa
    """
    query = """
    SELECT
        ge.razao_emp AS razao_social,
        ge.cgce_emp AS cnpj,
        est.sigla_uf AS uf,
        ge.cida_emp AS cidade
    FROM bethadba.geempre ge
    LEFT JOIN bethadba.gemunicipio mun 
        ON mun.codigo_municipio = ge.codigo_municipio
    LEFT JOIN bethadba.geestado est 
        ON est.codigo_uf = mun.codigo_uf
    WHERE ge.stat_emp = 'A'
    ORDER BY ge.cgce_emp, ge.cida_emp, ge.nome_emp;
    """
    conn = get_connection()

    try:

        df = pd.read_sql(query, conn)
    
        if df.empty:
            print("Nenhum empregado encontrado.")
            return df

        print(f"{len(df)} empresas consultadas.")
        print(df)
        df.to_excel("resultado_consulta_empresas.xlsx", index=False)
        return df

    except Exception as e:
        raise Exception(f"Erro na consulta de empregados: {e}")

    finally:
        if conn:
            conn.close()
            
def salvar_no_banco(df):
    """
    Salva as empresas no banco de dados
    """
    # Ajusta os nomes das colunas do DataFrame para bater com o schema do banco
    df_db = df.rename(columns={"razao_social": "nome"}).copy()

    # Garante a coluna telefone com valor padrão string vazia
    if "telefone" not in df_db.columns:
        df_db["telefone"] = ""

    # Substitui NaN por None para não quebrar na inserção
    df_db = df_db.where(pd.notna(df_db), None)

    query = """
    INSERT INTO cliente_cliente (nome, cnpj, uf, cidade, telefone)
    VALUES (:nome, :cnpj, :uf, :cidade, :telefone)
    ON CONFLICT (cnpj)
    DO UPDATE SET
        nome = EXCLUDED.nome,
        uf = EXCLUDED.uf,
        cidade = EXCLUDED.cidade,
        telefone = EXCLUDED.telefone
    """
    with engine.connect() as conn:
        conn.execute(text(query), df_db.to_dict(orient='records'))
        
df = consultar_empresas()
salvar_no_banco(df)