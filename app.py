import streamlit as st
import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, value

st.title("🚀 Smart Resource Allocation")

# Sidebar for constraints
budget_limit = st.sidebar.slider("Total Budget", 100, 1000, 300)
staff_limit = st.sidebar.slider("Staff Capacity", 5, 50, 15)

# Sample Data
data = {
    'Project': [f"Proj_{i}" for i in range(10)],
    'Cost': [45, 30, 85, 20, 50, 40, 65, 15, 35, 70],
    'Benefit': [80, 50, 150, 30, 90, 70, 110, 25, 60, 130],
    'Staff': [3, 2, 5, 1, 3, 2, 4, 1, 2, 4]
}
df = pd.DataFrame(data)
st.write("### Available Projects", df)

if st.button("Run Smart Allocation"):
    model = LpProblem(name="Resource_Optimization", sense=LpMaximize)
    project_vars = LpVariable.dicts("Select", df.Project, cat="Binary")

    # Objective: Maximize Benefit
    model += lpSum([df.Benefit[i] * project_vars[df.Project[i]] for i in df.index])

    # Constraints
    model += lpSum([df.Cost[i] * project_vars[df.Project[i]] for i in df.index]) <= budget_limit
    model += lpSum([df.Staff[i] * project_vars[df.Project[i]] for i in df.index]) <= staff_limit

    model.solve()

    # Display results
    selected = [df.iloc[i] for i in df.index if project_vars[df.Project[i]].varValue == 1]
    results_df = pd.DataFrame(selected)

    st.success(f"Optimized Total Benefit: {value(model.objective)}")
    st.write("### Selected Projects", results_df)
