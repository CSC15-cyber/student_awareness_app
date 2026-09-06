import json
import secrets
from datetime import datetime
from pathlib import Path

import gspread
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from google.oauth2.service_account import Credentials


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Mobile Device Security Awareness Study",
    page_icon="🛡️",
    layout="wide"
)


# ============================================================
# CUSTOM THEME (clean minimal dashboard style)
# ============================================================

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

:root {
    --ink: #16171D;
    --ink-soft: #52545E;
    --ink-muted: #8C8F9A;
    --border: #E7E8EC;
    --card-bg: #FFFFFF;
    --page-bg: #F4F5F7;
    --sidebar-bg: #16171D;
    --green: #34D399;
    --red: #FB7185;
    --yellow: #FBBF24;
    --blue: #60A5FA;
    --violet: #16171D;
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* ---------- Background: flat, light, no gradients — keeps focus on content ---------- */
.stApp {
    background: var(--page-bg);
}

/* ---------- Base text: dark, readable, everywhere in the main content ---------- */
div[data-testid="stAppViewContainer"] { color: var(--ink); }
h1, h2, h3, h4, h5, h6 { font-family: 'Poppins', sans-serif; color: var(--ink) !important; }
p, span, li, label, div, small { color: var(--ink-soft) !important; }

h1 { font-size: 2.1rem !important; font-weight: 700 !important; letter-spacing: -0.02em; }
h2 { font-size: 1.35rem !important; font-weight: 600 !important; margin-top: 1.4rem; }
h3 { font-size: 1.15rem !important; font-weight: 600 !important; }
.stMarkdown p, div[data-testid="stMarkdownContainer"] p, div[data-testid="stMarkdownContainer"] {
    font-size: 1rem !important;
    line-height: 1.6 !important;
    color: var(--ink-soft) !important;
}
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] *,
.stCaption {
    color: var(--ink-muted) !important;
}

