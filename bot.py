import logging
import os
import datetime
import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
PAYPAL_EMAIL = "tucorreo@paypal.com"  # Reemplaza con tu correo real
ADMIN_ID = 123456789  # Reemplaza con tu ID de Telegram

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PLANES = {
    "gratuito": {"precio": 0, "mensajes_dia": 20, "tokens_dia": 500},
    "basico": {"precio": 4.99, "mensajes_dia": 200, "tokens_dia": 2000},
}

user_data = {}

niveles = ["Primaria", "Secundaria", "Universidad"]
estilos = ["Formal", "Informal", "Resumido", "Detallado"]
idiomas = ["Español", "Inglés", "Portugués"]

def reset_uso_diario(user_id):
    hoy = datetime.date.today()
    if user_id not in user_data:
        return
    if user_data[user_id]["fecha_uso"] != hoy:
        user_data[user_id]["uso"] = {"mensajes": 0, "tokens": 0}
        user_data[user_id]["fecha_uso"] = hoy

def consultar_deepseek(prompt_usuario):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt_usuario}]
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"Error DeepSeek: {e}")
        return "Error al procesar la solicitud."

def inicializar_usuario(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            "plan": "gratuito",
            "uso": {"mensajes": 0, "tokens": 0},
            "fecha_uso": datetime.date.today(),
            "nivel": "Universidad",
            "estilo": "Formal",
            "idioma": "Español"
        }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    inicializar_usuario(user_id)

    keyboard = [
        [InlineKeyboardButton("💬 Hacer una Pregunta", callback_data="pregunta")],
        [InlineKeyboardButton("📖 Explicar un Tema", callback_data="explicar_tema")],
        [InlineKeyboardButton("📝 Ayuda con Tareas", callback_data="ayuda_tareas")],
        [InlineKeyboardButton("⚙️ Configuración", callback_data="configuracion")],
    ]
    texto = (
        f"Hola {update.message.from_user.first_name}!\n"
        f"Tu plan actual es *{user_data[user_id]['plan'].capitalize()}*\n\n"
        f"Elige una opción para comenzar."
    )
    await update.message.reply_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    inicializar_usuario(user_id)
    data = query.data

    if data in ["pregunta", "explicar_tema", "ayuda_tareas"]:
        context.user_data['modo'] = data
        await query.edit_message_text("✍️ Escribe tu solicitud y te ayudaré.")
        return

    if data == "configuracion":
        keyboard = [
            [InlineKeyboardButton("🎓 Nivel Educativo", callback_data="cfg_nivel")],
            [InlineKeyboardButton("🔊 Estilo de Respuesta", callback_data="cfg_estilo")],
            [InlineKeyboardButton("🌐 Idioma", callback_data="cfg_idioma")],
            [InlineKeyboardButton("🔁 Reiniciar Conversación", callback_data="cfg_reset")],
            [InlineKeyboardButton("💼 Cambiar Plan", callback_data="cfg_plan")],
        ]
        await query.edit_message_text("⚙️ Configuración:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == "cfg_plan":
        texto = (
            "💡 *Selecciona el plan que más se ajuste a tus necesidades:*\n\n"
            "🔓 *Gratuito*\n   • 💰 Precio: $0\n   • 💬 Mensajes/día: 20\n   • 🧠 Tokens/día: 500\n\n"
            "🔹 *Básico*\n   • 💰 Precio: $4.99/mes\n   • 💬 Mensajes/día: 200\n   • 🧠 Tokens/día: 2,000\n\n"
            "🔸 *Pro*\n   • 💰 Precio: $9.99/mes\n   • 💬 Mensajes/día: 500\n   • 🧠 Tokens/día: 5,000\n\n"
            "🚀 *Ilimitado*\n   • 💰 Precio: $19.99/mes\n   • 💬 Mensajes/día: Ilimitados\n   • 🧠 Tokens/día: 15,000\n\n"
            "👉 *Pulsa uno de los botones para cambiar de plan.*"
        )
        botones_planes = [
            [InlineKeyboardButton("🔓 Gratuito", callback_data="plan_gratuito")],
            [InlineKeyboardButton("🔹 Básico", callback_data="plan_basico")],
            [InlineKeyboardButton("🔸 Pro", callback_data="plan_pro")],
            [InlineKeyboardButton("🚀 Ilimitado", callback_data="plan_ilimitado")],
        ]
        await query.edit_message_text(texto, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(botones_planes))
        return

    if data == "plan_gratuito":
        await query.edit_message_text(
            "🔓 *Plan Gratuito*\n\n"
            "💬 20 mensajes por día\n"
            "🧠 500 tokens por día\n"
            "💰 Costo: *$0*\n\n"
            "Este plan es ideal para uso casual.",
            parse_mode="Markdown"
        )
        return

    if data == "plan_basico":
        await query.edit_message_text(
            "🔹 *Plan Básico*\n\n"
            "💬 200 mensajes por día\n"
            "🧠 2,000 tokens por día\n"
            "💰 Costo: *$4.99/mes*\n\n"
            f"📩 Para activarlo, envía el pago a *{PAYPAL_EMAIL}* por PayPal y responde aquí con el comprobante.",
            parse_mode="Markdown"
        )
        return

    if data == "plan_pro":
        await query.edit_message_text(
            "🔸 *Plan Pro*\n\n"
            "💬 500 mensajes por día\n"
            "🧠 5,000 tokens por día\n"
            "💰 Costo: *$9.99/mes*\n\n"
            f"📩 Envía el pago a *{PAYPAL_EMAIL}* por PayPal para activar este plan.",
            parse_mode="Markdown"
        )
        return

    if data == "plan_ilimitado":
        await query.edit_message_text(
            "🚀 *Plan Ilimitado*\n\n"
            "💬 Mensajes ilimitados por día\n"
            "🧠 15,000 tokens por día\n"
            "💰 Costo: *$19.99/mes*\n\n"
            f"📩 Envía el pago a *{PAYPAL_EMAIL}* por PayPal para activar este plan.",
            parse_mode="Markdown"
        )
        return

    if data == "cfg_reset":
        user_data[user_id]["uso"] = {"mensajes": 0, "tokens": 0}
        await query.edit_message_text("🔁 Conversación reiniciada. Usa /start para comenzar de nuevo.")
        return

    if data == "cfg_nivel":
        botones = [[InlineKeyboardButton(n, callback_data=f"nivel_{n}")] for n in niveles]
        await query.edit_message_text("Selecciona tu nivel educativo:", reply_markup=InlineKeyboardMarkup(botones))
        return

    if data.startswith("nivel_"):
        user_data[user_id]["nivel"] = data.split("_")[1]
        await query.edit_message_text(f"✅ Nivel educativo actualizado a {user_data[user_id]['nivel']}.")
        return

    if data == "cfg_estilo":
        botones = [[InlineKeyboardButton(e, callback_data=f"estilo_{e}")] for e in estilos]
        await query.edit_message_text("Selecciona el estilo de respuesta:", reply_markup=InlineKeyboardMarkup(botones))
        return

    if data.startswith("estilo_"):
        user_data[user_id]["estilo"] = data.split("_")[1]
        await query.edit_message_text(f"✅ Estilo de respuesta actualizado a {user_data[user_id]['estilo']}.")
        return

    if data == "cfg_idioma":
        botones = [[InlineKeyboardButton(i, callback_data=f"idioma_{i}")] for i in idiomas]
        await query.edit_message_text("Selecciona el idioma:", reply_markup=InlineKeyboardMarkup(botones))
        return

    if data.startswith("idioma_"):
        user_data[user_id]["idioma"] = data.split("_")[1]
        await query.edit_message_text(f"✅ Idioma actualizado a {user_data[user_id]['idioma']}.")
        return

    await query.edit_message_text("❌ Opción no reconocida.")

async def texto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    inicializar_usuario(user_id)
    reset_uso_diario(user_id)

    plan = user_data[user_id]["plan"]
    uso = user_data[user_id]["uso"]
    max_msgs = PLANES[plan]["mensajes_dia"]
    max_tokens = PLANES[plan]["tokens_dia"]

    if uso["mensajes"] >= max_msgs:
        await update.message.reply_text(f"❌ Has alcanzado tu límite diario de mensajes.")
        return

    tokens_estimados = 100
    if uso["tokens"] + tokens_estimados > max_tokens:
        await update.message.reply_text(f"❌ Has alcanzado tu límite diario de tokens.")
        return

    modo = context.user_data.get('modo', 'pregunta')
    texto = update.message.text
    nivel = user_data[user_id].get("nivel", "Universidad")
    estilo = user_data[user_id].get("estilo", "Formal")
    idioma = user_data[user_id].get("idioma", "Español")

    if modo == "pregunta":
        prompt = f"Responde la siguiente pregunta de forma {estilo}, en idioma {idioma}, para un estudiante de nivel {nivel}: {texto}"
    elif modo == "explicar_tema":
        prompt = f"Explica el siguiente tema de forma {estilo}, en idioma {idioma}, para un estudiante de nivel {nivel}: {texto}"
    elif modo == "ayuda_tareas":
        prompt = f"Ayuda con esta tarea. Proporciona la mejor explicación en estilo {estilo}, idioma {idioma}, para nivel {nivel}: {texto}"
    else:
        prompt = texto

    respuesta = consultar_deepseek(prompt)
    uso["mensajes"] += 1
    uso["tokens"] += tokens_estimados
    user_data[user_id]["uso"] = uso

    await update.message.reply_text(respuesta)

async def activar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        _, username = context.args
        for uid, datos in user_data.items():
            chat = await context.bot.get_chat(uid)
            if chat.username == username:
                datos["plan"] = "basico"
                await update.message.reply_text(f"✅ Plan básico activado para @{username}.")
                return
        await update.message.reply_text("❌ Usuario no encontrado.")
    except:
        await update.message.reply_text("❌ Uso correcto: /activar usuario")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activar", activar))
    app.add_handler(CallbackQueryHandler(menu_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, texto_handler))

    logger.info("🤖 Bot iniciado...")
    app.run_polling()

if __name__ == "__main__":
    main()
