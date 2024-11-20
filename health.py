from dotenv import load_dotenv
import streamlit as st
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

# Custom CSS for centered and modern UI with 10px borders
st.markdown(
    """
    <style>
    .main-content {
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
    }
    .custom-input {
        width: 50%;
        margin: 0 auto;
        border-radius: 8px;
        border: 10px solid #ccc;
        padding: 10px;
        font-size: 16px;
        position: relative;
    }
    .custom-button {
        width: 50%;
        margin-top: 20px;
        border-radius: 8px;
        padding: 10px;
        font-size: 16px;
        background-color: #ff6f61;
        color: white;
        border: 10px solid #ccc;
        cursor: pointer;
    }
    .mic-icon {
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
        cursor: pointer;
        font-size: 20px;
        color: #ff6f61;
    }
    .title {
        text-align: center;
        font-size: 2.5rem;
        margin-bottom: 10px;
    }
    .info {
        text-align: center;
        font-size: 1.1rem;
        color: #6c757d;
        margin-bottom: 30px;
    }
    .recommendations {
        max-width: 800px;
        margin: 20px auto;
    }
    img {
        display: block;
        margin-left: auto;
        margin-right: auto;
        border-radius: 10px;
        max-width: 100%;
        height: auto;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# App Title and Introduction
st.markdown('<div class="main-content">', unsafe_allow_html=True)
st.image("health food.jpg", width=300)  # Add the image path here
st.markdown('<h1 class="title">🍎 NutriGenie 🥗</h1>', unsafe_allow_html=True)
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

        # Display the recommendations
        st.markdown('<div class="recommendations">', unsafe_allow_html=True)
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
        st.markdown('</div>', unsafe_allow_html=True)

        # Speak the response for blind users
        text_to_speech(f"Here are your recommendations. Foods to eat: {foods_to_eat}. "
                       f"Foods to avoid: {foods_to_avoid}. Health tips: {health_tips}.")

    except Exception as e:
        st.error(f"⚠️ Error: {e}")

st.markdown('</div>', unsafe_allow_html=True)

