import os
import sys
import json
import logging
import threading
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Render port health check
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is live!")

    def log_message(self, format, *args):
        return

def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

def parse_text_to_dict(text: str) -> dict:
    """Parses plain text lines like 'weight 50' or 'name: Alex' into a dictionary."""
    data = {}
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        
        if ":" in line:
            parts = line.split(":", 1)
        else:
            parts = line.split(maxsplit=1)
        
        if len(parts) == 2:
            key = parts[0].strip().lower().replace(" ", "_")
            val = parts[1].strip()
            
            if val.isdigit():
                val = int(val)
            else:
                try:
                    val = float(val)
                except ValueError:
                    pass
            
            if isinstance(val, str) and "," in val:
                val = [item.strip() for item in val.split(",")]

            data[key] = val
    return data

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Paste your client assessment text directly into this chat!\n\n"
        "Example format:\n"
        "name: Alex\n"
        "weight: 70\n"
        "height: 175\n"
        "fitness_goal: hypertrophy"
    )

async def handle_pasted_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    data = parse_text_to_dict(text)
    if not data:
        await update.message.reply_text("❌ Could not read any details. Please paste lines like:\nname: John\nweight: 70")
        return

    await update.message.reply_text("⏳ Assessment received! Building PDF plan...")

    temp_json = f"temp_{user_id}.json"
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    output_pdf = os.path.join(output_dir, f"{user_id}_plan.pdf")

    try:
        with open(temp_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

        # Runs generate.py directly from the root folder
        subprocess.run(
            [sys.executable, "generate.py", temp_json, output_pdf],
            check=True
        )

        client_name = str(data.get("name", "Client")).replace(" ", "_")
        if os.path.exists(output_pdf):
            with open(output_pdf, "rb") as pdf_file:
                await update.message.reply_document(
                    document=pdf_file,
                    filename=f"{client_name}_Plan.pdf",
                    caption="✅ Plan generated successfully!"
                )
        else:
            await update.message.reply_text("❌ PDF generation failed.")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error processing assessment: {str(e)}")

    finally:
        if os.path.exists(temp_json):
            os.remove(temp_json)
        if os.path.exists(output_pdf):
            os.remove(output_pdf)

def main():
    threading.Thread(target=run_health_check, daemon=True).start()

    token = os.getenv("BOT_TOKEN")
    if not token:
        print("BOT_TOKEN missing!")
        return

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pasted_text))

    app.run_polling()

if __name__ == "__main__":
    main()
