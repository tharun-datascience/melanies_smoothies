# streamlit_app.py (working version)

import streamlit as st
from snowflake.snowpark.functions import col

st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom smoothie!")

# Step 1: Ask for name on order
name_on_order = st.text_input("Name on Smoothie")
st.write("The Name on your smoothie will be:", name_on_order)

# ---------------------------
# OPTION A: Use Snowpark's get_active_session()
# ---------------------------
# Use this only if your runtime/environment exposes a Snowpark active session.
# You must import get_active_session from snowflake.snowpark.context
# Uncomment the following two lines if you have a Snowpark active session available:
#
# from snowflake.snowpark.context import get_active_session
# session = get_active_session()
#
# ---------------------------
# OPTION B (recommended for Streamlit Cloud): use Streamlit Connections
# ---------------------------
# Use this if you've configured a "snowflake" connection in Streamlit (Manage app -> Connections)
# This creates a connection object and gets a Snowpark session from it.
try:
    cnx = st.connection("snowflake")   # requires that you added a Snowflake connection in Streamlit
    session = cnx.session()
except Exception as e:
    st.error("Could not get Snowflake session via st.connection(). If running locally, make sure you have a Snowpark session available.")
    st.stop()

# ---------------------------
# Load fruit names into a Python list
# ---------------------------
try:
    # Pull only FRUIT_NAME column and collect to Python list
    snowpark_df = session.table("smoothies.public.fruit_options").select(col("FRUIT_NAME"))
    rows = snowpark_df.collect()  # returns list of Row objects
    fruit_options = [r["FRUIT_NAME"] for r in rows]
except Exception as e:
    st.error(f"Failed to load fruit options: {e}")
    st.stop()

# Step 3: Show multiselect for up to 5 ingredients
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    options=fruit_options,
    max_selections=5
)

# Step 4: Insert into orders only if ingredients are chosen AND name provided
if st.button("Submit Order"):
    if not name_on_order:
        st.warning("Please enter the name on the order.")
    elif not ingredients_list:
        st.warning("Please choose at least one ingredient.")
    else:
        ingredients_string = ", ".join(ingredients_list)

        # WARNING: using f-strings for SQL is simple but be careful with quoting in production.
        insert_sql = f"""
            INSERT INTO smoothies.public.orders(ingredients, name_on_order)
            VALUES ('{ingredients_string}', '{name_on_order}')
        """
        try:
            session.sql(insert_sql).collect()
            st.success(f"Your Smoothie is ordered! Thanks, {name_on_order}")
        except Exception as e:
            st.error(f"Failed to insert order: {e}")
