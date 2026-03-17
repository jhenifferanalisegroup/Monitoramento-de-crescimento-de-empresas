import requests
import os
import resend
from dotenv import load_dotenv

def montar_email(alertas):
    if not alertas:
        return None
    linhas = []
    for a in alertas:
        linha = f"""
                    <tr>
                        <td style="padding:6px 4px;">{a['codigo']}</td>
                        <td style="padding:6px 4px;">{a['cnpj']}</td>
                        <td style="padding:6px 4px; word-break:break-word;">{a['empresa']}</td>
                        <td style="padding:6px 4px;" align="right">{a['total_anterior']}</td>
                        <td style="padding:6px 4px;" align="right">{a['total_atual']}</td>
                        <td style="padding:6px 4px;" align="right">{a['crescimento_anterior']*100:.2f}%</td>
                    </tr>
                """
        linhas.append(linha)

    html = f"""
    <html>
        <body style="margin:0; padding:0; background-color:#f5f5f5; font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f5f5f5; padding:24px 0; font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                <tr>
                    <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff; border-radius:8px; overflow:hidden; font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color:#000000;">
                            <tr>
                                <td style="background-color:#000000; padding:12px 12px;" align="left">
                                    <img src="https://i.imgur.com/YVsuqX1.png" alt="Logo" style="height:80px; display:block;" />
                                </td>
                            </tr>
                            <tr>
                                <td style="padding:24px;">
                                    <h1 style="margin:0 0 8px 0; font-size:22px; color:#000000;">Alerta de crescimento de entradas (compras)</h1>
                                    <p style="margin:0 0 16px 0; font-size:14px; color:#333333;">
                                        As empresas abaixo apresentaram crescimento de entradas (compras) acima de 20% em pelo menos um dos cenários monitorados.
                                    </p>
                                    <table width="100%" cellpadding="4" cellspacing="0" style="border-collapse:separate; border-spacing:0; font-size:12px;">
                                        <colgroup>
                                            <col style="width:10%">
                                            <col style="width:19%">
                                            <col style="width:17%">
                                            <col style="width:20%">
                                            <col style="width:20%">
                                            <col style="width:20%">
                                            <col style="width:20%">
                                        </colgroup>
                                        <thead>
                                            <tr style="background-color:#D1B48B; color:#000000;">
                                                <!--<th align="left" style="padding:8px; border-radius:8px 0 0 0;">Referência</th>-->
                                                <th align="left" style="padding:8px;">Código</th>
                                                <th align="left" style="padding:8px;">CNPJ</th>
                                                <th align="left" style="padding:8px;">Empresa</th>
                                                
                                                <th align="right" style="padding:8px;">Entradas (anterior)</th>
                                                <th align="right" style="padding:8px;">Entradas (Atual)</th>
                                                <th align="right" style="padding:8px; border-radius:0 8px 0 0;">Crescimento (mês)</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {''.join(linhas)}
                                        </tbody>
                                    </table>
                                </td>
                            </tr>
                            <tr>
                                <td style="background-color:#faf4ea; padding:12px 24px; font-size:11px; color:#555555;" align="right">
                                    Monitoramento automático de evolução de entradas (compras)
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
    </html>
    """
    return html


def enviar_email_alerta(html):
    load_dotenv()
    resend.api_key = os.getenv("RESEND_API_KEY")

    #print(resend.api_key)
    params: resend.Emails.SendParams ={
        "from":f"Alerta de Crescimento de Entradas (Compras) - Análise Group <ti@gesthub.analisegroup.cnt.br>",
        "to":["jheniffer@analisegroup.cnt.br", "jonathan.viana@analisegroup.cnt.br"],
        "subject":"Crescimento de entradas (compras) detectado",
        "html": html
    }
    email = resend.Emails.send(params)
    print(email)
    
 