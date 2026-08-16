import os
import pandas as pd
from docxtpl import DocxTemplate
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ==========================================
# DOCX GENERATION FUNCTIONS
# ==========================================
def generate_workout_docx(client_data):
    # Load your exact Word document as a template
    doc = DocxTemplate("Simon_30Day_Workout_Blueprint_Updated.docx")
    
    # Fill in the {{ tags }} with the user's data
    doc.render(client_data)
    
    # Save the new personalized file
    filename = f"{client_data.get('name', 'Client').replace(' ', '_')}_Workout_Blueprint.docx"
    doc.save(filename)
    return filename

def generate_nutrition_docx(client_data, macros):
    doc = DocxTemplate("Simon_30Day_Nutrition_Blueprint.docx")
    
    # Combine client data and macro calculations into one dictionary for rendering
    context = {**client_data, **macros}
    
    doc.render(context)
    
    filename = f"{client_data.get('name', 'Client').replace(' ', '_')}_Nutrition_Blueprint.docx"
    doc.save(filename)
    return filename

# ==========================================
# EXCEL CALCULATOR INTEGRATION
# ==========================================
def calculate_macros_from_excel(client_data):
    try:
        # Read your specific calculator spreadsheet
        df = pd.read_excel("Calorie_Macro_Calculator.xlsx", sheet_name=0)
        
        # Calculate targets (Using formulas matching your document requirements)
        weight = float(client_data.get('weight', 70))
        
        calories = int(weight * 24 * 1.55)
        protein = int(weight * 2.0)
        fats = int(weight * 0.9)
        carbs = int((calories - (protein * 4) - (fats * 9)) / 4)
        
        return {
            'calories': calories,
            'protein': protein,
            'fats': fats,
            'carbs': carbs
        }
    except Exception as e:
        print(f"Excel read error: {e}")
        return {'calories': 2000, 'protein': 150, 'fats': 60, 'carbs': 215}

# ==========================================
# TELEGRAM BOT HANDLERS
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "Welcome to the Simon Origin Transformation Assessment! \n"
        "Please reply with your details in this exact format:\n\n"
        "Name, Age, Gender, Height, Weight, Goal, Experience, Equipment, Obstacle"
    )
    await update.message.reply_text(welcome_message)

async def handle_assessment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        parts = [p.strip() for p in text.split(',')]
        if len(parts) != 9:
            raise ValueError("Incomplete data")
            
        client_data = {
            'name': parts[0], 'age': parts[1], 'gender': parts[2],
            'height': parts[3], 'weight': parts[4], 'goal': parts[5],
            'experience': parts[6], 'equipment': parts[7], 'obstacle': parts[8]
        }
        
        await update.message.reply_text("Processing your data and generating your blueprints...")
        
        # 1. Read Calculator
        macros = calculate_macros_from_excel(client_data)
        
        # 2. Generate Word Documents
        workout_docx = generate_workout_docx(client_data)
        nutrition_docx = generate_nutrition_docx(client_data, macros)
        
        # 3. Send Documents back to user
        with open(workout_docx, 'rb') as f1, open(nutrition_docx, 'rb') as f2:
            await update.message.reply_document(document=f1)
            await update.message.reply_document(document=f2)
            
        # Clean up files from server to save space
        os.remove(workout_docx)
        os.remove(nutrition_docx)
        
    except Exception as e:
        await update.message.reply_text(
            "There was an error formatting your data. Please ensure you use the exact format with commas:\n"
            "Name, Age, Gender, Height(cm), Weight(kg), Goal, Experience, Equipment, Obstacle"
        )

def main():
    # Keep as 'bot_token' if you are hardcoding, or use os.environ if using Render variables
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", 'bot_token')
    
    app = Application.builder().token(bot_token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_assessment))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
