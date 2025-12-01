import os
import sqlite3
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Groq client
from groq import Groq


from mini_project2 import (
    create_connection, ex1, ex2, ex3, ex4, ex5,
    ex6, ex7, ex8, ex9, ex10, ex11
)


st.set_page_config(page_title="Sales Dashboard", layout="wide")


load_dotenv()

DB_PATH = "normalized.db"

APP_PASSWORD = os.getenv("APP_PASSWORD", "tatu123")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


if not GROQ_API_KEY:
    st.error("GROQ_API_KEY not found in environment. Add it to .env as GROQ_API_KEY=your_key")
    st.stop()

groq_client = Groq(api_key=GROQ_API_KEY)


@st.cache_resource
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = 1")
    return conn

@st.cache_data(ttl=600)
def get_customer_names():
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            """
            SELECT DISTINCT FirstName || ' ' || LastName AS Name
            FROM Customer
            ORDER BY Name;
            """,
            conn,
        )
        return df["Name"].tolist()
    except Exception:
        return []

def run_query(sql: str) -> pd.DataFrame:
    conn = get_connection()
    return pd.read_sql_query(sql, conn)


st.sidebar.title("Login")
password_input = st.sidebar.text_input("Password", type="password")

if password_input != APP_PASSWORD:
    st.sidebar.info("Enter the password to view the dashboard.")
    st.stop()

st.title("Sales Dashboard (normalized.db)")


left_col, right_col = st.columns(2)

with left_col:
    st.subheader("Query controls")

    customers = get_customer_names()
    selected_customer = None
    if customers:
        selected_customer = st.selectbox("Select a customer", customers)
    else:
        st.warning("No customers found.")

    query_option = st.selectbox(
        "Select a predefined query",
        [
            "Customer orders (ex1)",
            "Customer total (ex2)",
            "All customers total (ex3)",
            "Region totals (ex4)",
            "Country totals (ex5)",
            "Rank countries by region (ex6)",
            "Top regional country (ex7)",
            "Quarterly by customer (ex8)",
            "Top 5 customers per quarter (ex9)",
            "Monthly ranking (ex10)",
            "MaxDaysWithoutOrder (ex11)",
            "Custom SQL",
        ],
    )

    custom_sql = ""
    if query_option == "Custom SQL":
        custom_sql = st.text_area(
            "Write a custom SQL query",
            value="SELECT * FROM Customer LIMIT 5;",
            height=150,
        )

    run_button = st.button("Run query")

with right_col:
    st.subheader("Results")

    if run_button:
        try:
            conn = get_connection()

            if query_option == "Customer orders (ex1)":
                sql = ex1(conn, selected_customer)
            elif query_option == "Customer total (ex2)":
                sql = ex2(conn, selected_customer)
            elif query_option == "All customers total (ex3)":
                sql = ex3(conn)
            elif query_option == "Region totals (ex4)":
                sql = ex4(conn)
            elif query_option == "Country totals (ex5)":
                sql = ex5(conn)
            elif query_option == "Rank countries by region (ex6)":
                sql = ex6(conn)
            elif query_option == "Top regional country (ex7)":
                sql = ex7(conn)
            elif query_option == "Quarterly by customer (ex8)":
                sql = ex8(conn)
            elif query_option == "Top 5 customers per quarter (ex9)":
                sql = ex9(conn)
            elif query_option == "Monthly ranking (ex10)":
                sql = ex10(conn)
            elif query_option == "MaxDaysWithoutOrder (ex11)":
                sql = ex11(conn)
            else:
                sql = custom_sql

            st.subheader("SQL")
            st.code(sql, language="sql")

            df = run_query(sql)
            st.subheader("Query result")
            st.dataframe(df, use_container_width=True)

        except Exception as e:
            st.error(f"Error running query: {e}")


st.markdown("---")
st.header("AI: Natural Language → SQL (Groq)")

nl_question = st.text_input("Ask a question (e.g., 'Top 5 customers by sales')")

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
            "Return ONLY a valid SQL SELECT statement."
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

        # Remove ⁠ sql blocks if any
        if sql_from_ai.startswith("  ⁠"):
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