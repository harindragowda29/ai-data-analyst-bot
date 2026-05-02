import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.set_page_config(page_title="AI SQL Agent", layout="wide")
st.title("🤖 AI Data Agent (CSV → SQL → Insights)")

# ---- FILE UPLOAD ----
uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])

if uploaded_file is not None:

    # ---- READ FILE SAFELY ----
    try:
        if uploaded_file.name.endswith(".csv"):
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except:
                df = pd.read_csv(uploaded_file, encoding='latin1')
        else:
            df = pd.read_excel(uploaded_file)

        if df.empty or df.shape[1] == 0:
            st.error("⚠️ File is empty or invalid.")
            st.stop()

    except Exception as e:
        st.error("❌ Error reading file.")
        st.stop()

    st.success("✅ File loaded successfully!")

    # ---- CREATE SQLITE DATABASE ----
    conn = sqlite3.connect("data.db")
    df.to_sql("data", conn, if_exists="replace", index=False)

    # ---- DATA PREVIEW ----
    st.subheader("📊 Data Preview")
    st.dataframe(df.head())

    # ---- USER INPUT ----
    st.subheader("💬 Ask a question about your data")
    user_question = st.text_input("Example: total sales by region")

    if user_question:

        schema = ", ".join(df.columns)

        # ---- PROMPT ----
        prompt = f"""
        You are a SQL expert.

        Table name: data
        Columns: {schema}

        Convert the following question into a valid SQLite query.
        Only return SQL query. No explanation.

        Question: {user_question}
        """

        try:
            # ---- GENERATE SQL ----
               
            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}]
            )

            sql_query = response.choices[0].message.content.strip()

            st.subheader("🧾 Generated SQL")
            st.code(sql_query, language="sql")

            # ---- EXECUTE SQL ----
            result = pd.read_sql_query(sql_query, conn)

            st.subheader("📊 Result")
            st.dataframe(result)

            # ---- VISUALIZATION ----
            if result.shape[1] >= 2:
                x_col = result.columns[0]
                y_col = result.columns[1]

                fig = px.bar(result, x=x_col, y=y_col, title="Auto Visualization")
                st.plotly_chart(fig)

        except Exception as e:
            st.error(f"❌ Error: {e}")
