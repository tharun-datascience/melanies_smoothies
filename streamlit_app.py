# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import requests   # ✅ added for SmoothieFroot API

st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")

st.write("Choose the fruits you want in your custom smoothie!")

# Step 1: Ask for name on order
name_on_order = st.text_input("Name on Smoothie")
st.write("The Name on your smoothie will be:", name_on_order)

# Step 2: Get Snowflake session (CLOUD/LOCAL)
cnx = st.connection("snowflake")  # requires connection configured in Streamlit Cloud OR secrets.toml locally
session = cnx.session()

# ✅ Use fruit_options table for ingredients
my_dataframe = session.table("smoothies.public.fruit_options").select(col("FRUIT_NAME"))
fruit_list = [row["FRUIT_NAME"] for row in my_dataframe.collect()]

# Step 3: Show multiselect for up to 5 ingredients
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    fruit_list,
    max_selections=5
)

# ---------------------------
# ✅ SmoothieFroot API call
# ---------------------------
fruit_choice = st.text_input("Enter a fruit to get nutrition info:", "watermelon")

if st.button("Get Fruit Info"):
    try:
        response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{fruit_choice.lower()}")
        if response.status_code == 200:
            fruit_data = response.json()
            st.success(f"Here are the details for {fruit_choice.capitalize()}:")
            st.json(fruit_data)
        else:
            st.error(f"Could not fetch data for {fruit_choice}. Status code: {response.status_code}")
    except Exception as e:
        st.error(f"Error fetching data: {e}")

# Step 4: Insert order
if ingredients_list:
    ingredients_string = ", ".join(ingredients_list)

    my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders(ingredients, name_on_order)
        VALUES ('{ingredients_string}', '{name_on_order}')
    """

    if st.button("Submit Order"):
        session.sql(my_insert_stmt).collect()
        st.success(f"Your Smoothie is ordered! {name_on_order}")
