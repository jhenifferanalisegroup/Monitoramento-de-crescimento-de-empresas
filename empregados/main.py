import pandas as pd
import requests
from datetime import datetime
from betha_service import consultar_quantidade_empregados
from historico_service import buscar_ultimo_snapshot, salvar_snapshot
from alerta_service import enviar_email_alerta


PERCENTUAL_ALERTA = 0.20


def calcular_crescimento(atual, anterior):

    if anterior == 0:
        return 1.0

    return (atual - anterior) / anterior




def executar():

    df = consultar_quantidade_empregados()

    for _, row in df.iterrows():

        empresa = row["nome_emp"]
        cnpj = row["cnpj"]
        total_atual = row["total_empregados_ativos"]

        snapshot_anterior = buscar_ultimo_snapshot(cnpj)

        if snapshot_anterior is None:
            salvar_snapshot(cnpj, total_atual)
            continue

        total_anterior = snapshot_anterior["total_ativos"]

        crescimento = calcular_crescimento(total_atual, total_anterior)

        if crescimento >= PERCENTUAL_ALERTA:
            enviar_email_alerta(
                empresa,
                cnpj,
                total_anterior,
                total_atual,
                crescimento
            )

        salvar_snapshot(cnpj, total_atual)


if __name__ == "__main__":
    executar()