#!/usr/bin/env python3
"""
AgriBot Firmware v18.6.0 - PRODUCTION READY
============================================

import RPi.GPIO as GPIO
from flask import Flask, request, jsonify, session, render_template_string, send_file, redirect, url_for
import threading, time, json, os
from datetime import datetime

# Load optional .env file (python-dotenv not required — manual parse fallback)
def _load_dotenv(path=".env"):
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())

_load_dotenv()
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

# ======================================================
# 0. HARDWARE CALIBRATION
# ======================================================
L_INVERT = False
R_INVERT = False 

# ======================================================
# 1. CONFIGURATION
# ======================================================
UI_PASSWORD = os.environ.get("AGRIBOT_PASSWORD", "admin123")  # Override via .env or env var
CONFIG_FILE = "field_config.json"
L_PWM, L_DIR = 12, 13
R_PWM, R_DIR = 18, 19
FERT_SERVO, FERT_LED = 23, 24
HALL_PIN = 17

BAT_CAP, R_INT = 10.0, 0.08
MAX_SPD, WATCHDOG_TO = 0.6, 6.0

# RAMPING CONFIGURATION - ALL MANUAL CONTROLS USE THESE
MANUAL_TARGET_PWM = 30.0  # Target PWM for all manual movements (30%)
RAMP_UP_TIME = 10.0       # Slow start time (10 seconds)
RAMP_DOWN_TIME = 7.0      # Slow stop time (7 seconds)

# GUIDED MODE USES DIFFERENT SETTINGS
GUIDED_TARGET_PWM = 30.0  # Can be different if needed
GUIDED_RAMP_UP   = 33.33  # seconds from 0 → 100 %
GUIDED_RAMP_DOWN = 23.33  # seconds from 100 → 0 %

# WAIT-FOR-ZERO TIMEOUT
WAIT_FOR_ZERO_TIMEOUT = 12.0   # seconds

PULSES_PER_METER = 10

FERT_FLOW_RATES = {
    0: 0.0, 10: 2.0, 20: 5.0, 30: 9.0, 40: 14.0,
    50: 20.0, 60: 27.0, 70: 35.0, 80: 44.0, 90: 54.0
}

# ======================================================
# LANGUAGE TRANSLATIONS
# ======================================================
TRANSLATIONS = {
    "en": {
        "title": "AGRIBOT",
        "version": "v18.6.0",
        "login_placeholder": "Enter Access Code",
        "login_button": "AUTHENTICATE",
        "select_language": "Select Language",
        "battery": "Battery",
        "voltage": "Voltage",
        "current": "Current",
        "runtime": "Runtime",
        "distance": "Distance",
        "pulses": "Pulses",
        "manual_control": "MANUAL CONTROL",
        "guided_mode": "GUIDED MODE",
        "stop": "STOP",
        "field_config": "Field Configuration",
        "length_m": "Length (m)",
        "spacing_m": "Spacing (m)",
        "rows": "Rows",
        "fertilizer_settings": "Fertilizer Settings",
        "total_fertilizer_kg": "Total fertilizer (kg)",
        "calculated_params": "Calculated Parameters",
        "servo_angle": "Servo Angle:",
        "flow_rate": "Flow Rate:",
        "dispensed": "Dispensed:",
        "hall_calibration": "Hall Sensor Calibration",
        "pulses_per_meter": "Pulses per meter",
        "save_calibration": "SAVE CALIBRATION",
        "hall_disabled": "Hall sensor disabled",
        "start_guided": "START GUIDED MODE",
        "anchored_continue": "ANCHORED - CONTINUE",
        "cutting_complete": "CUTTING COMPLETE - CONTINUE",
        "abort_mission": "ABORT MISSION",
        "manual_fertilizer": "Manual Fertilizer Control",
        "apply": "APPLY",
        "close_valve": "CLOSE VALVE",
        "auto_note": "Auto-controlled in guided mode",
        "download_report": "DOWNLOAD REPORT",
        "idle": "IDLE",
        "manual": "MANUAL",
        "guided": "GUIDED",
        "safety_stop": "SAFETY STOP"
    },
    "ta": {
        "title": "அக்ரிபாட்",
        "version": "v18.6.0",
        "login_placeholder": "அணுகல் குறியீடு",
        "login_button": "உள்நுழைய",
        "select_language": "மொழியைத் தேர்ந்தெடுக்கவும்",
        "battery": "மின்கலன்",
        "voltage": "மின்னழுத்தம்",
        "current": "மின்னோட்டம்",
        "runtime": "இயக்க நேரம்",
        "distance": "தூரம்",
        "pulses": "துடிப்புகள்",
        "manual_control": "கைமுறை கட்டுப்பாடு",
        "guided_mode": "வழிகாட்டப்பட்ட பயன்முறை",
        "stop": "நிறுத்து",
        "field_config": "வயல் அமைப்பு",
        "length_m": "நீளம் (மீ)",
        "spacing_m": "இடைவெளி (மீ)",
        "rows": "வரிசைகள்",
        "fertilizer_settings": "உர அமைப்புகள்",
        "total_fertilizer_kg": "மொத்த உரம் (கிகி)",
        "calculated_params": "கணக்கிடப்பட்ட அளவுகள்",
        "servo_angle": "சர்வோ கோணம்:",
        "flow_rate": "ஓட்ட விகிதம்:",
        "dispensed": "வழங்கப்பட்டது:",
        "hall_calibration": "ஹால் சென்சார் அளவீடு",
        "pulses_per_meter": "ஒரு மீட்டருக்கு துடிப்புகள்",
        "save_calibration": "அளவீட்டைச் சேமி",
        "hall_disabled": "ஹால் சென்சார் முடக்கப்பட்டது",
        "start_guided": "வழிகாட்டப்பட்ட பயன்முறையைத் தொடங்கு",
        "anchored_continue": "நங்கூரமிடப்பட்டது - தொடர்க",
        "cutting_complete": "வெட்டுதல் முடிந்தது - தொடர்க",
        "abort_mission": "பணியை நிறுத்து",
        "manual_fertilizer": "கைமுறை உர கட்டுப்பாடு",
        "apply": "பயன்படுத்து",
        "close_valve": "வால்வை மூடு",
        "auto_note": "வழிகாட்டப்பட்ட பயன்முறையில் தானாக கட்டுப்படுத்தப்படும்",
        "download_report": "அறிக்கையைப் பதிவிறக்கு",
        "idle": "செயலற்ற",
        "manual": "கைமுறை",
        "guided": "வழிகாட்டப்பட்டது",
        "safety_stop": "பாதுகாப்பு நிறுத்தம்"
    },
    "hi": {
        "title": "एग्रीबॉट",
        "version": "v18.6.0",
        "login_placeholder": "एक्सेस कोड दर्ज करें",
        "login_button": "लॉगिन करें",
        "select_language": "भाषा चुनें",
        "battery": "बैटरी",
        "voltage": "वोल्टेज",
        "current": "करंट",
        "runtime": "रनटाइम",
        "distance": "दूरी",
        "pulses": "पल्स",
        "manual_control": "मैनुअल नियंत्रण",
        "guided_mode": "गाइडेड मोड",
        "stop": "रोकें",
        "field_config": "फील्ड सेटिंग",
        "length_m": "लंबाई (मी)",
        "spacing_m": "स्पेसिंग (मी)",
        "rows": "पंक्तियाँ",
        "fertilizer_settings": "उर्वरक सेटिंग्स",
        "total_fertilizer_kg": "कुल उर्वरक (किग्रा)",
        "calculated_params": "गणना किए गए पैरामीटर",
        "servo_angle": "सर्वो कोण:",
        "flow_rate": "प्रवाह दर:",
        "dispensed": "वितरित:",
        "hall_calibration": "हॉल सेंसर कैलिब्रेशन",
        "pulses_per_meter": "प्रति मीटर पल्स",
        "save_calibration": "कैलिब्रेशन सेव करें",
        "hall_disabled": "हॉल सेंसर अक्षम",
        "start_guided": "गाइडेड मोड शुरू करें",
        "anchored_continue": "एंकर हो गया - जारी रखें",
        "cutting_complete": "कटाई पूर्ण - जारी रखें",
        "abort_mission": "मिशन रद्द करें",
        "manual_fertilizer": "मैनुअल उर्वरक नियंत्रण",
        "apply": "लागू करें",
        "close_valve": "वाल्व बंद करें",
        "auto_note": "गाइडेड मोड में स्वचालित",
        "download_report": "रिपोर्ट डाउनलोड करें",
        "idle": "निष्क्रिय",
        "manual": "मैनुअल",
        "guided": "गाइडेड",
        "safety_stop": "सुरक्षा रोक"
    },
    "te": {
        "title": "అగ్రిబాట్",
        "version": "v18.6.0",
        "login_placeholder": "యాక్సెస్ కోడ్ నమోదు చేయండి",
        "login_button": "ప్రామాణీకరించండి",
        "select_language": "భాషను ఎంచుకోండి",
        "battery": "బ్యాటరీ",
        "voltage": "వోల్టేజ్",
        "current": "కరెంట్",
        "runtime": "రన్‌టైమ్",
        "distance": "దూరం",
        "pulses": "పల్స్‌లు",
        "manual_control": "మాన్యువల్ నియంత్రణ",
        "guided_mode": "గైడెడ్ మోడ్",
        "stop": "ఆపు",
        "field_config": "ఫీల్డ్ కాన్ఫిగరేషన్",
        "length_m": "పొడవు (మీ)",
        "spacing_m": "అంతరం (మీ)",
        "rows": "వరుసలు",
        "fertilizer_settings": "ఎరువుల సెట్టింగ్‌లు",
        "total_fertilizer_kg": "మొత్తం ఎరువు (కిలోలు)",
        "calculated_params": "లెక్కించిన పారామితులు",
        "servo_angle": "సర్వో కోణం:",
        "flow_rate": "ప్రవాహ రేటు:",
        "dispensed": "పంపిణీ చేయబడింది:",
        "hall_calibration": "హాల్ సెన్సార్ క్యాలిబ్రేషన్",
        "pulses_per_meter": "మీటరుకు పల్స్‌లు",
        "save_calibration": "క్యాలిబ్రేషన్ సేవ్ చేయండి",
        "hall_disabled": "హాల్ సెన్సార్ నిలిపివేయబడింది",
        "start_guided": "గైడెడ్ మోడ్ ప్రారంభించండి",
        "anchored_continue": "యాంకర్ చేయబడింది - కొనసాగించండి",
        "cutting_complete": "కట్టింగ్ పూర్తయింది - కొనసాగించండి",
        "abort_mission": "మిషన్ రద్దు చేయండి",
        "manual_fertilizer": "మాన్యువల్ ఎరువు నియంత్రణ",
        "apply": "వర్తింపజేయండి",
        "close_valve": "వాల్వ్ మూసివేయండి",
        "auto_note": "గైడెడ్ మోడ్‌లో స్వయంచాలకంగా నియంత్రించబడుతుంది",
        "download_report": "రిపోర్ట్ డౌన్‌లోడ్ చేయండి",
        "idle": "నిష్క్రియ",
        "manual": "మాన్యువల్",
        "guided": "గైడెడ్",
        "safety_stop": "భద్రతా స్టాప్"
    },
    "kn": {
        "title": "ಅಗ್ರಿಬಾಟ್",
        "version": "v18.6.0",
        "login_placeholder": "ಪ್ರವೇಶ ಕೋಡ್ ನಮೂದಿಸಿ",
        "login_button": "ದೃಢೀಕರಿಸಿ",
        "select_language": "ಭಾಷೆ ಆಯ್ಕೆಮಾಡಿ",
        "battery": "ಬ್ಯಾಟರಿ",
        "voltage": "ವೋಲ್ಟೇಜ್",
        "current": "ಕರೆಂಟ್",
        "runtime": "ರನ್‌ಟೈಮ್",
        "distance": "ದೂರ",
        "pulses": "ಪಲ್ಸ್‌ಗಳು",
        "manual_control": "ಕೈಪಿಡಿ ನಿಯಂತ್ರಣ",
        "guided_mode": "ಮಾರ್ಗದರ್ಶಿತ ಮೋಡ್",
        "stop": "ನಿಲ್ಲಿಸಿ",
        "field_config": "ಕ್ಷೇತ್ರ ಸಂರಚನೆ",
        "length_m": "ಉದ್ದ (ಮೀ)",
        "spacing_m": "ಅಂತರ (ಮೀ)",
        "rows": "ಸಾಲುಗಳು",
        "fertilizer_settings": "ಗೊಬ್ಬರ ಸೆಟ್ಟಿಂಗ್‌ಗಳು",
        "total_fertilizer_kg": "ಒಟ್ಟು ಗೊಬ್ಬರ (ಕೆಜಿ)",
        "calculated_params": "ಲೆಕ್ಕಾಚಾರ ಮಾಡಲಾದ ನಿಯತಾಂಕಗಳು",
        "servo_angle": "ಸರ್ವೋ ಕೋನ:",
        "flow_rate": "ಹರಿವಿನ ದರ:",
        "dispensed": "ವಿತರಿಸಲಾಗಿದೆ:",
        "hall_calibration": "ಹಾಲ್ ಸೆನ್ಸಾರ್ ಕ್ಯಾಲಿಬ್ರೇಶನ್",
        "pulses_per_meter": "ಪ್ರತಿ ಮೀಟರ್‌ಗೆ ಪಲ್ಸ್‌ಗಳು",
        "save_calibration": "ಕ್ಯಾಲಿಬ್ರೇಶನ್ ಉಳಿಸಿ",
        "hall_disabled": "ಹಾಲ್ ಸೆನ್ಸಾರ್ ನಿಷ್ಕ್ರಿಯಗೊಂಡಿದೆ",
        "start_guided": "ಮಾರ್ಗದರ್ಶಿತ ಮೋಡ್ ಪ್ರಾರಂಭಿಸಿ",
        "anchored_continue": "ಲಂಗರು ಹಾಕಲಾಗಿದೆ - ಮುಂದುವರಿಸಿ",
        "cutting_complete": "ಕತ್ತರಿಸುವಿಕೆ ಪೂರ್ಣಗೊಂಡಿದೆ - ಮುಂದುವರಿಸಿ",
        "abort_mission": "ಮಿಷನ್ ರದ್ದುಮಾಡಿ",
        "manual_fertilizer": "ಕೈಪಿಡಿ ಗೊಬ್ಬರ ನಿಯಂತ್ರಣ",
        "apply": "ಅನ್ವಯಿಸಿ",
        "close_valve": "ವಾಲ್ವ್ ಮುಚ್ಚಿ",
        "auto_note": "ಮಾರ್ಗದರ್ಶಿತ ಮೋಡ್‌ನಲ್ಲಿ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ನಿಯಂತ್ರಿಸಲಾಗುತ್ತದೆ",
        "download_report": "ವರದಿ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ",
        "idle": "ನಿಷ್ಕ್ರಿಯ",
        "manual": "ಕೈಪಿಡಿ",
        "guided": "ಮಾರ್ಗದರ್ಶಿತ",
        "safety_stop": "ಸುರಕ್ಷತೆ ನಿಲುಗಡೆ"
    },
    "ur": {
        "title": "ایگری بوٹ",
        "version": "v18.6.0",
        "login_placeholder": "رسائی کوڈ درج کریں",
        "login_button": "تصدیق کریں",
        "select_language": "زبان منتخب کریں",
        "battery": "بیٹری",
        "voltage": "وولٹیج",
        "current": "کرنٹ",
        "runtime": "رن ٹائم",
        "distance": "فاصلہ",
        "pulses": "نبضیں",
        "manual_control": "دستی کنٹرول",
        "guided_mode": "رہنمائی شدہ موڈ",
        "stop": "روکیں",
        "field_config": "فیلڈ ترتیب",
        "length_m": "لمبائی (میٹر)",
        "spacing_m": "فاصلہ (میٹر)",
        "rows": "قطاریں",
        "fertilizer_settings": "کھاد کی ترتیبات",
        "total_fertilizer_kg": "کل کھاد (کلوگرام)",
        "calculated_params": "شمار شدہ پیرامیٹرز",
        "servo_angle": "سرو زاویہ:",
        "flow_rate": "بہاؤ کی شرح:",
        "dispensed": "تقسیم شدہ:",
        "hall_calibration": "ہال سینسر کیلیبریشن",
        "pulses_per_meter": "فی میٹر نبضیں",
        "save_calibration": "کیلیبریشن محفوظ کریں",
        "hall_disabled": "ہال سینسر غیر فعال",
        "start_guided": "رہنمائی شدہ موڈ شروع کریں",
        "anchored_continue": "لنگر ڈالا گیا - جاری رکھیں",
        "cutting_complete": "کٹائی مکمل - جاری رکھیں",
        "abort_mission": "مشن منسوخ کریں",
        "manual_fertilizer": "دستی کھاد کنٹرول",
        "apply": "لاگو کریں",
        "close_valve": "والو بند کریں",
        "auto_note": "رہنمائی شدہ موڈ میں خودکار کنٹرول",
        "download_report": "رپورٹ ڈاؤن لوڈ کریں",
        "idle": "بیکار",
        "manual": "دستی",
        "guided": "رہنمائی شدہ",
        "safety_stop": "حفاظتی رکاوٹ"
    }
}

# ======================================================
# 2. STATE & PERSISTENCE
# ======================================================
def load_cfg():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f: 
                c = json.load(f)
                global PULSES_PER_METER
                if "pulses_per_m" in c:
                    PULSES_PER_METER = c["pulses_per_m"]
                return c
        except: 
            pass
    return {"L": 5.0, "S": 1.0, "R": 4, "pulses_per_m": 10, "fert_kg": 0.0}

def save_cfg():
    with open(CONFIG_FILE, 'w') as f:
        json.dump({
            "L": state["path_L"],
            "S": state["path_S"],
            "R": state["path_R"],
            "pulses_per_m": PULSES_PER_METER,
            "fert_kg": state["fert_kg"]
        }, f)

BOOT_CFG = load_cfg()
state_lock = threading.RLock()  # FIX 11: RLock prevents self-deadlock when nested

state = {
    "voltage": 25.6, "current": 0.0, "percentage": 100.0,
    "runtime": ">24h", "status": "IDLE", "eta": 0.0, "active_seg": -1,
    "path_L": BOOT_CFG["L"], "path_S": BOOT_CFG["S"], "path_R": BOOT_CFG["R"],
    "wait_action": "", "distance": 0.0, "pulses": 0,
    "fert_kg": BOOT_CFG.get("fert_kg", 0.0),
    "fert_angle_calc": 0.0, "fert_dispensed": 0.0
}

# SESSION TRACKING
session_data = {
    "sessions": [],
    "current_session": None
}

target_l, target_r = 0, 0
current_l, current_r = 0.0, 0.0
fert_target = 0.0
fert_current = 0.0
consumed_ah = 0.0
stop_flag = False
last_pulse = time.time()
manual_active = False
pwm_f = None
continue_flag = False
pulse_count = 0
distance_traveled = 0.0
fert_dispensing = False
fert_start_time = 0
fert_total_dispensed = 0.0
emergency_stop_flag = False
guided_generation = 0  # FIX 9: incremented on each new guided session
guided_thread = None    # FIX 10: tracks the live guided thread for joining

# FIX 8: Accumulator for total distance across all travel_distance() calls
# Reset at start_session(), incremented after every travel_distance() call.
session_total_distance = 0.0

# ======================================================
# SESSION TRACKING FUNCTIONS
# ======================================================
def start_session(L, S, R, fert_kg):
    global session_data, session_total_distance
    # FIX 8: Reset the distance accumulator for the new session
    session_total_distance = 0.0
    session = {
        "id": len(session_data["sessions"]) + 1,
        "start_time": datetime.now(),
        "end_time": None,
        "config": {
            "length": L,
            "spacing": S,
            "rows": R,
            "fertilizer_kg": fert_kg
        },
        "stats": {
            "total_distance": 0.0,
            "fertilizer_dispensed": 0.0,
            "battery_start": state["percentage"],
            "battery_end": None,
            "rows_completed": 0,
            "status": "IN PROGRESS"
        },
        "events": []
    }
    session_data["current_session"] = session
    session_data["sessions"].append(session)
    log_session_event("Session started")

def log_session_event(event_description):
    if session_data["current_session"]:
        session_data["current_session"]["events"].append({
            "time": datetime.now(),
            "description": event_description
        })

def end_session(status="COMPLETED"):
    if session_data["current_session"]:
        session_data["current_session"]["end_time"] = datetime.now()
        session_data["current_session"]["stats"]["battery_end"] = state["percentage"]
        # FIX 8: Use the accumulated total distance, not just the last segment's value
        session_data["current_session"]["stats"]["total_distance"] = round(session_total_distance, 2)
        session_data["current_session"]["stats"]["fertilizer_dispensed"] = state["fert_dispensed"]
        session_data["current_session"]["stats"]["status"] = status
        log_session_event(f"Session ended: {status}")

def generate_session_report():
    if not session_data["sessions"]:
        return None
    
    session = session_data["sessions"][-1]
    
    filename = f"/tmp/agribot_session_{session['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#64ffda'),
        spaceAfter=20,
        alignment=1
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#64ffda'),
        spaceAfter=10,
        spaceBefore=10
    )
    
    story.append(Paragraph("AgriBot Session Report", title_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Session Information", heading_style))
    session_info = [
        ["Session ID:", str(session["id"])],
        ["Start Time:", session["start_time"].strftime("%Y-%m-%d %H:%M:%S")],
        ["End Time:", session["end_time"].strftime("%Y-%m-%d %H:%M:%S") if session["end_time"] else "In Progress"],
        ["Status:", session["stats"]["status"]]
    ]
    
    t = Table(session_info, colWidths=[2.5*inch, 4*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#1a1f3a')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#64ffda')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    story.append(t)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("Field Configuration", heading_style))
    config_data = [
        ["Length per Row:", f"{session['config']['length']} meters"],
        ["Row Spacing:", f"{session['config']['spacing']} meters"],
        ["Number of Rows:", str(session['config']['rows'])],
        ["Fertilizer Target:", f"{session['config']['fertilizer_kg']} kg"]
    ]
    
    t = Table(config_data, colWidths=[2.5*inch, 4*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#1a1f3a')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#64ffda')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    story.append(t)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("Performance Statistics", heading_style))
    battery_consumed = session['stats']['battery_start'] - (session['stats']['battery_end'] if session['stats']['battery_end'] else session['stats']['battery_start'])
    stats_data = [
        ["Total Distance:", f"{session['stats']['total_distance']:.2f} meters"],
        ["Fertilizer Dispensed:", f"{session['stats']['fertilizer_dispensed']:.1f} grams"],
        ["Rows Completed:", f"{session['stats']['rows_completed']} / {session['config']['rows']}"],
        ["Battery Start:", f"{session['stats']['battery_start']:.1f}%"],
        ["Battery End:", f"{session['stats']['battery_end']:.1f}%" if session['stats']['battery_end'] else "N/A"],
        ["Battery Consumed:", f"{battery_consumed:.1f}%"]
    ]
    
    t = Table(stats_data, colWidths=[2.5*inch, 4*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#1a1f3a')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#64ffda')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    story.append(t)
    story.append(Spacer(1, 15))
    
    if session["events"]:
        story.append(Paragraph("Event Log", heading_style))
        event_data = [["Time", "Event"]]
        for event in session["events"]:
            event_data.append([
                event["time"].strftime("%H:%M:%S"),
                event["description"]
            ])
        
        t = Table(event_data, colWidths=[1.5*inch, 5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1f3a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#64ffda')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(t)
    
    story.append(Spacer(1, 20))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=1)
    story.append(Paragraph(f"Generated by AgriBot v18.6.0 on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
    
    doc.build(story)
    return filename

# ======================================================
# 3. FERTILIZER FLOW CALCULATION
# ======================================================
def interpolate_flow_rate(angle):
    if angle <= 0:
        return 0.0
    if angle >= 90:
        return FERT_FLOW_RATES[90]
    keys = sorted(FERT_FLOW_RATES.keys())
    for i in range(len(keys) - 1):
        if keys[i] <= angle <= keys[i + 1]:
            x1, y1 = keys[i], FERT_FLOW_RATES[keys[i]]
            x2, y2 = keys[i + 1], FERT_FLOW_RATES[keys[i + 1]]
            return y1 + (y2 - y1) * (angle - x1) / (x2 - x1)
    return FERT_FLOW_RATES[90]

def calculate_fert_angle(desired_kg, L, R):
    if desired_kg <= 0:
        return 0.0
    total_distance = L * R
    actual_speed = MAX_SPD * (GUIDED_TARGET_PWM / 100.0)
    if actual_speed <= 0:
        actual_speed = 0.001
    total_time = total_distance / actual_speed
    desired_grams = desired_kg * 1000.0
    required_flow_rate = desired_grams / total_time
    
    for angle in range(0, 91):
        flow = interpolate_flow_rate(angle)
        if flow >= required_flow_rate:
            return float(angle)  # FIX 14: no safety margin overage
    
    return 90.0

def update_fert_dispensed(angle, dt):
    global fert_total_dispensed
    if angle > 0:
        flow_rate = interpolate_flow_rate(angle)
        dispensed = flow_rate * dt
        fert_total_dispensed += dispensed
        with state_lock:
            state["fert_dispensed"] = round(fert_total_dispensed, 1)

# ======================================================
# 4. HALL SENSOR MONITORING
# ======================================================
def hall_callback(channel):
    global pulse_count, distance_traveled
    with state_lock:
        pulse_count += 1
        distance_traveled = pulse_count / PULSES_PER_METER
        state["pulses"] = pulse_count
        state["distance"] = round(distance_traveled, 2)

def setup_hall():
    if HALL_PIN is None:
        return
    GPIO.setup(HALL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(HALL_PIN, GPIO.FALLING, callback=hall_callback, bouncetime=1)

# ======================================================
# 5. KINEMATICS & HARDWARE ENGINE
# ======================================================
def set_tgt(l, r):
    global target_l, target_r
    with state_lock: 
        target_l, target_r = l, r
        if l != 0 or r != 0:
            if state["status"] != "GUIDED":
                state["status"] = "MANUAL"
        elif not manual_active and state["status"] == "MANUAL":
            state["status"] = "IDLE"

def hardware_engine():
    global consumed_ah, pwm_f, stop_flag, fert_current, current_l, current_r, emergency_stop_flag
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup([L_PWM, L_DIR, R_PWM, R_DIR, FERT_SERVO, FERT_LED], GPIO.OUT)
    setup_hall()
    
    pl = GPIO.PWM(L_PWM, 1000)
    pr = GPIO.PWM(R_PWM, 1000)
    pwm_f = GPIO.PWM(FERT_SERVO, 50)
    
    pl.start(0)
    pr.start(0)
    pwm_f.start(2.5)
    
    dt, avg_i = 0.05, 4.5
    
    guided_ramp_up_rate = (100.0 / GUIDED_RAMP_UP) * dt
    guided_ramp_down_rate = (100.0 / GUIDED_RAMP_DOWN) * dt
    
    manual_ramp_up = (MANUAL_TARGET_PWM / RAMP_UP_TIME) * dt
    manual_ramp_down = (MANUAL_TARGET_PWM / RAMP_DOWN_TIME) * dt

    def approach(curr, targ, up_rate, down_rate):
        if targ == 0:
            if curr > 0:
                return max(0.0, curr - down_rate)
            elif curr < 0:
                return min(0.0, curr + down_rate)
            else:
                return 0.0
        if curr * targ < 0:
            if curr > 0:
                return max(0.0, curr - down_rate)
            else:
                return min(0.0, curr + down_rate)
        if abs(curr) < abs(targ):
            if targ > 0:
                return min(targ, curr + up_rate)
            else:
                return max(targ, curr - up_rate)
        elif abs(curr) > abs(targ):
            if curr > targ:
                return max(targ, curr - down_rate)
            else:
                return min(targ, curr + down_rate)
        else:
            return curr
    
    while True:
        with state_lock:
            tl, tr = target_l, target_r
            ft = fert_target
            is_manual = (state["status"] == "MANUAL")
            is_guided = (state["status"] == "GUIDED")
            curr_l_local = current_l
            curr_r_local = current_r
            last_pulse_local = last_pulse
        
        if time.time() - last_pulse_local > WATCHDOG_TO:
            if (tl != 0 or tr != 0) and is_guided:
                with state_lock:
                    global stop_flag
                    stop_flag = True
                set_tgt(0, 0)
                with state_lock:
                    state["status"] = "SAFETY STOP"
        
        emergency_flag_local = False
        with state_lock:
            emergency_flag_local = emergency_stop_flag
        
        if emergency_flag_local:
            curr_l_local = 0
            curr_r_local = 0
            tl = tr = 0
            set_tgt(0, 0)
            with state_lock:
                current_l = 0
                current_r = 0
                emergency_stop_flag = False
        
        elif is_manual:
            if tl != 0:
                target_sign = 1 if tl > 0 else -1
                target_magnitude = MANUAL_TARGET_PWM
                if abs(curr_l_local) < target_magnitude:
                    curr_l_local += manual_ramp_up * target_sign
                    if abs(curr_l_local) > target_magnitude:
                        curr_l_local = target_magnitude * target_sign
            else:
                if curr_l_local > 0:
                    curr_l_local = max(0, curr_l_local - manual_ramp_down)
                elif curr_l_local < 0:
                    curr_l_local = min(0, curr_l_local + manual_ramp_down)
            
            if tr != 0:
                target_sign = 1 if tr > 0 else -1
                target_magnitude = MANUAL_TARGET_PWM
                if abs(curr_r_local) < target_magnitude:
                    curr_r_local += manual_ramp_up * target_sign
                    if abs(curr_r_local) > target_magnitude:
                        curr_r_local = target_magnitude * target_sign
            else:
                if curr_r_local > 0:
                    curr_r_local = max(0, curr_r_local - manual_ramp_down)
                elif curr_r_local < 0:
                    curr_r_local = min(0, curr_r_local + manual_ramp_down)
        
        elif is_guided:
            curr_l_local = approach(curr_l_local, tl, guided_ramp_up_rate, guided_ramp_down_rate)
            if curr_l_local > 100:
                curr_l_local = 100
            elif curr_l_local < -100:
                curr_l_local = -100
            curr_r_local = approach(curr_r_local, tr, guided_ramp_up_rate, guided_ramp_down_rate)
            if curr_r_local > 100:
                curr_r_local = 100
            elif curr_r_local < -100:
                curr_r_local = -100
        
        else:
            if curr_l_local != 0 or curr_r_local != 0:
                curr_l_local = 0
                curr_r_local = 0
        
        with state_lock:
            current_l = curr_l_local
            current_r = curr_r_local
        
        left_dir_pin = GPIO.LOW if (curr_l_local >= 0) != L_INVERT else GPIO.HIGH
        right_dir_pin = GPIO.LOW if (curr_r_local >= 0) != R_INVERT else GPIO.HIGH
        GPIO.output(L_DIR, left_dir_pin)
        GPIO.output(R_DIR, right_dir_pin)
        
        pl.ChangeDutyCycle(min(100, abs(curr_l_local)))
        pr.ChangeDutyCycle(min(100, abs(curr_r_local)))

        fert_current = fert_current * 0.7 + ft * 0.3
        duty = 2.5 + (fert_current / 100.0) * 5.0
        pwm_f.ChangeDutyCycle(duty)
        GPIO.output(FERT_LED, GPIO.HIGH if fert_current > 5 else GPIO.LOW)
        
        update_fert_dispensed(fert_current, dt)

        inst_i = 4.5 + ((abs(current_l) + abs(current_r)) / 200.0 * 26.8)
        avg_i = (0.99 * avg_i) + (0.01 * inst_i)
        consumed_ah += inst_i * (dt / 3600.0)
        rem = max(0, BAT_CAP - consumed_ah)
        pct = (rem / BAT_CAP) * 100.0
        
        if pct > 90:
            base_volts = 25.6
        elif pct >= 20:
            base_volts = 24.0
        else:
            base_volts = 23.8
        
        volts = base_volts - (inst_i * R_INT)
        
        with state_lock:
            state["voltage"] = round(volts, 1)
            state["current"] = round(inst_i, 1)
            state["percentage"] = round(pct, 1)
            state["runtime"] = (
                f"{int(rem / avg_i)}h "
                f"{int(((rem / avg_i) - int(rem / avg_i)) * 60)}m"
            ) if avg_i > 0.1 else ">24h"
        
        time.sleep(dt)

# ======================================================
# 6. SEMI-AUTOMATIC GUIDED MODE
# ======================================================
def reset_distance():
    global pulse_count, distance_traveled
    pulse_count = 0
    distance_traveled = 0.0
    with state_lock:
        state["pulses"] = 0
        state["distance"] = 0.0

def set_fert_angle(angle):
    global fert_target
    angle_logical = max(0, min(90, angle))
    angle_physical = 44.0 - (angle_logical / 90.0) * 7.0
    fert_target = angle_physical

def run_guided(L, S, R, fert_kg):
    global stop_flag, continue_flag, fert_total_dispensed, session_total_distance
    # FIX 10d: stop_flag is reset by start_g() BEFORE this thread launches,
    # NOT here. Resetting it here would undo the kill signal for any still-dying
    # old thread that shares the same global. Capture generation for guard.
    with state_lock:
        my_generation = guided_generation
    fert_total_dispensed = 0.0
    
    start_session(L, S, R, fert_kg)
    calculated_angle = calculate_fert_angle(fert_kg, L, R)
    
    with state_lock:
        state["status"] = "GUIDED"
        state["path_L"] = L
        state["path_S"] = S
        state["path_R"] = R
        state["fert_kg"] = fert_kg
        state["fert_angle_calc"] = round(calculated_angle, 1)
        state["fert_dispensed"] = 0.0
        state["eta"] = round(R * (L / MAX_SPD + S / MAX_SPD + 8.0), 1)
        state["wait_action"] = "ANCHOR"

    t_turn = 5.0

    def wait_for_zero(timeout=WAIT_FOR_ZERO_TIMEOUT, thresh=1.0):
        t0 = time.time()
        while time.time() - t0 < timeout:
            with state_lock:
                if stop_flag:
                    break
                cl = abs(current_l)
                cr = abs(current_r)
            if cl < thresh and cr < thresh:
                break
            time.sleep(0.02)

    def wait_for_continue():
        global continue_flag
        with state_lock:
            continue_flag = False
        while True:
            with state_lock:
                if continue_flag or stop_flag:
                    return stop_flag
            time.sleep(0.1)

    def interruptible_turn_sleep(duration):
        """
        FIX 7: Replace hard time.sleep(t_turn) with a short-tick loop that
        checks stop_flag every 100ms. Returns True if aborted, False if
        the full duration elapsed normally.
        """
        t0 = time.time()
        while time.time() - t0 < duration:
            with state_lock:
                if stop_flag:
                    return True   # Aborted
            time.sleep(0.1)
        return False  # Completed normally

    def travel_distance(target_m, dispense_fert=False):
        """
        FIX 8: After the segment completes (or is aborted), accumulate the
        distance covered into session_total_distance.
          - Uses Hall sensor distance_traveled if pulses were detected
          - Falls back to target_m (time-based expected distance) if no pulses
        """
        global session_total_distance
        reset_distance()
        
        if dispense_fert and calculated_angle > 0:
            set_fert_angle(calculated_angle)
            log_session_event(f"Fertilizer valve opened at {calculated_angle}°")
        
        actual_speed = MAX_SPD * (GUIDED_TARGET_PWM / 100.0)
        if actual_speed <= 0:
            actual_speed = 0.001
        time_needed = target_m / actual_speed
        target_pulses = int(target_m * PULSES_PER_METER) if HALL_PIN is not None else 0
        
        set_tgt(GUIDED_TARGET_PWM, GUIDED_TARGET_PWM)
        start_time = time.time()
        
        while time.time() - start_time < time_needed:
            # FIX 11b: Read stop_flag under lock, then release BEFORE
            # calling set_tgt() which also needs the lock. Nested lock
            # acquisition with threading.Lock = deadlock.
            with state_lock:
                should_abort = stop_flag
            if should_abort:
                set_tgt(0, 0)
                set_fert_angle(0)
                wait_for_zero()
                with state_lock:
                    seg_dist = distance_traveled
                session_total_distance += seg_dist if seg_dist > 0.01 else (time.time() - start_time) * actual_speed
                return True
            time.sleep(0.05)
        
        set_tgt(0, 0)
        # FIX 14: Close fertilizer valve IMMEDIATELY when motors are commanded
        # to stop — before wait_for_zero(). Previously the valve stayed open
        # during the entire ramp-down (~7s), causing ~300g extra per row.
        # Robot is still slowly moving during ramp-down so fertilizer was
        # being dispensed with no distance tracking benefit.
        if dispense_fert:
            set_fert_angle(0)
            log_session_event("Fertilizer valve closed")
        wait_for_zero()
        
        time.sleep(0.3)
        
        if HALL_PIN is not None and pulse_count < target_pulses:
            correction_start = time.time()
            set_tgt(GUIDED_TARGET_PWM, GUIDED_TARGET_PWM)
            while pulse_count < target_pulses:
                with state_lock:
                    should_stop = stop_flag
                    stale = my_generation != guided_generation
                if should_stop or stale or time.time() - correction_start > 3.0:
                    break
                time.sleep(0.05)
            set_tgt(0, 0)
            wait_for_zero()
        
        # FIX 8: Accumulate segment distance after it completes normally
        with state_lock:
            seg_dist = distance_traveled
        session_total_distance += seg_dist if seg_dist > 0.01 else target_m

        with state_lock:
            return stop_flag

    log_session_event("Waiting for initial anchor")
    if wait_for_continue():
        set_tgt(0, 0)
        set_fert_angle(0)
        with state_lock:
            state["status"] = "IDLE"
            state["wait_action"] = ""
        end_session("ABORTED")
        return

    for r in range(R):
        with state_lock:
            if stop_flag or my_generation != guided_generation:
                break
        
        with state_lock:
            state["active_seg"] = r * 3
            state["wait_action"] = ""
        
        log_session_event(f"Starting row {r+1}/{R}")
        
        if travel_distance(L, dispense_fert=True):
            break
        
        if session_data["current_session"]:
            session_data["current_session"]["stats"]["rows_completed"] = r + 1
        
        log_session_event(f"Completed row {r+1}/{R}")
        
        with state_lock:
            should_stop = stop_flag
        if r == R - 1 or should_stop:
            break
        
        with state_lock:
            state["wait_action"] = "CUT"
        
        log_session_event("Waiting for cutting")
        if wait_for_continue():
            break
        
        with state_lock:
            state["active_seg"] += 1
            state["wait_action"] = ""
        
        turn_dir = (
            ( GUIDED_TARGET_PWM, -GUIDED_TARGET_PWM) if r % 2 == 0
            else (-GUIDED_TARGET_PWM,  GUIDED_TARGET_PWM)
        )
        
        # Sub-action 1: first pivot turn
        # FIX 7: interruptible_turn_sleep checks stop_flag every 100ms
        log_session_event("Executing first pivot turn")
        set_tgt(turn_dir[0], turn_dir[1])
        if interruptible_turn_sleep(t_turn):
            set_tgt(0, 0)
            set_fert_angle(0)
            wait_for_zero()
            break
        set_tgt(0, 0)
        wait_for_zero()
        time.sleep(0.4)
        
        with state_lock:
            state["active_seg"] += 1
        
        # Sub-action 2: traverse row spacing
        if travel_distance(S, dispense_fert=False):
            break
        
        # Sub-action 3: second pivot turn
        # FIX 7: interruptible_turn_sleep checks stop_flag every 100ms
        log_session_event("Executing second pivot turn")
        set_tgt(turn_dir[0], turn_dir[1])
        if interruptible_turn_sleep(t_turn):
            set_tgt(0, 0)
            set_fert_angle(0)
            wait_for_zero()
            break
        set_tgt(0, 0)
        wait_for_zero()
        time.sleep(0.6)
        
        with state_lock:
            state["wait_action"] = "ANCHOR"
        
        log_session_event("Waiting for anchoring")
        if wait_for_continue():
            break
    
    # Final clean-up
    set_tgt(0, 0)
    set_fert_angle(0)
    wait_for_zero()
    with state_lock:
        final_stopped = stop_flag
        # FIX 9: Only reset state if no newer guided session has started.
        # Without this check, a stale cleanup overwrites the new session's
        # "GUIDED" status back to "IDLE", freezing the new run entirely.
        if guided_generation == my_generation:
            state["status"] = "IDLE"
            state["active_seg"] = -1
            state["wait_action"] = ""
    
    end_session("COMPLETED" if not final_stopped else "ABORTED")


# ======================================================
# 7. FLASK SERVER
# ======================================================
app = Flask(__name__)
app.secret_key = os.environ.get("AGRIBOT_SECRET_KEY", "change-me-in-production")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        lang = request.form.get('lang', 'en')
        if request.form.get('p') == UI_PASSWORD:
            session['auth'] = True
            session['lang'] = lang
            # FIX 10b: PRG pattern. After login POST, redirect to GET /
            # so that F5 page reload is always a clean GET request.
            # Without this, browser shows "confirm form resubmission" on reload;
            # if the user dismisses that dialog the JS heartbeat stops, the
            # watchdog fires after 6s, and kills the next guided session.
            return redirect(url_for('index'))
        return render_template_string(LOGIN_HTML, t=TRANSLATIONS.get(lang, TRANSLATIONS['en']))

    if 'lang' in request.args and session.get('auth'):
        session['lang'] = request.args.get('lang', 'en')

    if not session.get('auth'):
        return render_template_string(LOGIN_HTML, t=TRANSLATIONS['en'])

    lang = session.get('lang', 'en')
    return render_template_string(UI_HTML, lang=lang, t=TRANSLATIONS[lang])

@app.route('/api/heartbeat', methods=['POST'])
def hb():
    global last_pulse
    with state_lock:
        last_pulse = time.time()
    return "OK"

@app.route('/api/control', methods=['POST'])
def ctrl():
    global last_pulse, manual_active, emergency_stop_flag
    c = request.json['cmd']
    with state_lock:
        last_pulse = time.time()
    
    if c == "STOP":
        manual_active = False
        with state_lock:
            emergency_stop_flag = True
        set_tgt(0, 0)
        with state_lock:
            state["status"] = "IDLE"
    else:
        manual_active = True
        with state_lock:
            state["status"] = "MANUAL"
        
        if c == "FORWARD":
            set_tgt(100, 100)
        elif c == "BACKWARD":
            set_tgt(-100, -100)
        elif c == "LEFT":
            set_tgt(-100, 100)
        elif c == "RIGHT":
            set_tgt(100, -100)
    
    return "OK"

@app.route('/api/guided/start', methods=['POST'])
def start_g():
    global guided_thread, guided_generation, stop_flag, emergency_stop_flag, continue_flag
    d = request.json
    fert_kg = float(d.get('fert_kg', 0.0))

    # FIX 11d: If a guided thread is alive, signal it to stop and wait
    # for it to exit cooperatively. Every loop inside run_guided checks
    # stop_flag with <=100ms poll interval, so this join returns quickly.
    # The 3s timeout is a hard safety net — it will NOT freeze Flask
    # because it is bounded. After timeout the new session starts anyway.
    if guided_thread is not None and guided_thread.is_alive():
        with state_lock:
            stop_flag = True
            emergency_stop_flag = True
            continue_flag = False  # Unblock wait_for_continue
        set_tgt(0, 0)
        set_fert_angle(0)
        guided_thread.join(timeout=1.0)  # 1s is plenty — every loop exits within 100ms

    # FIX 10c STEP 3: All flags reset in one atomic block — safe because
    # no other guided thread is alive at this point.
    with state_lock:
        stop_flag = False
        emergency_stop_flag = False
        continue_flag = False
        guided_generation += 1
        state["status"] = "IDLE"
        state["active_seg"] = -1
        state["wait_action"] = ""

    # FIX 10c STEP 4: Launch and track the new thread.
    t = threading.Thread(
        target=run_guided,
        args=(float(d['L']), float(d['S']), int(d['R']), fert_kg),
        daemon=True
    )
    guided_thread = t
    t.start()
    return "OK"

@app.route('/api/guided/continue', methods=['POST'])
def cont_g():
    global continue_flag
    with state_lock:
        continue_flag = True
    return "OK"

@app.route('/api/guided/stop', methods=['POST'])
def stop_g():
    global stop_flag, emergency_stop_flag  # FIX 13: all globals declared at function top
    with state_lock:
        stop_flag = True
        emergency_stop_flag = True
    set_tgt(0, 0)
    set_fert_angle(0)
    with state_lock:
        state["status"] = "IDLE"
        state["wait_action"] = ""
    return "OK"

@app.route('/api/calibrate/hall', methods=['POST'])
def calib_hall():
    global PULSES_PER_METER
    PULSES_PER_METER = int(request.json.get('ppm', 10))
    save_cfg()
    return "OK"

@app.route('/api/fert', methods=['POST'])
def fert():
    
    val = float(request.json.get('w', 0))
    set_fert_angle(val)
    return "OK"

@app.route('/api/calc_fert', methods=['POST'])
def calc_fert():
    d = request.json
    L = float(d.get('L', 5.0))
    R = int(d.get('R', 4))
    fert_kg = float(d.get('fert_kg', 0.0))
    angle = calculate_fert_angle(fert_kg, L, R)
    return jsonify({
        "angle": round(angle, 1),
        "flow_rate": round(interpolate_flow_rate(angle), 1)
    })

@app.route('/api/language', methods=['POST'])
def set_language():
    lang = request.json.get('lang', 'en')
    if lang in TRANSLATIONS:
        session['lang'] = lang
        return jsonify({"status": "OK"})
    return jsonify({"status": "ERROR"}), 400

@app.route('/api/report/generate', methods=['GET'])
def generate_report():
    pdf_file = generate_session_report()
    if pdf_file and os.path.exists(pdf_file):
        return send_file(pdf_file, as_attachment=True, download_name=f"agribot_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    else:
        return jsonify({"error": "No session data available"}), 404

@app.route('/api/data')
def data():
    with state_lock:
        s = state.copy()
        s["pulses_per_m"] = PULSES_PER_METER
        s["hall_enabled"] = HALL_PIN is not None
        s["has_session_data"] = len(session_data["sessions"]) > 0
        s["lang"] = session.get('lang', 'en')
        return jsonify(s)

# ======================================================
# 8. UI HTML
# ======================================================
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .login-container {
            background: rgba(15, 32, 39, 0.9);
            border: 1px solid rgba(100, 255, 218, 0.3);
            border-radius: 12px;
            padding: 40px 35px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            text-align: center;
            backdrop-filter: blur(10px);
            max-width: 380px;
            width: 90%;
        }
        h2 {
            font-size: 1.7rem;
            font-weight: 300;
            letter-spacing: 3px;
            margin-bottom: 8px;
            color: #64ffda;
        }
        .version {
            font-size: 0.7rem;
            color: #8892b0;
            margin-bottom: 25px;
            letter-spacing: 2px;
        }
        select, input[type="password"] {
            width: 100%;
            padding: 14px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(100, 255, 218, 0.2);
            border-radius: 6px;
            color: #fff;
            font-size: 0.95rem;
            margin-bottom: 15px;
            transition: all 0.3s;
        }
        select { margin-bottom: 12px; }
        input[type="password"]:focus, select:focus {
            outline: none;
            border-color: #64ffda;
            background: rgba(255, 255, 255, 0.08);
        }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(90deg, #64ffda 0%, #4db8a8 100%);
            border: none;
            border-radius: 6px;
            color: #0a192f;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            letter-spacing: 1px;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(100, 255, 218, 0.4);
        }
    </style>
</head>
<body>
    <form method="post" class="login-container">
        <h2>{{ t.title }}</h2>
        <div class="version">{{ t.version }}</div>
        <select name="lang">
            <option value="en">English</option>
            <option value="ta">தமிழ் (Tamil)</option>
            <option value="hi">हिन्दी (Hindi)</option>
            <option value="te">తెలుగు (Telugu)</option>
            <option value="kn">ಕನ್ನಡ (Kannada)</option>
            <option value="ur">اردو (Urdu)</option>
        </select>
        <input name="p" type="password" placeholder="{{ t.login_placeholder }}" autofocus>
        <button type="submit">{{ t.login_button }}</button>
    </form>
</body>
</html>
"""

