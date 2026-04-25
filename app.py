import streamlit as st
import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, value

st.set_page_config(page_title="Smart Allocator", page_icon="🚀")
st.title("🚀 Smart Resource Allocation")

# 1. Sidebar Configuration
st.sidebar.header("Settings")
budget_limit = st.sidebar.number_input("Total Budget", min_value=0, value=500)
staff_limit = st.sidebar.number_input("Staff Capacity", min_value=0, value=20)

# 2. File Uploader
uploaded_file = st.file_uploader("Upload your Project Data (CSV or Excel)", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    # Auto-detect file type
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.write("### 📋 Uploaded Data Preview", df.head())

        # Check for required columns
        required = ["Project", "Cost", "Benefit", "Staff"]
        if all(col in df.columns for col in required):
            
            if st.button("Run Smart Allocation"):
                # 3. Optimization Logic
                model = LpProblem(name="Resource_Optimization", sense=LpMaximize)
                project_vars = LpVariable.dicts("Select", df.Project, cat="Binary")

                # Objective: Maximize Benefit
                model += lpSum([df.Benefit[i] * project_vars[df.Project[i]] for i in df.index])

                # Constraints
                model += lpSum([df.Cost[i] * project_vars[df.Project[i]] for i in df.index]) <= budget_limit
                model += lpSum([df.Staff[i] * project_vars[df.Project[i]] for i in df.index]) <= staff_limit

                model.solve()

                # 4. Display Results
                selected = [df.iloc[i] for i in df.index if project_vars[df.Project[i]].varValue == 1]
                if selected:
                    results_df = pd.DataFrame(selected)
                    st.success(f"✅ Optimized Total Benefit: {value(model.objective)}")
                    st.write("### 🎯 Recommended Allocation", results_df)
                else:
                    st.warning("No projects fit within the current constraints.")
        else:
            st.error(f"Missing columns! Your file must have: {', '.join(required)}")
            
    except Exception as e:
        st.error(f"Error loading file: {e}")
else:
    st.info("Waiting for a file... Please upload a spreadsheet to start.")
