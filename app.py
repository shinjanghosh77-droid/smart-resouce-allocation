import streamlit as st
import pandas as pd
import plotly.express as px
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, value

# 1. Advanced Configuration
st.set_page_config(page_title="AI Resource Intel", layout="wide")

# 2. Intelligent Scoring Engine (The "Smart" Part)
def compute_smart_score(row):
    """
    Heuristic: Weights Urgency and Impact against Resource Consumption.
    This simulates a decision-maker's logic.
    """
    weights = {"Critical": 10, "High": 7, "Medium": 4, "Low": 2}
    urgency_val = weights.get(row['Urgency'], 1)
    # ROI = (Impact * Urgency) / (Cost + Staff_Hours)
    score = (row['Benefit'] * urgency_val) / (row['Cost'] + row['Staff'] + 1)
    return round(score, 2)

st.title("🧠 Intelligent Resource Allocation System")
st.caption("Powered by MILP (Mixed-Integer Linear Programming) Optimization")

# 3. Sidebar - The "Control Room"
with st.sidebar:
    st.header("🛠️ Constraints")
    max_budget = st.slider("Max Budget ($)", 500, 5000, 1500)
    max_staff = st.slider("Max Staff Hours", 10, 200, 80)
    st.divider()
    st.markdown("### Why this framework?\n*Streamlit allows for **High-Fidelity Prototyping**, turning Python data models into interactive software instantly.*")

# 4. Data Handling
uploaded_file = st.file_uploader("Upload Project Manifest", type=["csv", "xlsx"])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    # Injecting Intelligence
    df['Intelligence_Score'] = df.apply(compute_smart_score, axis=1)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📥 Input Intelligence")
        st.dataframe(df, use_container_width=True)

    # 5. The Solver (The "Math" Part)
    model = LpProblem(name="Optimal_Allocation", sense=LpMaximize)
    projects = df['Project'].tolist()
    # Decision Variables: Binary (0 or 1)
    x = LpVariable.dicts("project", projects, cat="Binary")

    # Objective: Maximize Intelligence Score
    model += lpSum([df.loc[i, 'Intelligence_Score'] * x[projects[i]] for i in range(len(projects))])

    # Constraints
    model += lpSum([df.loc[i, 'Cost'] * x[projects[i]] for i in range(len(projects))]) <= max_budget
    model += lpSum([df.loc[i, 'Staff'] * x[projects[i]] for i in range(len(projects))]) <= max_staff

    model.solve()

    # 6. Results & Visualization
    selected_projects = [p for p in projects if x[p].varValue == 1]
    results_df = df[df['Project'].isin(selected_projects)]

    with col2:
        st.subheader("🚀 Optimized Selection")
        st.metric("Global Efficiency Score", f"{int(value(model.objective))}")
        st.dataframe(results_df, use_container_width=True)

    # 7. Impact Visualization (Heatmap)
    st.divider()
    st.subheader("📈 Decision Impact Visualization")
    fig = px.scatter(df, x="Cost", y="Benefit", size="Staff", color="Urgency",
                 hover_name="Project", title="Project Landscape (Bubble size = Staff Hours)")
    # Highlight selected ones
    fig.add_scatter(x=results_df['Cost'], y=results_df['Benefit'], mode='markers', 
                marker=dict(symbol='star', size=15, color='gold'), name='Optimized Pick')
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Please upload a CSV with: Project, Cost, Benefit, Staff, Urgency")
