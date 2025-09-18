# Import python packages
import streamlit as st
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col

# Write directly to the app
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write(
    """
    Choose the fruits you want in your custom smoothie!
    """
)

# Step 1: Ask for name on order
name_on_order = st.text_input("Name on Smoothie")
st.write("The Name on your smoothie will be:", name_on_order)

# Step 2: Get session
session = get_active_session()

# ✅ Use fruit_options table for ingredients
my_dataframe = session.table("smoothies.public.fruit_options").select(col("FRUIT_NAME"))
#fruit_list = [row["FRUIT_NAME"] for row in fruit_df.collect()]

# Step 3: Show multiselect for up to 5 ingredients
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    my_dataframe,
    max_selections=5
)

# Step 4: Insert into orders only if ingredients are chosen
#if ingredients and name_on_order:
 #   ingredients_string = ", ".join(ingredients)
 #   st.write("You selected: " + ingredients_string)

#    my_insert_stmt = f"""
  #      INSERT INTO smoothies.public.orders(ingredients, name_on_order)
      #  VALUES ('{ingredients_string}', '{name_on_order}')
  #  """
#
 #   if st.button("Submit Order"):
  #      session.sql(my_insert_stmt).collect()
   #     st.success(f"Your Smoothie is ordered! {name_on_order}")




if ingredients_list:
    ingredients_string = ''

    for fruit_choosen in ingredients_list:
        ingredients_string+= fruit_choosen +' '

    my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders(ingredients, name_on_order)
        VALUES ('{ingredients_string}', '{name_on_order}')
    """
    time_to_start = st.button("Submit Order")

    
