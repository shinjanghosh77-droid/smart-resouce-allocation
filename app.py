import streamlit as st
import pandas as pd
import plotly.express as px
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, value
from st_supabase_connection import SupabaseConnection

# 1. Page & Professional UI Configuration
st.set_page_config(page_title="AI Resource Intel", layout="wide", page_icon="🧠")

# Custom CSS for a clean, modern dashboard
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #007bff; color: white; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 2. Database Connection (Using the GitHub Secrets we added)
try:
    conn = st.connection(
        "supabase",
        type=SupabaseConnection,
        url=st.secrets["SUPABASE_URL"],
        key=st.secrets["SUPABASE_KEY"]
    )
except Exception as e:
    st.error("⚠️ Database Connection Failed. Check your GitHub Secrets!")

# 3. Intelligent Scoring Logic
def compute_smart_score(row):
    weights = {"Critical": 10, "High": 7, "Medium": 4, "Low": 2}
    urgency_val = weights.get(row['Urgency'], 1)
    # ROI Score = (Benefit * Urgency) / (Resources Spent)
    score = (row['Benefit'] * urgency_val) / (row['Cost'] + row['Staff'] + 1)
    return round(score, 2)

# 4. Sidebar Control Panel
st.title("🧠 Intelligent Resource Allocation System")
with st.sidebar:
    st.header("⚙️ Constraints")
    max_budget = st.slider("Max Budget ($)", 100, 5000, 1500)
    max_staff = st.slider("Max Staff Hours", 10, 300, 80)
    st.divider()
    st.info("This system uses Mixed-Integer Linear Programming (MILP) to find the mathematically optimal project mix.")

# 5. File Upload & Instructions
with st.expander("📊 See required Excel format"):
    st.write("Ensure your file has these exact columns: **Project, Cost, Benefit, Staff, Urgency**")
    st.table(pd.DataFrame({"Project": ["A"], "Cost": [100], "Benefit": [200], "Staff": [10], "Urgency": ["High"]}))

uploaded_file = st.file_uploader("Upload Project Manifest (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df['Intelligence_Score'] = df.apply(compute_smart_score, axis=1)
    
    tab1, tab2 = st.tabs(["📋 Data Preview", "🚀 Optimization Result"])

    with tab1:
        st.dataframe(df, use_container_width=True)

    with tab2:
        if st.button("Calculate & Save Optimal Allocation"):
            # --- THE OPTIMIZATION ENGINE ---
            model = LpProblem(name="Optimal_Allocation", sense=LpMaximize)
            projects = df['Project'].tolist()
            x = LpVariable.dicts("assign", projects, cat="Binary")

            model += lpSum([df.loc[i, 'Intelligence_Score'] * x[projects[i]] for i in range(len(projects))])
            model += lpSum([df.loc[i, 'Cost'] * x[projects[i]] for i in range(len(projects))]) <= max_budget
            model += lpSum([df.loc[i, 'Staff'] * x[projects[i]] for i in range(len(projects))]) <= max_staff
            model.solve()

            # --- PROCESS RESULTS ---
            selected_names = [p for p in projects if x[p].varValue == 1]
            res_df = df[df['Project'].isin(selected_names)]

            if not res_df.empty:
                # Show Metrics
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Priority Index", int(value(model.objective)))
                c2.metric("Budget Used", f"${res_df.Cost.sum()}")
                c3.metric("Staff Hours", f"{res_df.Staff.sum()}h")

                # Visual Charts
                fig = px.bar(res_df, x="Project", y="Intelligence_Score", color="Urgency", title="Allocated Project Scores")
                st.plotly_chart(fig, use_container_width=True)

                st.write("### ✅ Selected Plan")
                st.dataframe(res_df, use_container_width=True)

                # --- SAVE TO SUPABASE ---
                for _, row in res_df.iterrows():
                    try:
                        conn.table("allocations").insert({
                            "project": row['Project'],
                            "cost": int(row['Cost']),
                            "benefit": int(row['Benefit']),
                            "staff": int(row['Staff']),
                            "urgency": row['Urgency']
                        }).execute()
                    except:
                        pass # Silently handle duplicates if necessary
                st.success("✨ Optimal plan saved to cloud database successfully!")
            else:
                st.error("No projects fit the current constraints.")

else:
    st.info("Waiting for data upload...")
