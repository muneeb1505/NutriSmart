from dotenv import load_dotenv
import streamlit as st
import sqlite3
import os
import google.generativeai as genai
import pyttsx3  # Text-to-Speech library
import speech_recognition as sr  # Speech recognition library

# Load environment variables
load_dotenv()

# Configure Gemini API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize the TTS engine
engine = pyttsx3.init()

# Initialize the speech recognizer
recognizer = sr.Recognizer()

# Database setup
DB_FILE = "nutrigenie.db"

def init_db():
    """Initialize the database and create tables if not exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_query TEXT,
            response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_to_db(user_query, response):
    """Save the user query and response to the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO searches (user_query, response) VALUES (?, ?)", (user_query, response))
    conn.commit()
    conn.close()

def get_saved_searches():
    """Retrieve previous searches from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_query, response FROM searches ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Function to get Gemini response
def get_gemini_response(prompt):
    model = genai.GenerativeModel("gemini-1.5-pro")
    response = model.generate_content([prompt])
    return response.text

# Function to convert text to speech
def text_to_speech(text):
    engine.say(text)
    engine.runAndWait()

# Function to capture audio and convert to text
def speech_to_text():
    with sr.Microphone() as source:
        st.info("🎤 Listening... Speak now.")
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            st.success(f"✅ You said: {text}")
            return text
        except sr.UnknownValueError:
            st.error("⚠️ Could not understand the audio. Please try again.")
        except sr.RequestError:
            st.error("⚠️ Could not request results; please check your internet connection.")
        except Exception as e:
            st.error(f"⚠️ Error: {e}")
    return None

# Initialize Streamlit app
st.set_page_config(page_title="NutriGenie", layout="wide", page_icon="🍎")

# Initialize the database
init_db()

# Sidebar - Display previous searches
st.sidebar.title("📂 Previous Searches")
saved_searches = get_saved_searches()
if saved_searches:
    for query, response in saved_searches:
        st.sidebar.markdown(f"**Query:** {query}")
        st.sidebar.markdown(f"**Response:** {response[:100]}...")  # Truncate response for display
        st.sidebar.markdown("---")
else:
    st.sidebar.info("No previous searches yet!")

# App Title and Introduction
st.markdown(
    """
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;">
    <h1 style="font-size: 2.5rem; margin-top: 20px;">🍎 NutriGenie 🥗</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<p class="info">Welcome to your personalized <strong>AI-powered health assistant!</strong> '
    'Get detailed dietary and lifestyle recommendations based on your health concerns.</p>',
    unsafe_allow_html=True,
)

st.info("✨ Simply enter or speak your health problems, and we'll guide you with expert advice!")

# Input Section
col1, col2 = st.columns([10, 1])
with col1:
    user_health_issue = st.text_input(
        "Describe your health problem or disease (e.g., diabetes, obesity, high blood pressure, heart problems):",
        placeholder="Type your health condition here...",
        key="custom-input",
    )
with col2:
    if st.button("🎤", key="mic-button", help="Click to speak"):
        spoken_input = speech_to_text()
        if spoken_input:
            user_health_issue = spoken_input

# Generate recommendations on button click or speech input
if user_health_issue and st.button("🔍 Get Recommendations", key="custom-button"):
    try:
        # Define the input prompt for health problem
        health_prompt = f"""
        You are a certified nutritionist. A user has the following health problem: {user_health_issue}.
        Provide a comprehensive response with:
        1. Foods the user should eat to improve their condition.
        2. Foods the user should avoid.
        3. Detailed lifestyle and health maintenance tips, including exercises, habits, and precautions.
        """

        # Get Gemini response
        health_response = get_gemini_response(health_prompt)

        # Save query and response to database
        save_to_db(user_health_issue, health_response)

        # Display the recommendations
        st.success("🎉 **Your Recommendations Are Ready!**")
        st.subheader("✅ **Foods to Eat**")
        foods_to_eat = health_response.split("Foods to Avoid")[0].strip()
        st.write(foods_to_eat)

        st.subheader("❌ **Foods to Avoid**")
        foods_to_avoid = health_response.split("Foods to Avoid")[1].split("Tips")[0].strip()
        st.write(foods_to_avoid)

        st.subheader("💡 **Health Tips**")
        health_tips = health_response.split("Tips")[1].strip()
        st.write(health_tips)

        # Speak the response for blind users
        text_to_speech(f"Here are your recommendations. Foods to eat: {foods_to_eat}. "
                       f"Foods to avoid: {foods_to_avoid}. Health tips: {health_tips}.")
    except Exception as e:
        st.error(f"⚠️ Error: {e}")
