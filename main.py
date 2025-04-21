from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from http.server import HTTPServer, SimpleHTTPRequestHandler
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from secret import SECRET_TELEGRAM_API_KEY
from selenium import webdriver
from telegram import Update
import subprocess
import functools
import threading
import signal
import json
import sys
import os


admin_chat_id = -1002571293789
no_auth_msg = "Это админская команда, работает только в чате https://t.me/+IBkZEqKkqRlhNGQy"
DEFAULT_URL = "http://127.0.0.1:8000/"


def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.id != admin_chat_id:
            await update.message.reply_text(no_auth_msg)
            return
        await func(update, context)
    return wrapper


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        json.dumps(update.to_dict(), ensure_ascii=False, indent=2)
    )


@admin_only
async def reload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    driver.refresh()
    await update.message.reply_text("🔄 Страница перезагружена")


@admin_only
async def produrl_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    driver.get(DEFAULT_URL)
    await update.message.reply_text("🌐🔒 Загружен продовый URL {DEFAULT_URL}")


@admin_only
async def url_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        custom_url = context.args[0]
        driver.get(custom_url)
        await update.message.reply_text(f"🌐🧪 Загружен тестовый URL {custom_url}")
    else:
        driver.get(DEFAULT_URL)
        await update.message.reply_text("🌐🔒 Загружен продовый URL {DEFAULT_URL}")


@admin_only
async def deploy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subprocess.run(["git", "pull"])
    await update.message.reply_text("🚀 git pull = ok, крешимся для перезапуска супервизором 😂")
    sys.exit(0)


def cleanup(signum, frame):
    driver.quit()
    sys.exit(0)


signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

handler_class = functools.partial(SimpleHTTPRequestHandler, directory="./static/")
httpd = HTTPServer(("127.0.0.1", 8000), handler_class)

def serve():
    httpd.serve_forever()

thread = threading.Thread(target=serve, daemon=True)
thread.start()

os.environ['DISPLAY'] = ':0'

options = Options()
options.add_argument("--kiosk")
options.add_argument("--no-first-run")
options.add_argument("--disable-infobars")
options.add_argument("--noerrdialogs")
options.add_argument("--use-fake-ui-for-media-stream")
options.add_experimental_option("excludeSwitches", ["enable-automation"])

service = Service("/usr/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=options)
driver.get(DEFAULT_URL)

application: Application = Application.builder().token(SECRET_TELEGRAM_API_KEY).build()

application.add_handler(CommandHandler("reload", reload_handler))
application.add_handler(CommandHandler("produrl", produrl_handler))
application.add_handler(CommandHandler("url", url_handler))
application.add_handler(CommandHandler("deploy", deploy_handler))
application.add_handler(MessageHandler(filters.ALL, message_handler))

application.run_polling()
