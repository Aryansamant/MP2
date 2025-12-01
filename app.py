import os
import streamlit as st
import pandas as pd
import sqlite3
from dotenv import load_dotenv   # <-- IMPORTANT

from groq import Groq

from mini_project2 import create_connection, ex1, ex2, ex3

# ==============================
# LOAD .env VARIABLES
# ==============================
load_dotenv()  # <-- loads .env file

DB_PATH = "normalized.db"

APP_PASSWORD = os.getenv("APP_PASSWORD", "abc123")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY not found in environment. Please set it in .env")
    st.stop()

groq_client = Groq(api_key=GROQ_API_KEY)

# ==============================
# HELPER FUNCTIONS
# ==============================

@st.cache_resource
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

@st.cache_data
def get_customer_names():
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT DISTINCT FirstName || ' ' || LastName AS Name
        FROM Customer
        ORDER BY Name;
        """,
        conn,
    )
    return df["Name"].tolist()

def run_query(sql: str) -> pd.DataFrame:
    conn = get_connection()
    return pd.read_sql_query(sql, conn)

# ==============================
# UI: LOGIN
# ==============================

st.set_page_config(page_title="Sales Dashboard", layout="wide")

st.sidebar.title("Login")
password_input = st.sidebar.text_input("Password", type="password")

if password_input != APP_PASSWORD:
    st.sidebar.info("Enter the password to view the dashboard.")
    st.stop()

st.title("Sales Dashboard (normalized.db)")

# ==============================
# MAIN LAYOUT
# ==============================

left_col, right_col = st.columns(2)

# LEFT COLUMN
with left_col:
    st.subheader("Query controls")

    customers = get_customer_names()
    selected_customer = st.selectbox("Select a customer", customers)

    query_option = st.selectbox(
        "Select a predefined query",
        [
            "Customer orders (ex1)",
            "Customer total (ex2)",
            "All customers total (ex3)",
            "Custom SQL",
        ],
    )

    custom_sql = ""
    if query_option == "Custom SQL":
        custom_sql = st.text_area(
            "Write a custom SQL query on normalized.db",
            value="SELECT * FROM Customer LIMIT 5;",
            height=150,
        )

    run_button = st.button("Run query")

# RIGHT COLUMN
with right_col:
    st.subheader("Results")

    if run_button:
        if query_option == "Customer orders (ex1)":
            conn = get_connection()
            sql = ex1(conn, selected_customer)

        elif query_option == "Customer total (ex2)":
            conn = get_connection()
            sql = ex2(conn, selected_customer)

        elif query_option == "All customers total (ex3)":
            conn = ex3(get_connection())

        else:
            sql = custom_sql

        st.code(sql, language="sql")

        try:
            df = run_query(sql)
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Error running query: {e}")

# ==============================
# AI SECTION (Groq + LLaMA 3.3)
# ==============================

st.markdown("---")
st.header("AI: Natural Language → SQL (Groq)")

nl_question = st.text_input("Ask a question (e.g., 'Top 5 customers by total sales')")

if st.button("Ask AI"):
    if not nl_question.strip():
        st.warning("Please type a question.")
    else:
        schema_description = """
        Tables:
        - Region(RegionID, Region)
        - Country(CountryID, Country, RegionID)
        - Customer(CustomerID, FirstName, LastName, Address, City, CountryID)
        - ProductCategory(ProductCategoryID, ProductCategory, ProductCategoryDescription)
        - Product(ProductID, ProductName, ProductUnitPrice, ProductCategoryID)
        - OrderDetail(OrderID, CustomerID, ProductID, OrderDate, QuantityOrdered)
        """

        system_prompt = (
            "You are an assistant that writes SQL for a SQLite database. "
            "Return ONLY a valid SQL SELECT statement. "
            "Do not include explanations, comments, or markdown."
        )

        user_prompt = f"""
        {schema_description}

        Question:
        {nl_question}

        SQL:
        """

        try:
            with st.spinner("Generating SQL..."):
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0,
                )

                sql_from_ai = response.choices[0].message.content.strip()

        except Exception as e:
            st.error(f"Groq API error: {e}")
            st.stop()

        # clean accidental formatting
        if sql_from_ai.startswith("```"):
            sql_from_ai = sql_from_ai.strip("`").strip()
            if sql_from_ai.lower().startswith("sql"):
                sql_from_ai = sql_from_ai[3:].strip()

        st.subheader("Generated SQL")
        st.code(sql_from_ai, language="sql")

        try:
            df = run_query(sql_from_ai)
            st.subheader("Query result")
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"SQL execution error: {e}")
