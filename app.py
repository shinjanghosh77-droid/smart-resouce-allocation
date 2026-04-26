import streamlit as st
import pandas as pd
import plotly.express as px
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, value
import google.generativeai as genai

# 1. Page Config
st.set_page_config(page_title="AI Smart Allocator", layout="wide", page_icon="🧠")

# 2. UI Styling
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #007bff; color: white; font-weight: bold; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 3. Smart Logic Function
def compute_smart_score(row):
    weights = {"Critical": 10, "High": 7, "Medium": 4, "Low": 2}
    urgency_val = weights.get(row['Urgency'], 1)
    score = (row['Benefit'] * urgency_val) / (row['Cost'] + row['Staff'] + 1)
    return round(score, 2)

# 4. Header & Sidebar
st.title("🧠 Intelligent Resource Allocation with Gemini AI")
with st.sidebar:
    st.header("⚙️ Constraints")
    budget_limit = st.number_input("💰 Total Budget", min_value=0, value=500)
    staff_limit = st.number_input("👥 Total Staff Hours", min_value=0, value=20)
    st.divider()
    st.info("System: MILP Solver + Google Gemini Pro")

# 5. File Upload
uploaded_file = st.file_uploader("Upload Project Data (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        
        # Data Prep
        df['Priority_Score'] = df.apply(compute_smart_score, axis=1)
        
        tab1, tab2 = st.tabs(["📊 Raw Data", "🚀 Optimized Result"])
        
        with tab1:
            st.dataframe(df, use_container_width=True)
        
        with tab2:
            if st.button("Run AI-Powered Allocation"):
                # --- OPTIMIZATION ENGINE ---
                model = LpProblem(name="Smart_Alloc", sense=LpMaximize)
                project_vars = LpVariable.dicts("Select", df.Project, cat="Binary")
                model += lpSum([df.Priority_Score[i] * project_vars[df.Project[i]] for i in df.index])
                model += lpSum([df.Cost[i] * project_vars[df.Project[i]] for i in df.index]) <= budget_limit
                model += lpSum([df.Staff[i] * project_vars[df.Project[i]] for i in df.index]) <= staff_limit
                model.solve()

                # Get Results
                selected_indices = [i for i in df.index if project_vars[df.Project[i]].varValue == 1]
                res_df = df.iloc[selected_indices]

                if not res_df.empty:
                    # Metrics & Chart
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Total Priority Index", f"📈 {int(value(model.objective))}")
                    m2.metric("Budget Used", f"${res_df.Cost.sum()}")
                    m3.metric("Staff Used", f"{res_df.Staff.sum()}h")

                    fig = px.bar(res_df, x="Project", y="Priority_Score", color="Urgency", title="Allocated Project Scores")
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(res_df, use_container_width=True)

                    # --- GOOGLE GEMINI AI SECTION ---
                    st.divider()
                    st.subheader("🤖 Gemini AI Strategic Analysis")
                    
                    if "GOOGLE_API_KEY" in st.secrets:
                        try:
                            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
                            gemini = genai.GenerativeModel('gemini-pro')
                            
                            data_text = res_df[['Project', 'Priority_Score', 'Urgency']].to_string()
                            prompt = f"Explain why this allocation is optimal for a business. Highlight the high priority projects. Data: {data_text}"
                            
                            with st.spinner("Gemini is analyzing..."):
                                response = gemini.generate_content(prompt)
                                st.write(response.text)
                        except Exception as e:
                            st.error(f"AI Error: {e}")
                    else:
                        st.warning("Google API Key not found in Secrets. Please add GOOGLE_API_KEY to see AI insights.")
                else:
                    st.error("No projects fit! Increase your budget or staff limits.")
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Please upload a file to start.")
# 5. Fixed Format Instructions (Always Visible)
st.subheader("📋 Step 1: Prepare Your Spreadsheet")
st.write("Your Excel or CSV file must have these exact column headers:")

# This creates the visual table on the frontend
sample_data = pd.DataFrame({
    "Project": ["Example A", "Example B"],
    "Cost": [100, 200],
    "Benefit": [250, 450],
    "Staff": [5, 10],
    "Urgency": ["High", "Medium"]
})
st.table(sample_data) # This displays the static table in the front

st.info("⚠️ Note: Column names are case-sensitive. Use plain numbers for Cost, Benefit, and Staff.")

# The file uploader follows right after
uploaded_file = st.file_uploader("📤 Now, upload your project data", type=["csv", "xlsx"])