/* ---------- Sidebar: near-black panel, minimal, like the reference nav rail ---------- */
section[data-testid="stSidebar"] {
    background: var(--sidebar-bg);
    border-radius: 0;
    border-right: 1px solid rgba(255, 255, 255, 0.06);
    padding-top: 0.5rem;
}
section[data-testid="stSidebar"] * { color: #C7C9D3 !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    font-family: 'Poppins', sans-serif;
    font-weight: 700 !important;
    color: #FFFFFF !important;
}
section[data-testid="stSidebar"] hr { border-color: rgba(255, 255, 255, 0.10); }
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.14);
    color: #FFFFFF !important;
    border-radius: 10px;
    font-weight: 600;
    width: 100%;
    box-shadow: none;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--green);
    border-color: var(--green);
    color: #16171D !important;
}
section[data-testid="stSidebar"] .stButton > button:hover * { color: #16171D !important; }
section[data-testid="stSidebar"] .stButton > button * { color: #FFFFFF !important; }
section[data-testid="stSidebar"] div[data-testid="stAlert"] {
    background: rgba(255, 255, 255, 0.06) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    box-shadow: none !important;
    border-left: 3px solid var(--green) !important;
}
section[data-testid="stSidebar"] div[data-testid="stAlert"] * { color: #FFFFFF !important; }

/* ---------- Buttons (main body): flat, dark, minimal ---------- */
.stButton > button, .stFormSubmitButton > button {
    background: var(--ink);
    color: #ffffff !important;
    border: none;
    border-radius: 12px;
    padding: 0.65rem 1.5rem;
    font-weight: 600;
    font-size: 1rem;
    box-shadow: none;
    transition: transform 0.15s ease, background 0.15s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    background: #2B2D38;
    transform: translateY(-1px);
}
.stButton > button *, .stFormSubmitButton > button * { color: #ffffff !important; }

/* ---------- Flat white cards, thin border, soft shadow — no glass/blur ---------- */
div[data-testid="stMetric"],
div[data-testid="stForm"],
div[data-testid="stPlotlyChart"],
div[data-testid="stExpander"] {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 18px;
    box-shadow: 0 2px 10px rgba(22, 23, 29, 0.05);
}

div[data-testid="stMetric"] { padding: 1.2rem 1rem; border-left: 3px solid var(--green); }
div[data-testid="column"]:nth-of-type(1) div[data-testid="stMetric"] { border-left-color: var(--green); }
div[data-testid="column"]:nth-of-type(2) div[data-testid="stMetric"] { border-left-color: var(--red); }
div[data-testid="column"]:nth-of-type(3) div[data-testid="stMetric"] { border-left-color: var(--yellow); }
div[data-testid="column"]:nth-of-type(4) div[data-testid="stMetric"] { border-left-color: var(--blue); }

div[data-testid="stMetricValue"] {
    color: var(--ink) !important;
    font-family: 'Poppins', sans-serif;
    font-size: 1.7rem !important;
    font-weight: 700 !important;
}
div[data-testid="stMetricLabel"] { color: var(--ink-muted) !important; font-weight: 600 !important; }

div[data-testid="stForm"] { padding: 2rem 2rem 1rem 2rem; }
div[data-testid="stPlotlyChart"] { padding: 0.8rem 0.8rem 1.4rem 0.8rem; overflow: visible; }

/* ---------- Alerts: flat white card, colored left accent, no blur ---------- */
/* Covers multiple possible DOM shapes across Streamlit versions, plus the
   stable ARIA role as a fallback, since the exact testid can shift. */
div[data-testid="stAlert"],
div[data-testid="stAlertContainer"],
div[data-testid="stNotification"],
.stAlert,
[role="alert"] {
    background: var(--card-bg) !important;
    border-radius: 14px !important;
    border: 1px solid var(--border) !important;
    box-shadow: 0 2px 10px rgba(22, 23, 29, 0.05) !important;
    border-left: 4px solid var(--green) !important;
}
div[data-testid="stAlert"] *,
div[data-testid="stAlertContainer"] *,
div[data-testid="stNotification"] *,
.stAlert *,
[role="alert"] * {
    color: var(--ink) !important;
}

/* ---------- Radio / multiselect option groups ---------- */
div[data-testid="stRadio"] > label,
div[data-testid="stMultiSelect"] > label {
    font-weight: 600 !important;
    color: var(--ink) !important;
    font-size: 1.02rem !important;
}
div[data-testid="stRadio"] > div {
    background: #FAFAFB;
    border-radius: 14px;
    padding: 0.7rem 0.9rem;
    border: 1px solid var(--border);
}
div[data-testid="stRadio"] label p { color: var(--ink-soft) !important; font-size: 0.98rem !important; }

/* ---------- Section headers act as card labels ---------- */
.stMarkdown h2 {
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--border);
}

/* ---------- Selectbox / multiselect: input box + dropdown popover + chips ---------- */
div[data-baseweb="select"],
div[data-baseweb="select"] > div,
div[data-baseweb="select"] div {
    background-color: #FFFFFF !important;
    border-color: var(--border) !important;
    border-radius: 12px !important;
}
div[data-baseweb="select"] input,
div[data-baseweb="select"] span:not([data-baseweb="tag"] span) {
    color: var(--ink) !important;
}

/* the option list renders in a portal, appended near the end of <body> —
   several possible DOM shapes are covered here so the fix holds regardless
   of the exact Streamlit/BaseWeb version rendering it */
div[data-baseweb="popover"],
div[data-baseweb="popover"] *,
ul[data-baseweb="menu"],
ul[data-baseweb="menu"] *,
div[data-testid="stSelectboxVirtualDropdown"],
div[data-testid="stSelectboxVirtualDropdown"] * {
    background-color: #FFFFFF !important;
    color: var(--ink) !important;
}
div[data-baseweb="popover"] li:hover,
div[data-baseweb="popover"] [role="option"]:hover,
div[data-baseweb="popover"] [aria-selected="true"],
div[data-testid="stSelectboxVirtualDropdown"] li:hover,
div[data-testid="stSelectboxVirtualDropdown"] [aria-selected="true"] {
    background-color: #F0FDF9 !important;
}
div[data-baseweb="popover"] {
    box-shadow: 0 10px 28px rgba(22, 23, 29, 0.14) !important;
    border-radius: 12px !important;
    overflow: hidden;
}

/* selected-option chips inside the multiselect box — restyled AFTER the
   rules above so the chip keeps its own look, not the white reset */
span[data-baseweb="tag"], span[data-baseweb="tag"] * {
    background-color: var(--ink) !important;
    color: #FFFFFF !important;
    border-radius: 8px !important;
}

/* ---------- Dividers & captions ---------- */
hr { border-color: var(--border); }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {
    color: var(--ink-muted) !important;
    font-size: 0.9rem !important;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ============================================================
# PATH CONFIGURATION
# ============================================================

APP_DIR = Path(__file__).resolve().parent


# ============================================================
# SESSION STATE
# ============================================================

if "anonymous_id" not in st.session_state:
    st.session_state.anonymous_id = ""

if "survey_submitted" not in st.session_state:
    st.session_state.survey_submitted = False

if "survey_answers" not in st.session_state:
    st.session_state.survey_answers = {}


# ============================================================
# QUESTION CONFIGURATION
# ============================================================

QUESTIONS = {

    1: {
        "question": "Q1. What is your current level of education?",
        "options": [
            "Junior College",
            "Undergraduate",
            "Other"
        ]
    },

    2: {
        "question": "Q2. Which mobile operating system do you primarily use?",
        "options": [
            "Android",
            "iOS"
        ]
    },

    3: {
        "question": "Q3. How would you rate your overall awareness of mobile device security?",
        "options": [
            "Very High",
            "High",
            "Moderate",
            "Low",
            "Very Low"
        ]
    },

    4: {
        "question": "Q4. Which of the following do you think is the biggest security risk to a smartphone user?",
        "options": [
            "Malware or malicious applications",
            "Phishing and online scams",
            "Theft or loss of the device",
            "Unauthorized access to personal data",
            "I am not sure"
        ]
    },

    5: {
        "question": "Q5. How do you primarily protect your smartphone from unauthorized access?",
        "options": [
            "PIN/Password",
            "Pattern",
            "Fingerprint",
            "Face recognition",
            "Combination of two or more methods",
            "I do not use any screen lock"
        ]
    },

    6: {
        "question": "Q6. Why is biometric authentication useful on a smartphone?",
        "options": [
            "It provides an additional method of authentication",
            "It increases internet speed",
            "It protects the phone from malware",
            "It prevents all types of cyberattacks",
            "I don't know"
        ]
    },

    7: {
        "question": "Q7. How regularly do you install operating-system/security updates on your smartphone?",
        "options": [
            "As soon as they are available",
            "Within a few days/weeks",
            "Only when the phone forces me to update",
            "Rarely",
            "Never / I don't know how"
        ]
    },

    8: {
        "question": "Q8. What is the main security benefit of keeping your smartphone and apps updated?",
        "options": [
            "It can fix known security vulnerabilities",
            "It increases battery capacity",
            "It increases storage space",
            "It prevents every possible cyberattack",
            "I don't know"
        ]
    },

    9: {
        "question": "Q9. Before installing an unfamiliar application, what do you usually check?",
        "options": [
            "Developer/publisher",
            "Reviews and ratings",
            "Permissions requested",
            "Source from which it is downloaded",
            "More than one of the above",
            "I normally don't check"
        ]
    },

    10: {
        "question": "Q10. An ordinary calculator app asks for access to your contacts, microphone and location. What would you most likely do?",
        "options": [
            "Allow all permissions",
            "Allow them without checking",
            "Check whether the permissions are necessary and deny unnecessary access",
            "Install it anyway because it is a calculator",
            "I don't know"
        ]
    },

    11: {
        "question": "Q11. Which of the following information can be at risk when unnecessary app permissions are granted?",
        "options": [
            "Location",
            "Contacts",
            "Microphone/camera data",
            "Personal information",
            "All of the above"
        ]
    },

    12: {
        "question": "Q12. What is phishing?",
        "options": [
            "A method of improving Wi-Fi speed",
            "A fraudulent attempt to obtain sensitive information",
            "A type of smartphone virus",
            "A method of backing up data",
            "I don't know"
        ]
    },

    13: {
        "question": "Q13. You receive a message saying, 'Your bank account will be blocked today. Click this link immediately to verify your account.' What should you do?",
        "options": [
            "Click the link immediately",
            "Enter the requested details",
            "Forward the message to friends",
            "Verify the message through the bank's official website/app or other official channel",
            "I don't know"
        ]
    },

    14: {
        "question": "Q14. Which situation is an example of social engineering?",
        "options": [
            "Someone manipulates you into revealing an OTP or password",
            "Your phone battery becomes low",
            "Your internet connection becomes slow",
            "Your phone receives a software update",
            "I don't know"
        ]
    },

    15: {
        "question": "Q15. Which of the following is a common sign of a potentially malicious application?",
        "options": [
            "It requests unnecessary permissions",
            "It comes from an untrusted source",
            "It behaves suspiciously or displays excessive unwanted advertisements",
            "All of the above",
            "I don't know"
        ]
    },

    16: {
        "question": "Q16. Which of the following mobile-device practices do you sometimes engage in? (Select all that apply)",
        "options": [
            "Installing apps from unofficial/unknown sources",
            "Connecting to unknown public Wi-Fi",
            "Clicking links from unknown senders",
            "Ignoring software/security updates",
            "Giving apps permissions without checking",
            "Sharing my phone PIN/password with others",
            "None of the above"
        ]
    },

    17: {
        "question": "Q17. When using public Wi-Fi, which activity do you consider safest?",
        "options": [
            "Accessing sensitive banking/payment accounts without checking the network",
            "Entering passwords on unknown websites",
            "Avoiding sensitive activities on untrusted networks",
            "Connecting automatically to any available Wi-Fi",
            "I don't know"
        ]
    },

    18: {
        "question": "Q18. Which measure would help you most in improving your mobile device security awareness?",
        "options": [
            "Cybersecurity awareness programs/workshops in college",
            "Practical demonstrations of real-world scams and attacks",
            "Regular security tips through college communication channels",
            "Training on privacy, app permissions and smartphone security settings",
            "All of the above"
        ]
    }
}


# ============================================================
# QUESTION AREAS
# ============================================================

QUESTION_AREAS = {
    3: "Overall Security Awareness",
    4: "Security Threat Awareness",
    5: "Screen Lock Security",
    6: "Biometric Authentication Knowledge",
    7: "Software Update Behaviour",
    8: "Security Update Knowledge",
    9: "Safe App Installation",
    10: "App Permission Decisions",
    11: "Privacy and Permissions",
    12: "Phishing Awareness",
    13: "Phishing Response Behaviour",
    14: "Social Engineering Awareness",
    15: "Malicious App Awareness",
    16: "Risky Mobile Security Practices",
    17: "Public Wi-Fi Safety"
}

AWARENESS_QUESTIONS = [3, 4, 6, 8, 11, 12, 14, 15]

BEHAVIOUR_QUESTIONS = [5, 7, 9, 10, 13, 16, 17]


# ============================================================
# GOOGLE SHEETS CONNECTION
# ============================================================

def find_service_account_file():

    preferred_file = APP_DIR / "service_account.json"

    if preferred_file.exists():
        return preferred_file

    for json_file in APP_DIR.glob("*.json"):

        try:
            with open(json_file, "r", encoding="utf-8") as file:
                data = json.load(file)

            if data.get("type") == "service_account":
                return json_file

        except Exception:
            continue

    return None


@st.cache_resource
def get_google_client():

    service_file = find_service_account_file()

    if service_file is None:
        raise FileNotFoundError(
            "Service account JSON file was not found in the application folder."
        )

    credentials = Credentials.from_service_account_file(
        str(service_file),
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )

    return gspread.authorize(credentials)


@st.cache_resource
def get_worksheet():

    client = get_google_client()

    spreadsheet_id = st.secrets["google_sheet"]["spreadsheet_id"]
    worksheet_name = st.secrets["google_sheet"]["worksheet_name"]

    spreadsheet = client.open_by_key(spreadsheet_id)

    return spreadsheet.worksheet(worksheet_name)


# ============================================================
# ANONYMOUS ID
# ============================================================

def generate_anonymous_id():
    return f"AWARE-{secrets.token_hex(4).upper()}"


# ============================================================
# SCORE LEVEL
# ============================================================

def get_score_level(score):

    if score >= 80:
        return "Excellent"

    elif score >= 60:
        return "Good"

    elif score >= 40:
        return "Moderate"

    elif score >= 20:
        return "Low"

    return "Very Low"


# ============================================================
# SCORE RISK STYLE (colour-coded by percentage)
# ============================================================

def get_score_style(score):

    if score >= 70:
        return {
            "color": "#16A34A",
            "bg": "rgba(22, 163, 74, 0.10)",
            "label": "Low Risk",
            "icon": "✅"
        }

    elif score >= 40:
        return {
            "color": "#F59E0B",
            "bg": "rgba(245, 158, 11, 0.12)",
            "label": "Medium Risk",
            "icon": "⚠️"
        }

    return {
        "color": "#EF4444",
        "bg": "rgba(239, 68, 68, 0.12)",
        "label": "High Risk",
        "icon": "🚨"
    }


# ============================================================
# GAP INTERPRETATION
# ============================================================

def get_gap_interpretation(awareness_score, behaviour_score):

    gap = awareness_score - behaviour_score

    if gap >= 20:
        return (
            "Large Awareness–Behaviour Gap",
            "You demonstrate good security awareness, but your everyday mobile security practices need significant improvement."
        )

    elif gap >= 10:
        return (
            "Moderate Awareness–Behaviour Gap",
            "Your security knowledge is stronger than your everyday security behaviour. Improving consistency is recommended."
        )

    elif gap <= -10:
        return (
            "Behaviour Stronger Than Awareness",
            "Your practical security behaviour is relatively stronger than your theoretical awareness. Learning more about mobile security concepts can strengthen your overall profile."
        )

    return (
        "Well Balanced",
        "Your mobile security awareness and behaviour are reasonably well aligned."
    )


# ============================================================
# QUESTION SCORING
# ============================================================

def score_question(question_number, answer):

    answer = str(answer).strip().lower()

    correct_answers = {

        6: "it provides an additional method of authentication",

        8: "it can fix known security vulnerabilities",

        10: "check whether the permissions are necessary and deny unnecessary access",

        11: "all of the above",

        12: "a fraudulent attempt to obtain sensitive information",

        13: "verify the message through the bank's official website/app or other official channel",

        14: "someone manipulates you into revealing an otp or password",

        15: "all of the above",

        17: "avoiding sensitive activities on untrusted networks"
    }


    # Q3 - Self-rated awareness
    if question_number == 3:

        scores = {
            "very high": 5,
            "high": 4,
            "moderate": 3,
            "low": 2,
            "very low": 1
        }

        return scores.get(answer, 0)


    # Q4 - Threat awareness
    if question_number == 4:

        if answer == "i am not sure":
            return 0

        return 5


    # Q5 - Screen lock behaviour
    if question_number == 5:

        if answer == "combination of two or more methods":
            return 5

        elif answer in [
            "pin/password",
            "fingerprint",
            "face recognition"
        ]:
            return 4

        elif answer == "pattern":
            return 3

        return 0


    # Q7 - Update behaviour
    if question_number == 7:

        scores = {
            "as soon as they are available": 5,
            "within a few days/weeks": 4,
            "only when the phone forces me to update": 2,
            "rarely": 1,
            "never / i don't know how": 0
        }

        return scores.get(answer, 0)


    # Q9 - App installation behaviour
    if question_number == 9:

        scores = {
            "more than one of the above": 5,
            "permissions requested": 4,
            "source from which it is downloaded": 4,
            "developer/publisher": 3,
            "reviews and ratings": 3,
            "i normally don't check": 0
        }

        return scores.get(answer, 0)


    # Q16 - Risky behaviour
    if question_number == 16:

        if "none of the above" in answer:
            return 5

        risky_keywords = [
            "installing apps",
            "connecting to unknown",
            "clicking links",
            "ignoring software",
            "giving apps permissions",
            "sharing my phone"
        ]

        risky_count = sum(
            keyword in answer
            for keyword in risky_keywords
        )

        return max(0, 5 - risky_count)


    # Standard knowledge questions
    if question_number in correct_answers:

        if answer == correct_answers[question_number]:
            return 5

        return 0


    return 0


# ============================================================
# PERSONAL SUGGESTIONS
# ============================================================

SUGGESTIONS = {

    3: "Improve your understanding of general mobile device security and the threats that affect smartphones.",

    4: "Learn more about major smartphone threats such as phishing, malware and unauthorized access.",

    5: "Use a strong screen lock and biometric authentication whenever possible.",

    6: "Learn how biometric authentication provides an additional layer of authentication security.",

    7: "Install operating system and security updates regularly instead of delaying them.",

    8: "Remember that software updates often fix known security vulnerabilities.",

    9: "Before installing an unfamiliar app, check the developer, reviews, permissions and download source.",

    10: "Only allow permissions that are necessary for an application's actual purpose.",

    11: "Review app permissions regularly because unnecessary permissions can expose personal information.",

    12: "Learn how phishing attacks attempt to trick users into revealing sensitive information.",

    13: "Never click suspicious urgent links. Verify messages through official websites or applications.",

    14: "Never share OTPs, passwords or sensitive information with people who pressure or manipulate you.",

    15: "Avoid suspicious applications, especially apps requesting unnecessary permissions or coming from untrusted sources.",

    16: "Reduce risky habits such as clicking unknown links, installing unofficial apps, ignoring updates and sharing passwords.",

    17: "Avoid sensitive activities such as banking or entering important passwords on untrusted public Wi-Fi."
}


# ============================================================
# SAVE RESPONSE TO GOOGLE SHEETS
# ============================================================

def save_response(answers):

    worksheet = get_worksheet()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    headers = worksheet.row_values(1)

    if not headers:
        raise Exception(
            "Google Sheet does not contain headers in Row 1."
        )

    row = []

    for header in headers:

        header_clean = str(header).strip()

        if header_clean == "Anonymous ID":

            row.append(st.session_state.anonymous_id)

        elif header_clean == "Timestamp":

            row.append(timestamp)

        else:

            found_question = False

            for q_number in range(1, 19):

                if (
                    header_clean == f"Q{q_number}"
                    or header_clean.startswith(f"Q{q_number}.")
                ):

                    row.append(answers.get(q_number, ""))

                    found_question = True

                    break

            if not found_question:
                row.append("")


    # Save response
    worksheet.append_row(
        values=row,
        value_input_option="RAW",
        insert_data_option="INSERT_ROWS"
    )


    # Verify the save
    recent_values = worksheet.get_all_values()[-10:]

    response_saved = any(
        st.session_state.anonymous_id in sheet_row
        for sheet_row in recent_values
    )

    if not response_saved:

        raise Exception(
            "The response could not be verified in Google Sheets."
        )

    return True


# ============================================================
# ANALYSIS
# ============================================================

def analyse_answers(answers):

    results = []

    for q_number in range(3, 18):

        score = score_question(
            q_number,
            answers.get(q_number, "")
        )

        category = (
            "Awareness"
            if q_number in AWARENESS_QUESTIONS
            else "Behaviour"
        )

        results.append({

            "Question": f"Q{q_number}",
            "Area": QUESTION_AREAS[q_number],
            "Category": category,
            "Score": score,
            "Answer": answers.get(q_number, "")
        })


    df = pd.DataFrame(results)


    awareness_total = df[
        df["Category"] == "Awareness"
    ]["Score"].sum()


    behaviour_total = df[
        df["Category"] == "Behaviour"
    ]["Score"].sum()


    awareness_score = (
        awareness_total /
        (len(AWARENESS_QUESTIONS) * 5)
    ) * 100


    behaviour_score = (
        behaviour_total /
        (len(BEHAVIOUR_QUESTIONS) * 5)
    ) * 100


    overall_score = (
        awareness_score + behaviour_score
    ) / 2


    return (
        df,
        awareness_score,
        behaviour_score,
        overall_score
    )


# ============================================================
# RESULTS PAGE
# ============================================================

def show_results():

    answers = st.session_state.survey_answers

    (
        results_df,
        awareness_score,
        behaviour_score,
        overall_score
    ) = analyse_answers(answers)


    gap = awareness_score - behaviour_score


    st.title("📊 Your Personalized Security Results")

    st.success(
        f"✅ Your response was successfully saved to Google Sheets!"
    )

    st.caption(
        f"Anonymous ID: {st.session_state.anonymous_id}"
    )


    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "🧠 Awareness",
        f"{awareness_score:.1f}%"
    )

    col2.metric(
        "📱 Behaviour",
        f"{behaviour_score:.1f}%"
    )

    col3.metric(
        "⚖️ Gap",
        f"{abs(gap):.1f}%"
    )

    col4.metric(
        "🏆 Overall",
        f"{overall_score:.1f}%"
    )


    # ========================================================
    # CHART
    # ========================================================

    st.subheader("📈 Your Security Profile")

    fig = go.Figure()

    bar_labels = ["Awareness", "Behaviour"]
    bar_values = [awareness_score, behaviour_score]

    # Green for the stronger score, coral for the one needing work —
    # mirrors the alternating green/red bar rhythm of the reference dashboard,
    # and reads clearly as "good" vs. "needs attention".
    top_index = 0 if awareness_score >= behaviour_score else 1

    bar_colors = ["#FB7185", "#FB7185"]
    bar_colors[top_index] = "#34D399"

    # Only the non-highlighted bar gets a plain text label; the highlighted
    # bar's value is shown by the floating callout bubble instead, so the
    # two labels never land on top of each other.
    bar_text = ["", ""]
    other_index = 1 - top_index
    bar_text[other_index] = f"{bar_values[other_index]:.0f}%"

    fig.add_trace(
        go.Bar(
            x=bar_labels,
            y=bar_values,
            marker=dict(color=bar_colors, line=dict(width=0)),
            width=0.34,
            text=bar_text,
            textposition="outside",
            textfont=dict(family="Poppins, sans-serif", size=16, color="#16171D"),
            hovertemplate="%{x}: %{y:.1f}%<extra></extra>"
        )
    )

    # Rounded bar tops if the installed Plotly version supports it;
    # silently skipped on older versions rather than breaking the app.
    try:
        fig.update_traces(marker_cornerradius=10)
    except Exception:
        pass

    # Floating callout bubble above the stronger score
    fig.add_annotation(
        x=bar_labels[top_index],
        y=bar_values[top_index] + max(bar_values) * 0.22,
        text=f"<b>{bar_values[top_index]:.0f}%</b>",
        showarrow=False,
        bgcolor="#34D399",
        bordercolor="#34D399",
        borderwidth=1,
        borderpad=8,
        font=dict(family="Poppins, sans-serif", size=13, color="#16171D")
    )

    fig.update_layout(
        yaxis=dict(
            range=[0, max(bar_values) * 1.55],
            showgrid=False,
            showticklabels=False,
            zeroline=False
        ),
        xaxis=dict(
            showline=False,
            tickfont=dict(family="Plus Jakarta Sans, sans-serif", size=15, color="#16171D")
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#16171D"),
        margin=dict(t=60, b=45, l=10, r=10),
        height=370,
        bargap=0.55,
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False}
    )


    # ========================================================
    # GAP
    # ========================================================

    st.subheader("⚖️ Awareness–Behaviour Gap")

    gap_title, gap_message = get_gap_interpretation(
        awareness_score,
        behaviour_score
    )

    st.info(
        f"### {gap_title}\n\n{gap_message}"
    )


    # ========================================================
    # WEAK AREAS
    # ========================================================

    st.subheader("⚠️ Risk / Weak Areas")

    weak_areas = results_df[
        results_df["Score"] <= 2
    ]

    if weak_areas.empty:

        st.success(
            "🎉 No major weak areas were identified."
        )

    else:

        for _, row in weak_areas.iterrows():

            st.warning(
                f"⚠️ **{row['Area']}**"
            )


    # ========================================================
    # PERSONAL SUGGESTIONS
    # ========================================================

    st.subheader("💡 Personal Suggestions")

    improvement_areas = results_df[
        results_df["Score"] <= 3
    ]

    if improvement_areas.empty:

        st.success(
            "🎉 Excellent! Continue maintaining your safe mobile security habits."
        )

    else:

        shown = set()

        for _, row in improvement_areas.iterrows():

            q_number = int(
                row["Question"].replace("Q", "")
            )

            if q_number not in shown:

                shown.add(q_number)

                suggestion = SUGGESTIONS.get(
                    q_number,
                    "Continue improving your mobile security awareness."
                )

                st.info(
                    f"💡 **{row['Area']}**\n\n{suggestion}"
                )


    # ========================================================
    # FINAL ASSESSMENT
    # ========================================================

    st.subheader("🏆 Final Assessment")

    risk_style = get_score_style(overall_score)

    st.markdown(
        f"""
        <div style="
            background: {risk_style['bg']};
            border: 2px solid {risk_style['color']};
            border-radius: 20px;
            padding: 1.8rem 2rem;
            text-align: center;
            box-shadow: 0 0 0 4px {risk_style['color']}22, 0 6px 20px {risk_style['color']}33;
        ">
            <div style="
                display: inline-block;
                font-family: 'Poppins', sans-serif;
                font-weight: 700;
                font-size: 0.95rem;
                letter-spacing: 0.03em;
                color: {risk_style['color']};
                background: #FFFFFF;
                border: 1px solid {risk_style['color']};
                border-radius: 999px;
                padding: 0.25rem 0.9rem;
                margin-bottom: 0.6rem;
            ">
                {risk_style['icon']} {risk_style['label']}
            </div>
            <div style="font-family: 'Poppins', sans-serif; font-size: 1.5rem; font-weight: 700; color: #16171D;">
                {get_score_level(overall_score)}
            </div>
            <div style="color: #52545E; margin-top: 0.35rem; font-size: 0.95rem;">
                Your overall mobile device security score is
            </div>
            <div style="font-family: 'Poppins', sans-serif; font-size: 3rem; font-weight: 800; color: {risk_style['color']}; line-height: 1.2; margin-top: 0.2rem;">
                {overall_score:.1f}%
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


    st.divider()


    if st.button(
        "🔄 Start New Survey",
        use_container_width=True
    ):

        st.session_state.anonymous_id = ""
        st.session_state.survey_answers = {}
        st.session_state.survey_submitted = False

        st.rerun()





# ============================================================
# MAIN APPLICATION
# ============================================================

st.title("🛡️ Mobile Device Security Awareness Study")

st.write(
    "This survey evaluates your mobile device security awareness and everyday security behaviour."
)


# ============================================================
# SHOW RESULTS AFTER SUBMISSION
# ============================================================

if st.session_state.survey_submitted:

    show_results()

    st.stop()


# ============================================================
# STEP 1 — GENERATE ANONYMOUS ID
# ============================================================

st.subheader("🔐 Step 1: Generate Your Anonymous ID")

if not st.session_state.anonymous_id:

    st.info(
        "Your identity remains anonymous. Generate your unique ID before starting the survey."
    )

    if st.button(
        "🔐 Generate My Anonymous ID",
        use_container_width=True
    ):

        st.session_state.anonymous_id = generate_anonymous_id()

        st.rerun()

else:

    st.success(
        f"Your Anonymous ID: {st.session_state.anonymous_id}"
    )


# ============================================================
# STEP 2 — SURVEY
# ============================================================

if st.session_state.anonymous_id:

    st.divider()

    st.subheader(
        "📝 Step 2: Complete the 18-Question Survey"
    )


    # Helper function
    # index=None means NO ANSWER is selected by default
    def unanswered_radio(question_number):

        return st.radio(
            QUESTIONS[question_number]["question"],
            QUESTIONS[question_number]["options"],
            index=None,
            key=f"question_{question_number}"
        )


    with st.form("security_survey"):

        answers = {}


        # ====================================================
        # SECTION A
        # ====================================================

        st.markdown("## 👤 Section A — Basic Information")

        answers[1] = unanswered_radio(1)

        answers[2] = unanswered_radio(2)


        # ====================================================
        # SECTION B
        # ====================================================

        st.markdown("## 🧠 Section B — Mobile Device Security Awareness")

        answers[3] = unanswered_radio(3)

        answers[4] = unanswered_radio(4)


        # ====================================================
        # SECTION C
        # ====================================================

        st.markdown("## 🔐 Section C — Screen Lock & Authentication")

        answers[5] = unanswered_radio(5)

        answers[6] = unanswered_radio(6)


        # ====================================================
        # SECTION D
        # ====================================================

        st.markdown("## 🔄 Section D — Software Updates")

        answers[7] = unanswered_radio(7)

        answers[8] = unanswered_radio(8)


        # ====================================================
        # SECTION E
        # ====================================================

        st.markdown("## 📱 Section E — App Permissions & Privacy")

        answers[9] = unanswered_radio(9)

        answers[10] = unanswered_radio(10)

        answers[11] = unanswered_radio(11)


        # ====================================================
        # SECTION F
        # ====================================================

        st.markdown("## 🎣 Section F — Phishing, Malware & Social Engineering")

        answers[12] = unanswered_radio(12)

        answers[13] = unanswered_radio(13)

        answers[14] = unanswered_radio(14)

        answers[15] = unanswered_radio(15)


        # ====================================================
        # SECTION G
        # ====================================================

        st.markdown("## ⚠️ Section G — Risky Mobile Security Practices")

        answers[16] = st.multiselect(
            QUESTIONS[16]["question"],
            QUESTIONS[16]["options"],
            key="question_16"
        )

        answers[17] = unanswered_radio(17)


        # ====================================================
        # SECTION H
        # ====================================================

        st.markdown("## 🛡️ Section H — Improving Mobile Security Awareness")

        answers[18] = unanswered_radio(18)


        submitted = st.form_submit_button(
            "🚀 Submit Survey & View My Results",
            use_container_width=True
        )


    # ========================================================
    # SUBMISSION VALIDATION AND SAVE
    # ========================================================

    if submitted:

        unanswered_questions = []

        # Check all questions
        for q_number in range(1, 19):

            if q_number == 16:

                if not answers[16]:
                    unanswered_questions.append("Q16")

            else:

                if answers[q_number] is None:
                    unanswered_questions.append(f"Q{q_number}")


        # Show missing questions
        if unanswered_questions:

            st.error(
                "⚠️ Please answer all questions before submitting: "
                + ", ".join(unanswered_questions)
            )

            st.stop()


        # Prevent contradictory Q16 selection
        if (
            "None of the above" in answers[16]
            and len(answers[16]) > 1
        ):

            st.error(
                "⚠️ For Q16, 'None of the above' cannot be selected together with other options."
            )

            st.stop()


        # Convert Q16 list to text before saving
        answers[16] = ", ".join(answers[16])


        # ====================================================
        # SAVE RESPONSE
        # ====================================================

        try:

            with st.spinner(
                "🔒 Saving your response securely..."
            ):

                saved = save_response(answers)


            # ONLY SHOW RESULTS AFTER SUCCESSFUL SAVE
            if saved:

                st.session_state.survey_answers = answers

                st.session_state.survey_submitted = True

                st.rerun()


            else:

                st.error(
                    "❌ The response could not be confirmed in Google Sheets."
                )


        except Exception as error:

            st.error(
                "❌ Your response could not be saved to Google Sheets."
            )

            st.code(str(error))