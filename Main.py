import os
import sys
import logging
import threading
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 1. DUMMY HTTP SERVER FOR RENDER PORT CHECK
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is live and running!")

    def log_message(self, format, *args):
        return  # Silence HTTP request logging in terminal

def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    logging.info(f"Health check server listening on port {port}")
    server.serve_forever()

# 2. TELEGRAM BOT COMMAND HANDLERS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome! Send /generate to build your custom workout and nutrition PDF plan."
    )

async def generate_pdf_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text("⏳ Generating your PDF plan... Please wait a few seconds.")

    # Ensure output directory exists
    output_dir = os.path.join("blueprint_bot", "outputs")
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Run blueprint_bot/generate.py script
        subprocess.run(
            [sys.executable, os.path.join("blueprint_bot", "generate.py")],
            check=True
        )

        # Locate generated PDF in blueprint_bot/outputs/
        generated_files = [
            os.path.join(output_dir, f) 
            for f in os.listdir(output_dir) 
            if f.endswith(".pdf")
        ]

        if generated_files:
            latest_pdf = max(generated_files, key=os.path.getmtime)
            with open(latest_pdf, "rb") as pdf_file:
                await update.message.reply_document(
                    document=pdf_file,
                    filename="Custom_Blueprint_Plan.pdf",
                    caption="✅ Here is your generated fitness plan!"
                )
        else:
            await update.message.reply_text("❌ Error: PDF was not generated.")

    except Exception as e:
        logging.error(f"Error during PDF generation: {e}")
        await update.message.reply_text(f"⚠️ An error occurred while generating the plan: {str(e)}")

# 3. MAIN RUNNER
def main():
    # Start web server thread to satisfy Render's port scanner
    threading.Thread(target=run_health_check, daemon=True).start()

    # Get Bot Token from Render Environment Variables
    token = os.getenv("BOT_TOKEN")
    if not token:
        logging.error("BOT_TOKEN environment variable is missing!")
        return

    # Initialize Telegram Application
    app = ApplicationBuilder().token(token).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate", generate_pdf_command))

    logging.info("Starting Telegram Bot...")
    app.run_polling()

if __name__ == "__main__":
    main()
