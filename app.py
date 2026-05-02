import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from groq import Groq
import os

# ---- GROQ CLIENT ----
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.set_page_config(page_title="AI SQL Agent", layout="wide")
st.title("🤖 AI Data Agent (CSV → SQL → Insights)")

# ---- FILE UPLOAD ----
uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])

if uploaded_file is not None:

    # ---- READ FILE ----
    try:
        if uploaded_file.name.endswith(".csv"):
            try:
                df = pd.read_csv(uploaded_file, encoding="utf-8")
            except:
                df = pd.read_csv(uploaded_file, encoding="latin1")
        else:
            df = pd.read_excel(uploaded_file)

        if df.empty or df.shape[1] == 0:
            st.error("⚠️ File is empty or invalid.")
            st.stop()

    except Exception as e:
        st.error("❌ Error reading file.")
        st.stop()

    st.success("✅ File loaded successfully!")

    # ---- SQLITE DATABASE ----
    conn = sqlite3.connect("data.db")
    df.to_sql("data", conn, if_exists="replace", index=False)

    # ---- PREVIEW ----
    st.subheader("📊 Data Preview")
    st.dataframe(df.head())

    # ---- QUESTION ----
    st.subheader("💬 Ask a question")
    user_question = st.text_input("Example: total sales by region")

    if user_question:

        schema = ", ".join(df.columns)

        prompt = f"""
        You are a SQL expert.

        Table name: data
        Columns: {schema}

        Convert the following question into a valid SQLite query.
        Only return SQL query.

        Question: {user_question}
        """

        try:
            # ---- GENERATE SQL ----
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}]
            )
            import re

          sql_query = response.choices[0].message.content.strip()
sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

            # ---- SAFETY CHECK ----
            if any(word in sql_query.lower() for word in ["drop", "delete", "update", "insert"]):
                st.error("⚠️ Unsafe query blocked!")
                st.stop()

            st.subheader("🧾 Generated SQL")
            st.code(sql_query, language="sql")

            # ---- EXECUTE ----
            result = pd.read_sql_query(sql_query, conn)

            st.subheader("📊 Result")
            st.dataframe(result)

            # ---- CHART CONTROL ----
            chart_type = st.selectbox(
                "Choose chart type",
                ["Auto", "Bar", "Line", "Scatter"]
            )

            # ---- VISUALIZATION ----
            if result.shape[1] >= 2:
                x_col = result.columns[0]
                y_col = result.columns[1]

                if chart_type == "Bar":
                    fig = px.bar(result, x=x_col, y=y_col)
                elif chart_type == "Line":
                    fig = px.line(result, x=x_col, y=y_col)
                elif chart_type == "Scatter":
                    fig = px.scatter(result, x=x_col, y=y_col)
                else:
                    if pd.api.types.is_numeric_dtype(result[y_col]):
                        fig = px.bar(result, x=x_col, y=y_col)
                    else:
                        fig = px.scatter(result, x=x_col, y=y_col)

                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Error: {e}")
