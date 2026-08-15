import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import datetime
import os

# --- 1. THE MATH & EXCEL ENGINE ---
def calculate_macros(client_data):
    try:
        # Load your actual Excel calculator spreadsheet
        calc_df = pd.read_excel('Calorie_Macro_Calculator.xlsx')
    except Exception as e:
        print(f"Note on Excel file load: {e}")

    # Fallback / dynamic math engine based on client goal and weight
    base_calories = 2000
    goal = client_data.get('goal', 'Fat Loss')
    if "Loss" in goal or "ክብደት" in goal:
        calories = base_calories - 300
    elif "Gain" in goal or "ጡንቻ" in goal:
        calories = base_calories + 300
    else:
        calories = base_calories

    weight = float(client_data.get('weight', 75))

    return {
        "calories": calories,
        "protein": int(weight * 2.0), # ~2.0g/kg body weight
        "carbs": int((calories * 0.4) / 4), 
        "fats": int((calories * 0.3) / 9),
        "water": 3.5
    }

# --- 2. SETUP STYLES & FONTS ---
def get_styles():
    try:
        # Register the Amharic font (must be in the same folder)
        pdfmetrics.registerFont(TTFont('AmharicFont', 'AbyssinicaSIL-Regular.ttf'))
        font_name = 'AmharicFont'
    except Exception as e:
        print(f"Font loading warning: {e}. Falling back to default.")
        font_name = 'Helvetica'

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontName=font_name, fontSize=15, alignment=1, spaceAfter=10)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontName=font_name, fontSize=11, spaceAfter=8)
    return title_style, normal_style, font_name

# --- 3. NUTRITION PDF GENERATOR ---
def generate_nutrition_pdf(client_data, macros):
    title_style, normal_style, font_name = get_styles()
    filename = f"{client_data['name'].replace(' ', '_')}_Nutrition_Plan.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []

    # Headers (Bilingual)
    elements.append(Paragraph("SIMON ORIGIN TRANSFORMATION", title_style))
    elements.append(Paragraph("30-Day Personalized Nutrition Blueprint", title_style))
    elements.append(Paragraph("የ30 ቀን የግል የአመጋገብ ዕቅድ", title_style))
    elements.append(Spacer(1, 10))
    
    # Snapshot Table matching template structure
    data = [
        ["Client Snapshot / የደንበኛ መረጃ", ""],
        ["Full Name / ሙሉ ስም", client_data.get('name', '')],
        ["Gender / ጾታ", client_data.get('gender', '')],
        ["Age / እድሜ", str(client_data.get('age', ''))],
        ["Primary Goal / ዋና ግብ", client_data.get('goal', '')],
        ["Daily Calories / የዕለት ካሎሪ", f"{macros['calories']} kcal / day"],
        ["Protein Target / የፕሮቲን ግብ", f"{macros['protein']} g"],
        ["Carbs Target / የካርቦሃይድሬት ግብ", f"{macros['carbs']} g"],
        ["Fat Target / የስብ ግብ", f"{macros['fats']} g"],
        ["Daily Fluid / የዕለት ውሃ ግብ", f"{macros['water']} Liters"]
    ]
    
    table = Table(data, colWidths=[200, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("Questions about this plan? Reach Simon directly at @s_simon_19.", normal_style))
    elements.append(Paragraph("ስለዚህ ዕቅድ ጥያቄ ካለዎት በቀጥታ @s_simon_19 ያግኙን።", normal_style))

    doc.build(elements)
    print(f"Generated Nutrition PDF: {filename}")
    return filename

# --- 4. WORKOUT PDF GENERATOR ---
def generate_workout_pdf(client_data):
    title_style, normal_style, font_name = get_styles()
    filename = f"{client_data['name'].replace(' ', '_')}_Workout_Plan.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []

    # Headers (Bilingual)
    elements.append(Paragraph("SIMON ORIGIN TRANSFORMATION", title_style))
    elements.append(Paragraph("30-Day Personalized Workout Blueprint", title_style))
    elements.append(Paragraph("የ30 ቀን የግል የልምምድ ዕቅድ", title_style))
    elements.append(Spacer(1, 10))

    experience = client_data.get('experience', 'Beginner')
    equipment = client_data.get('equipment', 'Home')

    # Training Snapshot Table matching template structure
    data = [
        ["Training Targets & Structure / የልምምድ ዒላማ እና ስርዓት", ""],
        ["Experience / የልምምድ ልምድ", experience],
        ["Equipment Available / ያለ መሳሪያ", equipment],
        ["Training Frequency / ድግግሞሽ", "4-5 training days / week"],
        ["Session Length / የክፍለ ጊዜ ርዝመት", "45-65 minutes"],
        ["Primary Method / ዋና ዘዴ", "Progressive overload + controlled technique"]
    ]
    
    table = Table(data, colWidths=[200, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("Questions about this plan? Reach Simon directly at @s_simon_19.", normal_style))
    elements.append(Paragraph("ስለዚህ ዕቅድ ጥያቄ ካለዎት በቀጥታ @s_simon_19 ያግኙን።", normal_style))

    doc.build(elements)
    print(f"Generated Workout PDF: {filename}")
    return filename
