import streamlit as st
import pandas as pd
import plotly.express as px
import os
import openai

# ---- API KEY ----
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="AI Data Analyst Pro", layout="wide")

st.title("🤖 AI Data Analyst Pro")

# ---- SESSION STATE (Chat History) ----
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---- FILE UPLOAD ----
uploaded_files = st.file_uploader(
    "Upload CSV or Excel files",
    type=["csv", "xlsx"],
    accept_multiple_files=True
)

dfs = []

if uploaded_files:
    for file in uploaded_files:
        try:
            if file.name.endswith(".csv"):
                try:
                    df = pd.read_csv(file, encoding='utf-8')
                except:
                    df = pd.read_csv(file, encoding='latin1')
            else:
                df = pd.read_excel(file)

            if not df.empty:
                df["source_file"] = file.name
                dfs.append(df)

        except:
            st.warning(f"⚠️ Could not read {file.name}")

    if dfs:
        df = pd.concat(dfs, ignore_index=True)

        st.success("✅ Files loaded successfully")

        # ---- SIDEBAR FILTERS ----
        st.sidebar.header("🔍 Filters")

        selected_column = st.sidebar.selectbox("Select column", df.columns)

        if df[selected_column].dtype == "object":
            values = st.sidebar.multiselect(
                "Select values",
                df[selected_column].unique(),
                default=df[selected_column].unique()
            )
            df = df[df[selected_column].isin(values)]

        # ---- DATA PREVIEW ----
        st.subheader("📊 Data Preview")
        st.dataframe(df.head())

        # ---- AUTO INSIGHTS ----
        st.subheader("📌 AI Insights")

        if st.button("Generate Insights"):
            prompt = f"""
            Analyze this dataset with columns: {list(df.columns)}.
            Give key insights, trends, and observations.
            """

            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )

            st.write(response['choices'][0]['message']['content'])

        # ---- CHATBOT ----
        st.subheader("💬 Ask Questions")

        user_input = st.text_input("Ask something about your data:")

        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})

            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages
            )

            reply = response['choices'][0]['message']['content']
            st.session_state.messages.append({"role": "assistant", "content": reply})

        for msg in st.session_state.messages:
            st.write(f"**{msg['role'].capitalize()}:** {msg['content']}")

        # ---- VISUALIZATION ----
        st.subheader("📈 Smart Visualization")

        col1 = st.selectbox("X-axis", df.columns)
        col2 = st.selectbox("Y-axis", df.columns)

        chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Scatter"])

        if st.button("Generate Chart"):
            if chart_type == "Bar":
                fig = px.bar(df, x=col1, y=col2)
            elif chart_type == "Line":
                fig = px.line(df, x=col1, y=col2)
            else:
                fig = px.scatter(df, x=col1, y=col2)

            st.plotly_chart(fig)

        # ---- DOWNLOAD ----
        st.subheader("⬇️ Download Data")

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, "processed_data.csv", "text/csv")