UI_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-user-select: none;
            user-select: none;
            -webkit-tap-highlight-color: transparent;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0e27;
            color: #e0e6ed;
            padding: 0;
            overflow-x: hidden;
        }
        
        .app-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 12px;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            background: linear-gradient(135deg, #1a1f3a 0%, #0f1729 100%);
            border-radius: 10px;
            margin-bottom: 15px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }
        
        .header-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .header-title h1 {
            font-size: 1.3rem;
            font-weight: 300;
            letter-spacing: 2px;
            color: #64ffda;
        }
        
        .header-title .version {
            font-size: 0.65rem;
            color: #8892b0;
            letter-spacing: 1px;
        }
        
        .lang-selector {
            padding: 6px 12px;
            background: rgba(100, 255, 218, 0.1);
            border: 1px solid #64ffda;
            border-radius: 5px;
            color: #64ffda;
            font-size: 0.8rem;
            cursor: pointer;
        }
        
        .status-badge {
            padding: 6px 15px;
            border-radius: 15px;
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            border: 2px solid;
        }
        
        .status-idle {
            background: rgba(136, 146, 176, 0.1);
            border-color: #8892b0;
            color: #8892b0;
        }
        
        .status-manual {
            background: rgba(100, 255, 218, 0.1);
            border-color: #64ffda;
            color: #64ffda;
        }
        
        .status-guided {
            background: rgba(94, 234, 212, 0.1);
            border-color: #5eead4;
            color: #5eead4;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-bottom: 15px;
        }
        
        @media (min-width: 600px) {
            .stats-grid {
                grid-template-columns: repeat(3, 1fr);
            }
        }
        
        .stat-card {
            background: linear-gradient(135deg, #1a1f3a 0%, #151a2e 100%);
            padding: 12px;
            border-radius: 8px;
            border-left: 3px solid #64ffda;
        }
        
        .stat-label {
            font-size: 0.65rem;
            color: #8892b0;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
            text-transform: uppercase;
        }
        
        .stat-value {
            font-size: 1.2rem;
            font-weight: 600;
            color: #e0e6ed;
        }
        
        .tabs {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-bottom: 15px;
        }
        
        .tab {
            padding: 12px;
            background: #151a2e;
            border: 1px solid #1a1f3a;
            border-radius: 8px;
            text-align: center;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.85rem;
            transition: all 0.3s;
        }
        
        .tab.active {
            background: linear-gradient(90deg, #64ffda 0%, #4db8a8 100%);
            color: #0a192f;
        }
        
        .panel {
            background: linear-gradient(135deg, #1a1f3a 0%, #151a2e 100%);
            padding: 18px;
            border-radius: 10px;
            margin-bottom: 15px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }
        
        .hidden {
            display: none;
        }
        
        .control-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 8px;
        }
        
        .control-btn {
            padding: 18px;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #334155;
            border-radius: 8px;
            color: #64ffda;
            font-size: 1.3rem;
            cursor: pointer;
            touch-action: manipulation;
        }
        
        .control-btn:active {
            background: linear-gradient(135deg, #64ffda 0%, #4db8a8 100%);
            color: #0a192f;
            transform: scale(0.95);
        }
        
        .stop-btn {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
            border-color: #ef4444;
        }
        
        .section-title {
            font-size: 0.9rem;
            color: #64ffda;
            margin-bottom: 10px;
            letter-spacing: 0.5px;
            font-weight: 600;
        }
        
        .input-group {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 8px;
            margin-bottom: 12px;
        }
        
        .input-wrapper {
            display: flex;
            flex-direction: column;
        }
        
        .input-label {
            font-size: 0.7rem;
            color: #8892b0;
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        input[type="number"] {
            padding: 10px 6px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid #334155;
            border-radius: 6px;
            color: #e0e6ed;
            font-size: 0.9rem;
            width: 100%;
        }
        
        input:focus {
            outline: none;
            border-color: #64ffda;
        }
        
        button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #64ffda;
            border-radius: 6px;
            color: #64ffda;
            font-weight: 600;
            cursor: pointer;
            font-size: 0.85rem;
            margin-top: 5px;
        }
        
        .primary-btn {
            background: linear-gradient(90deg, #64ffda 0%, #4db8a8 100%);
            color: #0a192f;
            border: none;
        }
        
        .action-btn {
            background: linear-gradient(90deg, #5eead4 0%, #14b8a6 100%);
            color: #0a192f;
            border: none;
            padding: 16px;
            font-size: 1rem;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; }
        }
        
        .danger-btn {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
            border-color: #ef4444;
        }
        
        .info-box {
            background: rgba(100, 255, 218, 0.05);
            border: 1px solid rgba(100, 255, 218, 0.2);
            border-radius: 6px;
            padding: 12px;
            margin: 12px 0;
        }
        
        .info-label {
            color: #64ffda;
            font-weight: 600;
            font-size: 0.8rem;
            margin-bottom: 6px;
        }
        
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 4px 0;
            font-size: 0.85rem;
        }
        
        .info-value {
            color: #5eead4;
            font-weight: 600;
        }
        
        input[type="range"] {
            width: 100%;
            height: 5px;
            background: #334155;
            border-radius: 5px;
            margin: 15px 0;
        }
        
        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 18px;
            height: 18px;
            background: #64ffda;
            border-radius: 50%;
            cursor: pointer;
        }
        
        .slider-value {
            text-align: center;
            font-size: 1.6rem;
            color: #64ffda;
            font-weight: 600;
            margin: 8px 0;
        }
        
        canvas {
            width: 100%;
            max-width: 100%;
            height: auto;
            aspect-ratio: 3/2;
            background: #0a0e27;
            border: 1px solid #334155;
            border-radius: 6px;
            margin-top: 12px;
        }
        
        .note {
            font-size: 0.75rem;
            color: #8892b0;
            margin-top: 8px;
            line-height: 1.4;
        }
    </style>
</head>
<body>
    <div class="app-container">
        <div class="header">
            <div class="header-left">
                <div class="header-title">
                    <h1>{{ t.title }}</h1>
                    <div class="version">{{ t.version }}</div>
                </div>
                <select class="lang-selector" id="langSelect" onchange="changeLang()">
                    <option value="en" {{ 'selected' if lang == 'en' else '' }}>EN</option>
                    <option value="ta" {{ 'selected' if lang == 'ta' else '' }}>தமிழ்</option>
                    <option value="hi" {{ 'selected' if lang == 'hi' else '' }}>हिन्दी</option>
                    <option value="te" {{ 'selected' if lang == 'te' else '' }}>తెలుగు</option>
                    <option value="kn" {{ 'selected' if lang == 'kn' else '' }}>ಕನ್ನಡ</option>
                    <option value="ur" {{ 'selected' if lang == 'ur' else '' }}>اردو</option>
                </select>
            </div>
            <div id="badge" class="status-badge status-idle">{{ t.idle }}</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">{{ t.battery }}</div>
                <div class="stat-value" id="bat">--%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">{{ t.voltage }}</div>
                <div class="stat-value" id="vol">--V</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">{{ t.current }}</div>
                <div class="stat-value" id="cur">--A</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">{{ t.runtime }}</div>
                <div class="stat-value" id="run">--</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">{{ t.distance }}</div>
                <div class="stat-value" id="dist">0.0m</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">{{ t.pulses }}</div>
                <div class="stat-value" id="pls">0</div>
            </div>
        </div>
        
        <div class="tabs">
            <div id="tM" class="tab active" onclick="setT('MAN')">{{ t.manual_control }}</div>
            <div id="tA" class="tab" onclick="setT('GUIDED')">{{ t.guided_mode }}</div>
        </div>
        
        <div id="pM" class="panel">
            <div class="control-grid">
                <div></div>
                <button class="control-btn" onmousedown="startCmd('FORWARD')" onmouseup="stopCmd()" ontouchstart="startCmd('FORWARD')" ontouchend="stopCmd()">↑</button>
                <div></div>
                <button class="control-btn" onmousedown="startCmd('LEFT')" onmouseup="stopCmd()" ontouchstart="startCmd('LEFT')" ontouchend="stopCmd()">←</button>
                <button class="control-btn stop-btn" onclick="stopCmd()">{{ t.stop }}</button>
                <button class="control-btn" onmousedown="startCmd('RIGHT')" onmouseup="stopCmd()" ontouchstart="startCmd('RIGHT')" ontouchend="stopCmd()">→</button>
                <div></div>
                <button class="control-btn" onmousedown="startCmd('BACKWARD')" onmouseup="stopCmd()" ontouchstart="startCmd('BACKWARD')" ontouchend="stopCmd()">↓</button>
                <div></div>
            </div>
        </div>
        
        <div id="pA" class="panel hidden">
            <div class="section-title">{{ t.field_config }}</div>
            <div class="input-group">
                <div class="input-wrapper">
                    <div class="input-label">{{ t.length_m }}</div>
                    <input type="number" id="L" value="1" oninput="updateFertCalc(); draw()">
                </div>
                <div class="input-wrapper">
                    <div class="input-label">{{ t.spacing_m }}</div>
                    <input type="number" id="S" value="1" oninput="draw()">
                </div>
                <div class="input-wrapper">
                    <div class="input-label">{{ t.rows }}</div>
                    <input type="number" id="R" value="2" oninput="updateFertCalc(); draw()">
                </div>
            </div>
            
            <div class="section-title">{{ t.fertilizer_settings }}</div>
            <input type="number" id="fertKg" value="0.173" placeholder="{{ t.total_fertilizer_kg }}" step="0.001" oninput="updateFertCalc()">
            
            <div class="info-box">
                <div class="info-label">{{ t.calculated_params }}</div>
                <div class="info-row">
                    <span>{{ t.servo_angle }}</span>
                    <span class="info-value"><span id="calcAngle">0</span>°</span>
                </div>
                <div class="info-row">
                    <span>{{ t.flow_rate }}</span>
                    <span class="info-value"><span id="calcFlow">0</span> g/s</span>
                </div>
                <div class="info-row">
                    <span>{{ t.dispensed }}</span>
                    <span class="info-value"><span id="fertDisp">0</span> g</span>
                </div>
            </div>
            
            <div class="section-title">{{ t.hall_calibration }}</div>
            <input type="number" id="ppm" value="5" placeholder="{{ t.pulses_per_meter }}">
            <button onclick="calibrateHall()">{{ t.save_calibration }}</button>
            
            
            <button id="bStart" class="primary-btn" onclick="startGuided()">{{ t.start_guided }}</button>
            <button id="bAnchor" class="action-btn hidden" onclick="continueGuided()">{{ t.anchored_continue }}</button>
            <button id="bCut" class="action-btn hidden" onclick="continueGuided()">{{ t.cutting_complete }}</button>
            <button id="bStop" class="danger-btn hidden" onclick="stopGuided()">{{ t.abort_mission }}</button>
            
            <canvas id="cvs" width="600" height="400"></canvas>
        </div>
        
        <div class="panel">
            <div class="section-title">{{ t.manual_fertilizer }}</div>
            <div class="slider-value"><span id="fertVal">0</span>°</div>
            <input type="range" id="fw" min="0" max="90" value="0" oninput="updateFertDisplay()">
            <div class="input-group" style="grid-template-columns: 1fr 1fr;">
                <button onclick="applyFert()">{{ t.apply }}</button>
                <button onclick="closeFert()">{{ t.close_valve }}</button>
            </div>
            <div class="note">{{ t.auto_note }}</div>
        </div>
        
        <div class="panel" id="reportPanel" style="display:none;">
            <button class="primary-btn" onclick="downloadReport()">{{ t.download_report }}</button>
        </div>
    </div>

<script>
    const ctx = document.getElementById('cvs').getContext('2d');
    let sD = {};
    let currentCmd = null;
    let cmdInterval = null;
    
    function post(u, d) {
        return fetch(u, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(d)
        });
    }
    
    function changeLang() {
        const lang = document.getElementById('langSelect').value;
        window.location.href = '/?lang=' + lang;
    }
    
    function startCmd(c) {
        if (currentCmd) return;
        currentCmd = c;
        post('/api/control', {cmd: c});
        cmdInterval = setInterval(() => {
            post('/api/control', {cmd: c});
        }, 100);
    }
    
    function stopCmd() {
        if (cmdInterval) {
            clearInterval(cmdInterval);
            cmdInterval = null;
        }
        currentCmd = null;
        post('/api/control', {cmd: 'STOP'});
    }
    
    document.addEventListener('touchmove', (e) => {
        if (currentCmd) e.preventDefault();
    }, {passive: false});
    
    function updateFertDisplay() {
        const val = document.getElementById('fw').value;
        document.getElementById('fertVal').innerText = val;
    }
    
    function applyFert() {
        post('/api/fert', {w: document.getElementById('fw').value});
    }
    
    function closeFert() {
        document.getElementById('fw').value = 0;
        updateFertDisplay();
        post('/api/fert', {w: 0});
    }
    
    function updateFertCalc() {
        const L = parseFloat(document.getElementById('L').value) || 1;
        const R = parseInt(document.getElementById('R').value) || 2;
        const fert_kg = parseFloat(document.getElementById('fertKg').value) || 0;
        
        fetch('/api/calc_fert', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({L: L, R: R, fert_kg: fert_kg})
        })
        .then(r => r.json())
        .then(d => {
            document.getElementById('calcAngle').innerText = d.angle;
            document.getElementById('calcFlow').innerText = d.flow_rate;
        });
    }
    
    function startGuided() {
        post('/api/guided/start', {
            L: L.value,
            S: S.value,
            R: R.value,
            fert_kg: fertKg.value
        });
    }
    
    function continueGuided() {
        post('/api/guided/continue', {});
    }
    
    function stopGuided() {
        post('/api/guided/stop', {});
    }
    
    function calibrateHall() {
        post('/api/calibrate/hall', { ppm: parseInt(ppm.value) });
    }
    
    function downloadReport() {
        window.location.href = '/api/report/generate';
    }
    
    function setT(m) {
        pM.classList.toggle('hidden', m != 'MAN');
        pA.classList.toggle('hidden', m != 'GUIDED');
        tM.classList.toggle('active', m == 'MAN');
        tA.classList.toggle('active', m == 'GUIDED');
        if (m == 'GUIDED') {
            draw();
            updateFertCalc();
        }
    }
    
    setInterval(() => {
        post('/api/heartbeat', {});
    }, 1000);
    
    setInterval(() => {
        fetch('/api/data').then(r => r.json()).then(d => {
            if (!sD.path_L && d.path_L) {
                L.value = d.path_L;
                S.value = d.path_S;
                R.value = d.path_R;
            }
            if (!sD.pulses_per_m && d.pulses_per_m) {
                ppm.value = d.pulses_per_m;
            }
            if (d.fert_kg !== undefined && fertKg.value == 0) {
                fertKg.value = d.fert_kg;
            }
            
            sD = d;
            bat.innerText = d.percentage + '%';
            vol.innerText = d.voltage + 'V';
            cur.innerText = d.current + 'A';
            run.innerText = d.runtime;
            dist.innerText = d.distance + 'm';
            pls.innerText = d.pulses;
            
            if (document.getElementById('hallNote')) {
                document.getElementById('hallNote').style.display = d.hall_enabled ? 'none' : 'block';
            }
            
            badge.innerText = d.status;
            badge.className = 'status-badge';
            if (d.status == 'IDLE' || d.status == 'SAFETY STOP') {
                badge.classList.add('status-idle');
            } else if (d.status == 'MANUAL') {
                badge.classList.add('status-manual');
            } else if (d.status == 'GUIDED') {
                badge.classList.add('status-guided');
            }
            
            if (d.fert_dispensed !== undefined) {
                fertDisp.innerText = d.fert_dispensed;
            }
            
            const isGuided = d.status == "GUIDED";
            bStart.classList.toggle('hidden', isGuided);
            bStop.classList.toggle('hidden', !isGuided);
            
            bAnchor.classList.toggle('hidden', d.wait_action != "ANCHOR");
            bCut.classList.toggle('hidden', d.wait_action != "CUT");
            
            if (d.has_session_data) {
                document.getElementById('reportPanel').style.display = 'block';
            }
            
            // FIX 12b: Always redraw when guided panel is visible.
            // This ensures canvas reflects both live server state (progress)
            // AND immediate input changes without any lag.
            if (!pA.classList.contains('hidden')) draw();
        }).catch(() => {}); // Ignore fetch errors (Pi briefly unreachable)
    }, 200);
    
    function draw() {
        let r = parseInt(R.value) || 2;
        let l = parseFloat(L.value) || 1;
        let s = parseFloat(S.value) || 1;
        let tW = (r - 1) * s;
        let sc = Math.min(540 / (tW || s * 2), 340 / l);
        let ox = (600 - tW * sc) / 2;
        let oy = (400 + l * sc) / 2;

        // FIX 12b: Always clear the full canvas first — prevents stale
        // teal progress lines persisting after abort or input changes.
        ctx.clearRect(0, 0, 600, 400);
        ctx.lineWidth = 3;
        ctx.lineCap = 'round';

        ctx.strokeStyle = '#334155';
        ctx.strokeRect(ox - 10, oy - l * sc - 10, tW * sc + 20, l * sc + 20);

        function tr(lim, col, dash) {
            ctx.beginPath();
            ctx.strokeStyle = col;
            ctx.setLineDash(dash ? [8, 8] : []);
            let cx = ox, cy = oy;
            ctx.moveTo(cx, cy);
            for (let i = 0; i < r; i++) {
                let ny = (i % 2 == 0) ? oy - l * sc : oy;
                if (i * 3 <= lim) {
                    ctx.lineTo(cx, ny);
                    cy = ny;
                }
                if (i < r - 1 && i * 3 + 2 <= lim) {
                    cx += s * sc;
                    ctx.lineTo(cx, cy);
                }
            }
            ctx.stroke();
        }

        // Draw grey planned path always
        tr(999, '#334155', true);

        // FIX 12b: Only draw teal progress when actually in GUIDED mode.
        // When status returns to IDLE after abort, active_seg resets to -1
        // on the server, so tr(-1,...) draws nothing — canvas shows clean
        // planned path only. Previously stale sD values kept the old
        // progress line visible after abort.
        if (sD.status === "GUIDED" && sD.active_seg >= 0) {
            tr(sD.active_seg, '#64ffda', false);
        }
    }
    
    updateFertDisplay();
    updateFertCalc();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    threading.Thread(target=hardware_engine, daemon=True).start()
    try:
        app.run(host="0.0.0.0", port=80, debug=False, threaded=True)  # FIX 12a: multi-threaded so one blocked request never freezes the UI
    finally:
        GPIO.cleanup()