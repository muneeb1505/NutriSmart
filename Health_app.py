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
    <style>
        .responsive-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
        }
        .responsive-container h1 {
            font-size: 2.5rem;
            margin-top: 20px;
        }
        /* Media Queries for responsiveness */
        @media (max-width: 768px) {
            .responsive-container h1 {
                font-size: 2rem;  /* Adjust font size for tablets */
            }
        }
        @media (max-width: 480px) {
            .responsive-container h1 {
                font-size: 1.5rem;  /* Adjust font size for mobile devices */
            }
        }
        img{
         width: 200px;
         height: 100px;
         border-radius: 10px;
        }
    </style>
    
      <div class="responsive-container">
        <h1>🍎 NutriGenie 🥗</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<p class="info"><br>Welcome to your personalized <strong>AI-powered health assistant!</strong> '
    'Get detailed dietary and lifestyle recommendations based on your health concerns.</p>',
    unsafe_allow_html=True,
)
tab1, tab2, tab3 = st.tabs(["NutriGenie", "Calorie Tracker with AI", " Calorie Calculator"])

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

# Tab 3: Calculate calorie needs
with tab3:
    st.markdown("### Enter your details to calculate your daily calorie needs.")

    # Input fields
    age = st.number_input("Enter your age (years):", min_value=1, max_value=120, step=1, key="age_input")
    gender = st.radio("Select your gender:", ("Male", "Female"), key="gender_input")
    height = st.number_input("Enter your height (cm):", min_value=50.0, max_value=250.0, step=0.1, key="height_input")
    weight = st.number_input("Enter your weight (kg):", min_value=10.0, max_value=300.0, step=0.1, key="weight_input")
    activity_level = st.selectbox(
        "Select your activity level:",
        ("Sedentary (little or no exercise)", 
         "Lightly active (light exercise/sports 1-3 days a week)",
         "Moderately active (moderate exercise/sports 3-5 days a week)",
         "Very active (hard exercise/sports 6-7 days a week)", 
         "Extra active (very hard exercise/sports and a physical job)"),
        key="activity_input"
    )

    if st.button("Calculate Calorie Needs"):
        if age <= 0 or height <= 0 or weight <= 0:
            st.error("Please enter valid age, height, and weight values.")
        else:
            # Mifflin-St Jeor Equation for BMR
            if gender == "Male":
                bmr = 10 * weight + 6.25 * height - 5 * age + 5
            else:  # Female
                bmr = 10 * weight + 6.25 * height - 5 * age - 161
            
            # Adjust for activity level
            if activity_level == "Sedentary (little or no exercise)":
                calorie_needs = bmr * 1.2
            elif activity_level == "Lightly active (light exercise/sports 1-3 days a week)":
                calorie_needs = bmr * 1.375
            elif activity_level == "Moderately active (moderate exercise/sports 3-5 days a week)":
                calorie_needs = bmr * 1.55
            elif activity_level == "Very active (hard exercise/sports 6-7 days a week)":
                calorie_needs = bmr * 1.725
            elif activity_level == "Extra active (very hard exercise/sports and a physical job)":
                calorie_needs = bmr * 1.9

            st.success("🎉 **Your Calorie Needs Are Calculated!**")
            st.subheader(f"Recommended Daily Calorie Intake: {int(calorie_needs)} kcal")
