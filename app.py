import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, value

st.set_page_config(page_title="Smart Volunteer AI", page_icon="🤝", layout="wide")

# --- SMART LOGIC: PRIORITY SCORING ---
def calculate_priority(row):
    # Higher Score = Higher Priority
    # (Benefit * Urgency) / Cost
    urgency_map = {"Low": 1, "Medium": 2, "High": 3, "Critical": 5}
    score = (row['Benefit'] * urgency_map.get(row['Urgency'], 1)) / (row['Cost'] + 1)
    return round(score, 2)

st.title("🤝 Smart Volunteer Intelligence System")
st.markdown("---")

# --- SIDEBAR: MISSION CONTROL ---
with st.sidebar:
    st.header("⚙️ System Constraints")
    budget_limit = st.number_input("💰 Funding Budget", min_value=0, value=1000)
    staff_limit = st.number_input("👥 Volunteer Hours", min_value=0, value=100)
    selected_skill = st.multiselect("🎯 Required Skills", ["Tech", "Medical", "Education", "Manual"], default=["Tech", "Medical"])

# --- DATA INPUT ---
uploaded_file = st.file_uploader("📤 Upload Task Manifest (CSV/Excel)", type=["csv", "xlsx"])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    # --- THE "SMART" ENGINE ---
    # 1. Skill Filtering
    df['Skill_Match'] = df['Required_Skill'].apply(lambda x: x in selected_skill)
    # 2. Priority Scoring (The AI Decision Factor)
    df['Priority_Score'] = df.apply(calculate_priority, axis=1)
    
    tab1, tab2, tab3 = st.tabs(["📋 Task Inbox", "🧠 AI Decision Engine", "📈 Impact Analytics"])

    with tab1:
        st.write("### Incoming Tasks & Skill Matching")
        st.dataframe(df.style.highlight_max(axis=0, subset=['Priority_Score'], color='#90ee90'))

    with tab2:
        if st.button("🚀 Run Smart Allocation"):
            # Optimization based on Priority Score
            model = LpProblem(name="Smart_Match", sense=LpMaximize)
            project_vars = LpVariable.dicts("Assign", df.Project, cat="Binary")
            
            # Objective: Maximize Priority Score for matched skills
            model += lpSum([df.Priority_Score[i] * project_vars[df.Project[i]] for i in df.index if df.Skill_Match[i]])
            
            # Constraints
            model += lpSum([df.Cost[i] * project_vars[df.Project[i]] for i in df.index]) <= budget_limit
            model += lpSum([df.Staff[i] * project_vars[df.Project[i]] for i in df.index]) <= staff_limit

            model.solve()
            
            # Results
            res_df = df.iloc[[i for i in df.index if project_vars[df.Project[i]].varValue == 1]]
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.metric("Total Priority Index", f"{int(value(model.objective))}")
                st.metric("Tasks Automated", len(res_df))
            with col2:
                # Heatmap-style Priority Chart
                fig = px.treemap(res_df, path=['Urgency', 'Project'], values='Priority_Score', 
                                 color='Priority_Score', color_continuous_scale='RdYlGn')
                st.plotly_chart(fig, use_container_width=True)

            st.write("### ✅ Auto-Assigned Task Lifecycle")
            st.table(res_df[['Project', 'Urgency', 'Priority_Score', 'Required_Skill']])

    with tab3:
        st.write("### Resource Utilization Trend")
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name='Available', x=['Budget', 'Hours'], y=[budget_limit, staff_limit], marker_color='lightgray'))
        if 'res_df' in locals():
            fig2.add_trace(go.Bar(name='Used', x=['Budget', 'Hours'], y=[res_df.Cost.sum(), res_df.Staff.sum()], marker_color='blue'))
        st.plotly_chart(fig2)

else:
    st.info("Please upload a file with columns: Project, Cost, Benefit, Staff, Required_Skill, Urgency")
