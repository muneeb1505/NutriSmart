from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai
from PIL import Image
import sqlite3
import io

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
st.set_page_config(page_title="NutriSmart", layout="wide", page_icon="🍎")

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
                font-size: 2rem;  /* Adjust font size for mobile devices */
            }
        }
    </style>
    
      <div class="responsive-container">
        <h1>🍎 NutriSmart 🥗</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<p class="info"><br>Welcome to your personalized <strong>AI-powered health assistant!</strong> '
    'Get detailed dietary and lifestyle recommendations based on your health concerns.</p>',
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["NutriSmart", "AI-Calorie Tracker", " Calorie Calculator", "Recipe Suggestions", "Personalized Shopping List"])

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
                Calories
                1. Item 1 - no. of calories
                2. Item 2 - no. of calories
                ----

                Protein
                1.Item 1 - no. of protein
                2.Item 2 - no. of protein
                ----

                Carbs
                1.Item 1 - no. of carbs
                2.Item 2 - no. of carbs
                ----

                Fats
                1.Item 1 - no. of fats
                2.Item 2 - no. of fats
                ----

                1.Total Calories: XX
                2.Total Protein: XX
                3.Total Carbs: XX
                4.Total Fats: XX
                """

                response = get_gemini_response(input_prompt, image_data)
                st.subheader("Analysis Result:")
                st.write(response)
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.error("Please upload or capture an image to analyze.")

# Tab 3: Calorie Needs by Age
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

    # Calculate calorie needs
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

# Tab 4: Recipe Suggestions
with tab4:
    st.header("Recipe Suggestions 🍳")
    st.markdown("### Get customized recipes based on your preferences, goals, and ingredients!")

    # User Inputs
    st.subheader("1. Dietary Preferences")
    dietary_preferences = st.selectbox(
        "Select your dietary preference:",
        ["No Preference", "Vegetarian", "Vegan", "Non-vegetarians", "Keto", "Gluten-Free", "Low-Carb", "High-Protein", "Mediterranean"
        "Raw Food", "Low-Fat", "Dairy-Free"]
    )

    st.subheader("2. Health Goals")
    health_goal = st.selectbox(
        "Select your health goal:",
        ["No Specific Goal", "Weight Loss", "Muscle Gain", "Managing Diabetes", "Boosting Immunity", "Heart Health", "Improving Gut Health", "Blood Pressure", "Better Skin and Hair",
        "Improving Mental Health", "Pregnancy Diet", "Healthy Aging", "Managing Thyroid", "Improving Stamina"]
    )

    st.subheader("3. Ingredients Available at Home")
    ingredients = st.text_area(
        "Enter the ingredients you have (comma-separated):",
        placeholder="e.g., chicken, tomatoes, garlic, onions",
        key="ingredients_input"
    )

    # Suggest Recipes Button
    if st.button("🍽️ Suggest Recipes"):
        if ingredients.strip() == "":
            st.error("Please enter at least one ingredient.")
        else:
            # Generate a prompt for recipe suggestions
            recipe_prompt = f"""
            You are a master chef and nutritionist. Based on the following inputs:
            - Dietary Preference: {dietary_preferences}
            - Health Goal: {health_goal}
            - Ingredients: {ingredients}

            Suggest 6 healthy and delicious recipes. For each recipe, include:
            1. Recipe name
            2. Brief description
            3. Ingredients list
            4. Step-by-step cooking instructions
            5. Nutritional information (calories, protein, carbs, fats)
            """

            # Fetch recipe suggestions using Gemini API
            recipe_response = get_gemini_response(recipe_prompt)

            # Display the Response
            st.success("🎉 *Your Recipe Suggestions Are Ready!*")
            if recipe_response:
                st.write(recipe_response)
            else:
                st.error("Unable to fetch recipes. Please try again.")

with tab5:
    st.header("Dynamic Shopping List Planner 🛒")
    st.markdown("### Create a smart shopping list based on your planned meals!")

    # User Input: Planned Meals
    st.subheader("1. Select Planned Recipes")
    planned_recipes = st.text_area(
        "Enter the recipes you want to make (comma-separated):",
        placeholder="e.g., Chicken Curry, Vegan Pasta, Greek Salad",
        key="planned_recipes"
    )

    # User Input: Ingredients at Home
    st.subheader("2. Ingredients You Already Have")
    available_ingredients = st.text_area(
        "Enter the ingredients you have at home (comma-separated):",
        placeholder="e.g., rice, garlic, olive oil, tomatoes",
        key="available_ingredients"
    )

    # Generate Shopping List Button
    if st.button("🛍️ Generate Shopping List"):
        if not planned_recipes.strip():
            st.error("Please enter at least one planned recipe.")
        elif not available_ingredients.strip():
            st.error("Please enter the ingredients you have at home.")
        else:
            # Generate a prompt for shopping list creation
            shopping_list_prompt = f"""
            You are a kitchen assistant. Based on the following inputs:
            - Planned Recipes: {planned_recipes}
            - Ingredients at Home: {available_ingredients}

            Create a smart shopping list by identifying the missing ingredients needed to make the planned recipes.
            Categorize the ingredients into sections (e.g., Vegetables, Spices, Dairy, etc.) for easy shopping.
            """

            # Fetch shopping list using Gemini API
            shopping_list_response = get_gemini_response(shopping_list_prompt)

            # Display the Shopping List
            st.success("✅ *Your Smart Shopping List is Ready!*")
            if shopping_list_response:
                st.write(shopping_list_response)
            else:
                st.error("Unable to generate shopping list. Please try again.")