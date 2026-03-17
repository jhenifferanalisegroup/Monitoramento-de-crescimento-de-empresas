## Monitoramento de Evolução de Empresa

Este projeto realiza o monitoramento de evolução de empresas em três dimensões principais:

- **Empresas** (cadastro base)
- **Empregados** (quantidade de empregados ativos)
- **Entradas (compras)**
- **Faturamento**

e integra esses dados em um banco interno (Postgres) para análise e alertas por e‑mail.

---

## 1. Buscar Empresas (popular `cliente_cliente`)

**Pasta**: `buscar empresas/`  
**Arquivo principal**: `main.py`

### Objetivo

- Consultar o cadastro de empresas no banco Betha/Domínio (via ODBC).
- Popular/atualizar a tabela `cliente_cliente` no banco Postgres (`DATABASE_URL`).

### Fluxo

1. `get_connection()`
   - Cria conexão ODBC com Betha usando as variáveis de ambiente:
     - `ODBC_DSN`
     - `DB_USER`
     - `DB_PASSWORD`

2. `consultar_empresas()`
   - Executa:
     ```sql
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
     ```
   - Retorna um `DataFrame` com colunas: `razao_social`, `cnpj`, `uf`, `cidade`.
   - Salva o resultado em `resultado_consulta_empresas.xlsx`.

3. `salvar_no_banco(df)`
   - Usa `sqlalchemy.create_engine(DATABASE_URL)` para conectar no Postgres.
   - Renomeia `razao_social` → `nome`.
   - Garante coluna `telefone` (NOT NULL) com valor padrão `""`.
   - Converte `NaN` para `None`.
   - Executa um UPSERT por CNPJ:
     ```sql
     INSERT INTO cliente_cliente (nome, cnpj, uf, cidade, telefone)
     VALUES (:nome, :cnpj, :uf, :cidade, :telefone)
     ON CONFLICT (cnpj)
     DO UPDATE SET
         nome = EXCLUDED.nome,
         uf = EXCLUDED.uf,
         cidade = EXCLUDED.cidade,
         telefone = EXCLUDED.telefone;
     ```

### Execução

No diretório raiz do projeto:

```bash
python ".\buscar empresas\main.py"
```

---

## 2. Monitoramento de Empregados

**Pasta**: `empregados/`

### Objetivo

- Monitorar crescimento da quantidade de empregados ativos por empresa.
- Disparar e‑mail quando o crescimento (mês anterior e/ou desde 02/2026) for ≥ 20%.
- Registrar snapshots mensais em `gestfiscal_snapshotempregados`.

### Componentes

- `betha_service.py`
  - `consultar_quantidade_empregados()`:
    - Consulta via ODBC a quantidade atual de empregados por empresa.
    - Retorna `DataFrame` com colunas como `codi_emp`, `cnpj`, `nome_emp`, `total_empregados_ativos`.

- `historico_service.py`
  - Usa `DATABASE_URL` para criar o `engine`.
  - `buscar_primeiro_snapshot(cnpj)`:
    - Lê o **primeiro** registro de `gestfiscal_snapshotempregados` para o CNPJ (menor `data_snapshot`).
    - Retorna `{"cnpj_empresa", "total_ativos", "data_snapshot}` ou `None`.
  - `buscar_ultimo_snapshot(cnpj)`:
    - Lê o **último** registro (maior `data_snapshot`).
    - Retorna `{"cnpj_empresa", "total_ativos", "data_snapshot}` ou `None`.
  - `salvar_snapshot(cnpj, total_ativos)`:
    - Insere em:
      ```sql
      INSERT INTO gestfiscal_snapshotempregados (cnpj_empresa, total_ativos, data_snapshot)
      VALUES (:cnpj_empresa, :total_ativos, :data_snapshot);
      ```

- `alerta_service.py`
  - `montar_email(alertas)`:
    - Recebe uma lista de dicionários com dados da empresa e dos crescimentos.
    - Gera um HTML com:
      - Header preto com logo `https://i.imgur.com/YVsuqX1.png`.
      - Fonte: `'Segoe UI', Tahoma, Geneva, Verdana, sans-serif`.
      - Tabela com cabeçalho em `#D1B48B` e corpo em branco.
  - `enviar_email_alerta(html)`:
    - Carrega `RESEND_API_KEY` do `.env`.
    - Usa `resend.Emails.send` para enviar o e‑mail.

