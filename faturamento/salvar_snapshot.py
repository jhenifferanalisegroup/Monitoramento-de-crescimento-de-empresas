from betha_service import consultar_saidas_empresa
from historico_service import buscar_ultimo_snapshot, buscar_primeiro_snapshot, salvar_snapshot


data_ini = "2026-02-01"
data_fim = "2026-02-28"

PERCENTUAL_ALERTA = 0.20
alertas_crescimento_primeiro = []
alertas_crescimento_anterior = []

informacoes_empresas = []

sem_historico = []

def calcular_percentual(atual, anterior):

    if anterior == 0:
        return 1.0

    crescimento = (atual - anterior) / anterior
    return crescimento


def executar_teste():

    df = consultar_saidas_empresa(data_ini, data_fim)

    print(f"\nEmpresas encontradas: {len(df)}\n")


#------------------ Verificação de crescimento desde 02/2026 ------------------
    for _, row in df.iterrows():

        empresa = row["empresa"]
        codigo = row["codi_emp"]
        cnpj = str(row["cnpj"])
        total_atual = row["valor_contabil_sai"]
        
        snapshot_ultimo = buscar_ultimo_snapshot(cnpj)
        if snapshot_ultimo is None:
            print(f"⚪ {empresa} | Sem histórico")
            informacoes_empresas.append(
                {
                    #"tipo": tipo_anterior,
                    "codigo": codigo,
                    "cnpj": cnpj,
                    "empresa": empresa,
                    "total_atual": total_atual,
                }
            )
            print(
                f"{cnpj} | {codigo} | {empresa} | atual={total_atual}"
            )

            continue


        snapshot_primeiro = buscar_primeiro_snapshot(cnpj)
        if snapshot_primeiro is None:
            print(f"⚠️ {empresa} | {cnpj} | {codigo} | Sem histórico")
            sem_historico.append(
                {
                    "codigo": codigo,
                    "cnpj": cnpj,
                    "empresa": empresa,
                }
            )
            continue

        total_primeiro = snapshot_primeiro["total_saida"]
        total_anterior = snapshot_ultimo["total_saida"]

        crescimento_primeiro = calcular_percentual(total_atual, total_primeiro)
        crescimento_anterior = calcular_percentual(total_atual, total_anterior)

        print(
            f"{cnpj} | {codigo} | {empresa} | primeiro={total_primeiro} | anterior={total_anterior} | atual={total_atual} | crescimento_primeiro={crescimento_primeiro*100:.2f}% | crescimento_anterior={crescimento_anterior*100:.2f}%"
        )
        

        informacoes_empresas.append(
            {
                #"tipo": tipo_anterior,
                "codigo": codigo,
                "cnpj": cnpj,
                "empresa": empresa,
                "total_primeiro": total_primeiro,
                "total_anterior": total_anterior,
                "total_atual": total_atual,
                "crescimento_primeiro": crescimento_primeiro,
                "crescimento_anterior": crescimento_anterior
            }
        )
    
        

if __name__ == "__main__":
    executar_teste()
    
    for info in informacoes_empresas:
        salvar_snapshot(info["cnpj"], info["total_saida"])