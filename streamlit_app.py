# streamlit_app.py
import streamlit as st
from snowflake.snowpark.functions import col
from snowflake.snowpark import Session
import traceback

st.set_page_config(page_title="Customize Your Smoothie")
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom smoothie!")

# Step 1: Ask for name on order
name_on_order = st.text_input("Name on Smoothie")
st.write("The Name on your smoothie will be:", name_on_order)

# ---------------------------
# Obtain a Snowpark Session (multiple fallbacks)
# ---------------------------
session = None
errors = []

# 1) Try Streamlit Connections: st.connection("snowflake")
try:
    cnx = st.connection("snowflake")
    if cnx is not None:
        # If the connection object offers .session() like in Streamlit + Snowpark integration:
        try:
            session = cnx.session()
            st.info("Using Snowpark session from st.connection('snowflake').")
        except Exception:
            # maybe connection object itself behaves like a session, try using it
            session = cnx
            st.info("Using connection object returned by st.connection('snowflake').")
    else:
        errors.append("st.connection('snowflake') returned None.")
except Exception as e:
    errors.append("st.connection('snowflake') raised: " + repr(e))

# 2) Try Snowpark's get_active_session (runtime provides active session)
if session is None:
    try:
        from snowflake.snowpark.context import get_active_session
        try:
            active = get_active_session()
            if active is not None:
                session = active
                st.info("Using Snowpark get_active_session() provided by runtime.")
            else:
                errors.append("get_active_session() returned None.")
        except Exception as e:
            errors.append("get_active_session() raised: " + repr(e))
    except Exception as e:
        errors.append("Could not import get_active_session(): " + repr(e))

# 3) Fallback: Build Session from st.secrets['snowflake'] (good for local dev)
if session is None:
    sf_conf = st.secrets.get("snowflake", {})
    if sf_conf:
        try:
            session = Session.builder.configs(sf_conf).create()
            st.info("Created Snowpark Session from st.secrets['snowflake'].")
        except Exception as e:
            errors.append("Session.builder.create() failed: " + repr(e))
    else:
        errors.append("No st.secrets['snowflake'] found.")

# If still no session, show helpful debugging output and stop
if session is None:
    st.error(
        "Could not get a Snowpark Session. Please configure one of:\n"
        "- a Streamlit 'snowflake' connection (Streamlit Cloud: Manage app → Connections),\n"
        "- a runtime-provided active Snowpark session, or\n"
        "- st.secrets['snowflake'] for local dev."
    )
    with st.expander("Debug info (errors encountered)"):
        for e in errors:
            st.write("-", e)
        st.write("Traceback (last):")
        st.text(traceback.format_exc())
    st.stop()

# ---------------------------
# Load fruit names into a Python list
# ---------------------------
try:
    # if your table is in database/schema, ensure session's current database/schema are set,
    # or use fully qualified name like DB.SCHEMA.TABLE
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
        insert_sql = f"""
            INSERT INTO smoothies.public.orders(ingredients, name_on_order)
            VALUES ('{ingredients_string}', '{name_on_order}')
        """
        try:
            session.sql(insert_sql).collect()
            st.success(f"Your Smoothie is ordered! Thanks, {name_on_order}")
        except Exception as e:
            st.error(f"Failed to insert order: {e}")