- `verificacao_envio_alerta.py`
  - `PERCENTUAL_ALERTA = 0.20`.
  - `calcular_percentual(atual, anterior)`:
    - Se `anterior == 0` → retorna `1.0` (100%).
    - Caso contrário: `(atual - anterior) / anterior`.
  - `executar_teste()`:
    - Chama `consultar_quantidade_empregados()`.
    - Para cada empresa:
      - Busca snapshots (`buscar_ultimo_snapshot`, `buscar_primeiro_snapshot`).
      - Calcula crescimento desde 02/2026 e vs mês anterior.
      - Quando o crescimento em relação ao mês anterior ≥ 20%:
        - Adiciona a empresa em `alertas_crescimento_anterior` e em `informacoes_empresas`.
  - Bloco `if __name__ == "__main__":`
    - Executa a verificação.
    - Monta e envia o e‑mail usando `montar_email(informacoes_empresas)` ou lista de alertas.
    - Opcionalmente salva snapshots para as empresas alertadas.

### Execução

```bash
python ".\empregados\verificacao_envio_alerta.py"
```

---

## 3. Monitoramento de Entradas (Compras)

**Pasta**: `entradas/`

### Objetivo

- Monitorar crescimento no valor de **entradas (compras)** por empresa.
- Comparar o valor atual com o **último snapshot**.
- Enviar alerta quando o crescimento mensal ≥ 20%.
- Atualizar snapshots em `gestfiscal_snapshotentradas`.

### Componentes

- `betha_service.py`
  - `consultar_entradas_empresa(data_ini, data_fim)`:
    - Consulta via ODBC os valores contábeis de entradas no período.
    - Query (resumo):
      ```sql
      SELECT 
          YEAR(efentradas.ddoc_ent)  AS ano,
          MONTH(efentradas.ddoc_ent) AS mes,
          geempre.codi_emp,
          geempre.cida_emp AS cidade,
          geempre.cgce_emp AS cnpj,
          geempre.nome_emp AS empresa,
          SUM(efentradas.vcon_ent) AS valor_contabil
      ...
      WHERE efentradas.ddoc_ent BETWEEN ? AND ?
      GROUP BY ...
      ORDER BY ano, mes, geempre.codi_emp;
      ```
    - Salva resultado em `resultado_consulta_entradas.xlsx`.

- `historico_service.py`
  - `buscar_primeiro_snapshot(cnpj)`:
    - Seleciona o primeiro registro de `gestfiscal_snapshotentradas` para o CNPJ.
    - Retorna `{"cnpj_empresa", "total_entrada", "data_snapshot}`.
  - `buscar_ultimo_snapshot(cnpj)`:
    - Seleciona o último registro de `gestfiscal_snapshotentradas`.
    - Retorna `{"cnpj_empresa", "total_entrada", "data_snapshot}`.
  - `salvar_snapshot(cnpj, total_entrada)`:
    - Verifica se o CNPJ existe em `cliente_cliente`:
      ```sql
      SELECT 1
      FROM cliente_cliente
      WHERE cnpj = :cnpj
      LIMIT 1;
      ```
    - Se existir, insere:
      ```sql
      INSERT INTO gestfiscal_snapshotentradas (cnpj_empresa, total_entrada, data_snapshot)
      VALUES (:cnpj_empresa, :total_entrada, :data_snapshot);
      ```

- `salvar_snapshot.py`
  - Utilitário para carregar snapshots históricos de entradas a partir da consulta atual.

- `alerta_service.py`
  - `montar_email(alertas)`:
    - Cria HTML com:
      - Logo no topo.
      - Título “Alerta de crescimento de entradas (compras)”.
      - Tabela com colunas: Código, CNPJ, Empresa, Entradas (anterior), Entradas (atual), Crescimento (mês).
  - `enviar_email_alerta(html)`:
    - Envia e‑mail de alerta de entradas (compras) usando Resend.

