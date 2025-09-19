# streamlit_app.py (use this robust session loader at top)
import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col
import traceback

st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom smoothie!")

# Get name
name_on_order = st.text_input("Name on Smoothie")
st.write("The Name on your smoothie will be:", name_on_order)

# --- Get a Snowpark Session (robust fallbacks) ---
session = None
errors = []

# 1) Try Streamlit Connection (Cloud) by name
try:
    cnx = st.connection("snowflake")  # only works if you added a Connection in Streamlit Cloud
    if cnx is not None:
        try:
            session = cnx.session()
            st.info("Using Snowpark session from st.connection('snowflake').")
        except Exception:
            # Sometimes the returned object is usable directly; try fallback
            session = cnx
            st.info("Using connection object returned by st.connection('snowflake').")
    else:
        errors.append("st.connection('snowflake') returned None.")
except Exception as e:
    errors.append("st.connection('snowflake') raised: " + repr(e))

# 2) Fallback: Build Session from st.secrets['snowflake'] (works locally or if you added secrets in Cloud)
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

# If still no session, show debug and stop
if session is None:
    st.error(
        "Could not get a Snowpark Session. Configure either:\n"
        "- a Streamlit Cloud Snowflake Connection (Manage app → Connections), or\n"
        "- st.secrets['snowflake'] (.streamlit/secrets.toml for local dev or Cloud Secrets)."
    )
    with st.expander("Debug info (errors encountered)"):
        for e in errors:
            st.write("-", e)
        st.write("Traceback (last):")
        st.text(traceback.format_exc())
    st.stop()

# --- rest of your app uses `session` safely ---
# Load fruit list
try:
    fruit_df = session.table("smoothies.public.fruit_options").select(col("FRUIT_NAME"))
    fruit_list = [r["FRUIT_NAME"] for r in fruit_df.collect()]
except Exception as e:
    st.error(f"Failed to load fruits: {e}")
    st.stop()

ingredients_list = st.multiselect("Choose up to 5 ingredients:", options=fruit_list, max_selections=5)

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
