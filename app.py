import streamlit as st
import pandas as pd
import plotly.express as px
import openai

# ---- SET YOUR API KEY ----
openai.api_key = "YOUR_OPENAI_API_KEY"

st.set_page_config(page_title="AI Data Analyst Bot", layout="wide")

st.title("🤖 AI Data Analyst Bot")
st.write("Upload your CSV file and ask questions about your data!")

# ---- FILE UPLOAD ----
uploaded_file = st.file_uploader("Upload CSV", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # Handle CSV
        if uploaded_file.name.endswith(".csv"):
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except:
                try:
                    df = pd.read_csv(uploaded_file, encoding='latin1')
                except:
                    df = pd.read_csv(uploaded_file, sep=';')  # handle different delimiter

        # Handle Excel
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)

        # Check empty or invalid
        if df.shape[1] == 0:
            st.error("⚠️ File has no columns. Please upload a valid CSV/Excel file.")
            st.stop()

        if df.empty:
            st.error("⚠️ File is empty.")
            st.stop()

        st.success("✅ File loaded successfully!")
        st.dataframe(df.head())

    except Exception as e:
        st.error("❌ Unable to read file. Please upload a proper CSV or Excel file.")
        st.stop()
        # Check if empty
        if df.empty:
            st.error("⚠️ Uploaded file is empty!")
            st.stop()

        st.subheader("📊 Data Preview")
        st.dataframe(df.head())

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
        st.stop()

    # ---- USER QUESTION ----
    question = st.text_input("Ask a question about your data:")

    if question:
        prompt = f"""
        You are a data analyst. Given the dataset columns: {list(df.columns)}
        Answer the question: {question}
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )

            answer = response['choices'][0]['message']['content']
            st.subheader("💡 Answer")
            st.write(answer)

        except Exception as e:
            st.error(f"Error: {e}")

    # ---- AUTO VISUALIZATION ----
    st.subheader("📈 Auto Visualization")

    col1 = st.selectbox("Select X-axis", df.columns)
    col2 = st.selectbox("Select Y-axis", df.columns)

    chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Scatter"])

    if st.button("Generate Chart"):
        if chart_type == "Bar":
            fig = px.bar(df, x=col1, y=col2)
        elif chart_type == "Line":
            fig = px.line(df, x=col1, y=col2)
        else:
            fig = px.scatter(df, x=col1, y=col2)

        st.plotly_chart(fig)

    # ---- BASIC INSIGHTS ----
    st.subheader("📊 Auto Insights")

    st.write(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}")
    st.write("Missing Values:")
    st.write(df.isnull().sum())
