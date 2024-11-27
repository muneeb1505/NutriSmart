from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai
from PIL import Image
import sqlite3

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


# Database file
DB_FILE = "nutrigenie.db"

# Function to initialize the database
def init_db():
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

# Function to save search queries and responses to the database
def save_to_db(user_query, response):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO searches (user_query, response) VALUES (?, ?)", (user_query, response))
    conn.commit()
    conn.close()

# Function to retrieve saved searches
def get_saved_searches():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_query, response FROM searches ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Function to get Gemini API response
def get_gemini_response(input_prompt, image=None):
    try:
        model = genai.GenerativeModel("gemini-1.5-pro" if image else "gemini-1.5-pro")
        if image:
            response = model.generate_content([input_prompt, image[0]])
        else:
            response = model.generate_content([input_prompt])
        return response.text
    except Exception as e:
        return f"Error: {e}"


# Initialize Streamlit app
st.set_page_config(page_title="NutriGenie", layout="wide", page_icon="🍎")

# Initialize database
init_db()

# Sidebar with search history
st.sidebar.title("📂 Previous Searches")
history = get_saved_searches()
if history:
 for user_query, response in history:
    with st.sidebar.expander(user_query):
        st.write(response)
else:
    st.sidebar.info("No previous searches yet!")

# Main Content
# st.title("NutriGenie - Your Nutrition Assistant")
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
tab1, tab2 = st.tabs(["NutriGenie", "Calorie Tracker with AI"])

# Tab 1: Text-Based Recommendations
with tab1:
    st.header("Your Health Companion")
    col1, col2 = st.columns([9, 1])

    # Text input
    user_query = col1.text_input("Enter your health problem (e.g., diabetes, obesity, heart related, etc):", key="input_box",
    placeholder="Type your health condition here...",)

    # Get recommendations
    if st.button(" 🔍 Get Recommendations"):
        if user_query.strip() == "":
            st.error("Please enter a health problem")
        else:
            prompt = f"""
            You are a certified nutritionist. A user has the following health problem: {user_query}.
            Provide detailed recommendations, including:
            1. Foods to eat.
            2. Foods to avoid.
            3. Lifestyle and exercise tips.
            """
            response = get_gemini_response(prompt)
            save_to_db(user_query, response)
            st.success("🎉 **Your Recommendations Are Ready!**")
            st.write(response)

# Tab 2: Calorie Tracker with AI - Total Calories
# Tab 2: Calorie Tracker with AI - Total Calories
with tab2:
    st.header("Track Calories, Stay Healthy")

    # Drag and Drop File Section
    st.markdown("### Upload Your Meal Image")
    uploaded_file = st.file_uploader("Drag and drop a food image here...", type=["jpg", "jpeg", "png"])

    # Camera Toggle Option
    st.markdown("### Or Capture Your Meal")
    enable_camera = st.checkbox("Enable Camera")

    # Conditional Camera Input
    camera_input = None
    if enable_camera:
        camera_input = st.camera_input("Take a photo of your meal")
        # Close Camera Button
        if st.button("Close Camera"):
            enable_camera = False  # Reset the checkbox (simulated close behavior)

    # Display uploaded or captured image
    image = None
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)
    elif camera_input is not None:
        image = Image.open(camera_input)
        st.image(image, caption="Captured Image", use_column_width=True)

    # Analyze Image
    if st.button("Analyze Image"):
        if image:
            try:
                # Process the image as binary data for the Gemini API
                image_data = [{"mime_type": "image/jpeg", "data": camera_input.getvalue() if camera_input else uploaded_file.getvalue()}]
                input_prompt = """
                You are an expert nutritionist. Analyze the image to identify the food items 
                and calculate the total calories. Provide the result in the following format:

                1. Item 1 - no. of calories
                2. Item 2 - no. of calories
                ----
                Total Calories: XX
                """
                response = get_gemini_response(input_prompt, image_data)
                st.subheader("Analysis Result:")
                st.write(response)
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.error("Please upload or capture an image to analyze.")

