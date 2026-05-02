import streamlit as st
import pandas as pd
import sqlite3
import openai
import plotly.express as px
import os

# ---- API KEY ----
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="AI SQL Agent", layout="wide")
st.title("🤖 AI Data Agent (CSV → SQL → Insights)")

# ---- FILE UPLOAD ----
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
    except:
        df = pd.read_csv(uploaded_file, encoding='latin1')

    st.success("✅ File loaded")

    # ---- CREATE SQLITE DB ----
    conn = sqlite3.connect("data.db")
    df.to_sql("data", conn, if_exists="replace", index=False)

    st.subheader("📊 Data Preview")
    st.dataframe(df.head())

    # ---- USER QUERY ----
    st.subheader("💬 Ask your question")
    user_question = st.text_input("Example: total sales by region")

    if user_question:
        schema = ", ".join(df.columns)

        prompt = f"""
        You are a SQL expert.

        Table name: data
        Columns: {schema}

        Convert the following question into a valid SQLite query:
        {user_question}

        Only return SQL query, no explanation.
        """

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        sql_query = response['choices'][0]['message']['content']

        st.subheader("🧾 Generated SQL")
        st.code(sql_query, language="sql")

        try:
            result = pd.read_sql_query(sql_query, conn)

            st.subheader("📊 Result")
            st.dataframe(result)

            # ---- VISUALIZATION ----
            if result.shape[1] >= 2:
                x_col = result.columns[0]
                y_col = result.columns[1]

                fig = px.bar(result, x=x_col, y=y_col)
                st.plotly_chart(fig)

        except Exception as e:
            st.error(f"❌ SQL Error: {e}")
