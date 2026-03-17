from betha_service import consultar_entradas_empresa
from historico_service import buscar_ultimo_snapshot, salvar_snapshot
from alerta_service import enviar_email_alerta, montar_email


PERCENTUAL_ALERTA = 0.20
alertas_crescimento_anterior = []
informacoes_empresas = []


def calcular_percentual(atual, anterior):
    if anterior == 0:
        return 1.0
    return (atual - anterior) / anterior


def executar_verificacao():
    # Período de análise – ajuste conforme o mês desejado
    data_ini = "2026-02-01"
    data_fim = "2026-02-28"

    df = consultar_entradas_empresa(data_ini, data_fim)

    print(f"\nEmpresas encontradas (entradas): {len(df)}\n")

    for _, row in df.iterrows():
        empresa = row["empresa"]
        codigo = row["codi_emp"]
        cnpj = str(row["cnpj"])
        total_atual = row["valor_contabil"]

        snapshot_ultimo = buscar_ultimo_snapshot(cnpj)
        if snapshot_ultimo is None:
            print(f"⚪ {empresa} | Sem histórico de entradas")
            # mesmo sem histórico anterior, já passamos a registrar o snapshot atual
            informacoes_empresas.append(
                {
                    "cnpj": cnpj,
                    "total_atual": total_atual,
                }
            )
            continue

        total_anterior = snapshot_ultimo["total_entrada"]
        crescimento_anterior = calcular_percentual(total_atual, total_anterior)

        print(
            f"{cnpj} | {codigo} | {empresa} | anterior={total_anterior} | "
            f"atual={total_atual} | crescimento_anterior={crescimento_anterior*100:.2f}%"
        )

        informacoes_empresas.append(
            {
                "cnpj": cnpj,
                "total_atual": total_atual,
            }
        )

        if crescimento_anterior >= PERCENTUAL_ALERTA:
            print(f"🚨 ALERTA DE CRESCIMENTO DE ENTRADAS EM COMPARAÇÃO AO MÊS ANTERIOR! {empresa}\n")
            alertas_crescimento_anterior.append(
                {
                    "codigo": codigo,
                    "cnpj": cnpj,
                    "empresa": empresa,
                    "total_anterior": total_anterior,
                    "total_atual": total_atual,
                    "crescimento_anterior": crescimento_anterior,
                }
            )


if __name__ == "__main__":
    executar_verificacao()
    conteudo_email = montar_email(alertas_crescimento_anterior)

    if conteudo_email:
        enviar_email_alerta(conteudo_email)

    # Após o envio dos e-mails (ou mesmo sem e-mail), salva um snapshot para cada empresa avaliada
    #for info in informacoes_empresas:
    #    salvar_snapshot(info["cnpj"], info["total_atual"])