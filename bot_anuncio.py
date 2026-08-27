import os
import re
import requests
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# 🔑 Suas configurações (preencha no Environment do Render)
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
PHONE_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "")
GRUPO_DESTINO = os.getenv("GRUPO_DESTINO", "")  # Número/grupo: ex: 5571999999999

GRAPH_VERSION = "v23.0"

# 🎨 Gerar texto do anúncio a partir do link
def gerar_anuncio(link):
    # Extrair nome do produto do link (simplificado)
    nome_produto = "Produto em Oferta"
    # Tentar pegar algo mais legível
    match = re.search(r'([a-zA-Z0-9-]+)\.(shopee|mercadolivre)\.com', link.lower())
    if match:
        nome_produto = match.group(1).replace('-', ' ').title()

    return f"""
🔥🔥 *SUPER OFERTA!* 🔥🔥

🛒 *{nome_produto}*

💥 Não perca essa oportunidade!
✅ Melhor preço garantido
🚚 Entrega rápida

🔗 *Link para comprar:*
{link}

---
🤖 Enviado pelo PromoBot | Divulgue e lucre!
"""

# 📤 Enviar mensagem no WhatsApp
def enviar_whatsapp(destinatario, texto):
    if not WHATSAPP_TOKEN or not PHONE_ID:
        print(f"[MODO TESTE] Para {destinatario}:\n{texto}")
        return True

    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": destinatario,
        "type": "text",
        "text": {"body": texto}
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=20)
    resp.raise_for_status()
    return True

# ✅ Webhook de verificação
@app.get("/webhook")
def verificar():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Token inválido", 403

# 📩 Receber mensagens
@app.post("/webhook")
def receber():
    try:
        dados = request.get_json()
        valor = dados["entry"][0]["changes"][0]["value"]
        mensagens = valor.get("messages", [])

        if not mensagens:
            return "OK", 200

        msg = mensagens[0]
        remetente = msg["from"]
        texto = msg.get("text", {}).get("body", "").strip()

        # 📌 Se mandou um link → gera anúncio
        if any(dominio in texto.lower() for dominio in ["shopee", "mercadolivre", "amazon", "ali"]):
            anuncio = gerar_anuncio(texto)
            
            # Envia de volta para você confirmar
            enviar_whatsapp(remetente, "✅ *Anúncio gerado!* Vou enviar no grupo...\n\n" + anuncio)
            
            # Envia para o grupo
            if GRUPO_DESTINO:
                enviar_whatsapp(GRUPO_DESTINO, anuncio)
                enviar_whatsapp(remetente, "✅ *Enviado no grupo com sucesso!* 🚀")
            else:
                enviar_whatsapp(remetente, "⚠️ Grupo não configurado! O anúncio foi gerado, mas faltou o número do grupo.")

        # 📌 Comandos
        elif texto.lower() in ["oi", "menu", "ajuda"]:
            enviar_whatsapp(remetente, """
🤖 *PROMO ANÚNCIO BOT* 🤖

Mande um link de afiliado que eu:
✅ Crio o texto do anúncio
✅ Envio no grupo automaticamente!

👉 É só mandar o link!
""")
        else:
            enviar_whatsapp(remetente, "👋 Mande um link de afiliado (Shopee, Mercado Livre...) que eu gero o anúncio e envio no grupo!")

    except Exception as e:
        print("Erro:", e)
    return "OK", 200

@app.get("/")
def home():
    return "🤖 Bot de Anúncios ONLINE! Mande seu link de afiliado."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