- `verificacao_envio_alerta.py`
  - `PERCENTUAL_ALERTA = 0.20`.
  - `calcular_percentual(atual, anterior)` igual ao de empregados.
  - `executar_verificacao()`:
    1. Define intervalo de análise (`data_ini`, `data_fim`).
    2. Chama `consultar_entradas_empresa`.
    3. Para cada empresa:
       - Busca `snapshot_ultimo`.  
         - Se não existir: loga “Sem histórico de entradas” e adiciona à lista de empresas para salvar snapshot.
       - Se existir:
         - Obtém `total_entrada` como `total_anterior`.
         - Calcula crescimento vs mês anterior.
         - Sempre adiciona a empresa em `informacoes_empresas` (para atualizar snapshot).
         - Se crescimento ≥ 20%, adiciona em `alertas_crescimento_anterior`.
    4. Após o loop:
       - Monta e envia o e‑mail com `alertas_crescimento_anterior` (se houver).
       - Percorre `informacoes_empresas` e chama `salvar_snapshot(cnpj, total_atual)` para gravar o valor atual como novo snapshot.

### Execução

```bash
python ".\entradas\verificacao_envio_alerta.py"
```

---

## 4. Monitoramento de Faturamento

**Pasta**: `faturamento/`

> A estrutura de faturamento segue o mesmo padrão de **entradas**, porém aplicada aos valores de faturamento.

### Objetivo

- Consultar faturamento por empresa em um determinado período.
- Comparar o faturamento atual com o último snapshot.
- Enviar alertas quando o crescimento mensal ≥ 20%.
- Atualizar snapshots em `gestfiscal_snapshotfaturamento` (nome conforme seu schema).

### Componentes (padrão)

- `betha_service.py`
  - Função para consultar faturamento agregado por empresa no período (`consultar_faturamento_empresa`, por exemplo).

- `historico_service.py`
  - Funções análogas às de `entradas`:
    - `buscar_primeiro_snapshot(cnpj)`
    - `buscar_ultimo_snapshot(cnpj)`
    - `salvar_snapshot(cnpj, total_faturamento)`

- `alerta_service.py`
  - `montar_email(alertas)` com tabela de faturamento (anterior, atual, crescimento).
  - `enviar_email_alerta(html)` com assunto “Crescimento de faturamento detectado”.

- `salvar_snapshot.py`
  - Script para popular/atualizar os snapshots de faturamento a partir da consulta atual.

- `verificacao_envio_alerta.py` (quando implementado)
  - Fluxo idêntico ao de `entradas`, mas usando os serviços de faturamento.

---

## 5. Configuração e Dependências

### Variáveis de ambiente

Em cada módulo (pasta) há arquivos `.env` com, pelo menos:

- `ODBC_DSN` – DSN ODBC do banco Betha/Domínio.
- `DB_USER`, `DB_PASSWORD` – credenciais ODBC.
- `DATABASE_URL` – string de conexão Postgres para SQLAlchemy, por exemplo:
  - `postgresql+psycopg2://usuario:senha@host:porta/banco`
- `RESEND_API_KEY` – chave da API do Resend para envio de e‑mails.

### Bibliotecas principais

- `pyodbc` – conexão ODBC (Betha/Domínio).
- `pandas` – leitura/manipulação de resultados SQL.
- `sqlalchemy` – conexão e execução de comandos no Postgres.
- `psycopg2` – driver Postgres.
- `resend` – envio de e‑mails de alerta.
- `python-dotenv` – carregamento de variáveis dos arquivos `.env`.

---

## 6. Resumo dos Fluxos

- **Buscar Empresas** (`buscar empresas/main.py`):
  - Atualiza a base de clientes (`cliente_cliente`) a partir do Betha.

- **Empregados** (`empregados/`):
  - Compara quantidade atual de empregados vs snapshots históricos.
  - Gera e‑mails de alerta quando crescimento ≥ 20%.
  - Atualiza snapshots.

- **Entradas** (`entradas/`):
  - Compara valor atual de entradas vs último snapshot.
  - Gera e‑mails de alerta quando crescimento ≥ 20%.
  - Atualiza snapshots.

- **Faturamento** (`faturamento/`):
  - Mesmo padrão de entradas, focado em faturamento.

