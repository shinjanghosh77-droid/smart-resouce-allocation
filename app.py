import streamlit as st
import pandas as pd
import plotly.express as px
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, value

# 1. Page Configuration
st.set_page_config(page_title="SmartAllocator Pro", page_icon="💎", layout="wide")

# Custom CSS for a modern Look
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #007bff;
        color: white;
        font-weight: bold;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Smart Scoring Logic (The "Intelligence" factor)
def compute_smart_score(row):
    # Weights for Urgency
    weights = {"Critical": 10, "High": 7, "Medium": 4, "Low": 2}
    urgency_val = weights.get(row['Urgency'], 1)
    # Intelligence Score: (Benefit * Urgency) / Resources
    score = (row['Benefit'] * urgency_val) / (row['Cost'] + row['Staff'] + 1)
    return round(score, 2)

# 3. Header
st.title("💎 Smart Resource Allocation System")
st.markdown("---")

# 4. Sidebar - Control Panel
with st.sidebar:
    st.header("⚙️ Allocation Constraints")
    budget_limit = st.number_input("💰 Total Budget Capacity", min_value=0, value=500)
    staff_limit = st.number_input("👥 Total Staff Capacity", min_value=0, value=20)
    st.divider()
    st.info("This engine uses Linear Programming to find the mathematically optimal solution.")

# 5. File Upload & Instructions
with st.expander("📊 See required Excel format"):
    st.write("Ensure your file has these exact columns:")
    cols = st.columns(4)
    cols[0].code("Project")
    cols[1].code("Cost")
    cols[2].code("Benefit")
    cols[3].code("Urgency")
    st.caption("Urgency should be: Low, Medium, High, or Critical")

uploaded_file = st.file_uploader("📤 Upload Project Data (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # Load Data
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        
        # Validation
        required = ["Project", "Cost", "Benefit", "Staff", "Urgency"]
        if all(col in df.columns for col in required):
            
            # Apply Smart Logic
            df['Priority_Score'] = df.apply(compute_smart_score, axis=1)
            
            tab1, tab2 = st.tabs(["📊 Raw Data", "🚀 Optimized Result"])
            
            with tab1:
                st.dataframe(df, use_container_width=True)
            
            with tab2:
                if st.button("Run Smart Allocation Engine"):
                    # --- THE OPTIMIZATION BRAIN ---
                    model = LpProblem(name="Smart_Alloc", sense=LpMaximize)
                    project_vars = LpVariable.dicts("Select", df.Project, cat="Binary")
                    
                    # Objective: Maximize Priority Score
                    model += lpSum([df.Priority_Score[i] * project_vars[df.Project[i]] for i in df.index])
                    
                    # Constraints
                    model += lpSum([df.Cost[i] * project_vars[df.Project[i]] for i in df.index]) <= budget_limit
                    model += lpSum([df.Staff[i] * project_vars[df.Project[i]] for i in df.index]) <= staff_limit
                    
                    model.solve()

                    # Filter Results
                    selected_indices = [i for i in df.index if project_vars[df.Project[i]].varValue == 1]
                    res_df = df.iloc[selected_indices]

                    if not res_df.empty:
                        # Top Metrics
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Total Priority Index", f"📈 {int(value(model.objective))}")
                        m2.metric("Budget Used", f"${res_df.Cost.sum()}", f"of {budget_limit}")
                        m3.metric("Staff Used", f"{res_df.Staff.sum()}h", f"of {staff_limit}")

                        # Visualization
                        st.markdown("### 📊 Allocation Impact Chart")
                        fig = px.bar(res_df, x="Project", y="Priority_Score", color="Urgency",
                                   title="Selected Project Scores (Highest = Best ROI)")
                        st.plotly_chart(fig, use_container_width=True)

                        st.write("### ✅ Your Optimized Selection")
                        st.dataframe(res_df, use_container_width=True)
                        
                        # Download Button
                        csv = res_df.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 Download This Plan", data=csv, file_name="smart_allocation.csv", mime="text/csv")
                    else:
                        st.error("No projects fit! Increase your budget or staff limits.")
        else:
            st.error(f"Missing columns! Your file must have: {', '.join(required)}")
    except Exception as e:
        st.error(f"Error: {e}")
import google.generativeai as genai

# 1. Setup AI (Paste your Key in Streamlit Secrets first!)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model_ai = genai.GenerativeModel('gemini-pro')
except Exception:
    st.warning("AI Key not found. Add GOOGLE_API_KEY to Streamlit Secrets to enable AI insights.")

# 2. Add this inside your "if not res_df.empty:" block at the very end
st.divider()
st.subheader("🤖 AI Allocation Insights")

if st.button("Ask AI to Analyze This Plan"):
    # Build a prompt using your result data
    data_summary = res_df[['Project', 'Priority_Score', 'Urgency']].to_string()
    prompt = f"Analyze this resource allocation plan and tell me why it's efficient. Data: {data_summary}"
    
    with st.spinner("AI is thinking..."):
        response = model_ai.generate_content(prompt)
        st.write(response.text)
# --- Everything above stays the same ---

if st.button("Run Smart Allocation Engine"):
    # ... (Your existing optimization code that creates res_df) ...
    
    if not res_df.empty:
        # 1. Show your metrics and charts (existing code)
        st.metric("Total Priority Index", f"📈 {int(value(model.objective))}")
        # ... (other metrics and bar charts) ...

        # 2. THE AI SECTION (Must be inside this 'if not res_df.empty' block)
        st.divider()
        st.subheader("🤖 AI Strategic Consultant")
        
        try:
            # Prepare the data for Gemini
            data_summary = res_df[['Project', 'Priority_Score', 'Urgency']].to_string()
            prompt = f"As a strategic consultant, analyze why these specific projects were selected for allocation. Focus on the Priority Score and Urgency. Data: {data_summary}"
            
            with st.spinner("AI Consultant is analyzing the plan..."):
                genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
                model_ai = genai.GenerativeModel('gemini-pro')
                response = model_ai.generate_content(prompt)
                st.write(response.text)
        except Exception as e:
            st.info("💡 Note: To see AI insights, ensure GOOGLE_API_KEY is added to Streamlit Secrets.")

# --- End of code ---

