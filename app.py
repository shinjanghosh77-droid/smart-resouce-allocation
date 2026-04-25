import streamlit as st
import pandas as pd
import plotly.express as px
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, value

# 1. Page Config & Styling
st.set_page_config(page_title="SmartAllocator Pro", page_icon="💎", layout="wide")

# Custom CSS for a modern "Dark/Glass" look
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #007bff;
        color: white;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover { background-color: #0056b3; color: white; }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Header Section
st.title("💎 Smart Resource Allocation")
st.markdown("---")

# 3. Sidebar - Clean Layout
with st.sidebar:
    st.image("https://flaticon.com", width=100)
    st.header("Control Panel")
    budget_limit = st.number_input("💰 Budget Capacity", min_value=0, value=500)
    staff_limit = st.number_input("👥 Staff Capacity", min_value=0, value=20)
    st.markdown("---")
    st.info("Adjust values above to see the allocation shift in real-time.")

# 4. Instructions Expander
with st.expander("📖 Step 1: Prepare your file"):
    st.write("Ensure your Excel/CSV has these exact columns:")
    cols = st.columns(4)
    cols[0].code("Project")
    cols[1].code("Cost")
    cols[2].code("Benefit")
    cols[3].code("Staff")
    st.caption("Upload your data below to begin.")

# 5. File Upload Area
uploaded_file = st.file_uploader("📤 Drag and drop your spreadsheet here", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        
        # Validation
        required = ["Project", "Cost", "Benefit", "Staff"]
        if all(col in df.columns for col in required):
            
            tab1, tab2 = st.tabs(["📊 Raw Data", "🚀 Optimized Result"])
            
            with tab1:
                st.dataframe(df, use_container_width=True)
            
            with tab2:
                if st.button("Calculate Best Allocation"):
                    # Optimization Engine
                    model = LpProblem(name="Smart_Alloc", sense=LpMaximize)
                    project_vars = LpVariable.dicts("Select", df.Project, cat="Binary")
                    model += lpSum([df.Benefit[i] * project_vars[df.Project[i]] for i in df.index])
                    model += lpSum([df.Cost[i] * project_vars[df.Project[i]] for i in df.index]) <= budget_limit
                    model += lpSum([df.Staff[i] * project_vars[df.Project[i]] for i in df.index]) <= staff_limit
                    model.solve()

                    # Process Results
                    selected_indices = [i for i in df.index if project_vars[df.Project[i]].varValue == 1]
                    res_df = df.iloc[selected_indices]

                    if not res_df.empty:
                        # Top Metrics
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Total Benefit", f"📈 {int(value(model.objective))}")
                        m2.metric("Budget Used", f"${res_df.Cost.sum()}", f"of {budget_limit}")
                        m3.metric("Staff Used", f"{res_df.Staff.sum()}", f"of {staff_limit}")

                        # Visualization
                        st.markdown("### 📊 Cost vs Benefit Analysis")
                        fig = px.bar(res_df, x="Project", y=["Cost", "Benefit"], barmode="group",
                                   color_discrete_sequence=['#ff4b4b', '#00d4ff'])
                        st.plotly_chart(fig, use_container_width=True)

                        st.write("### ✅ Final Selection")
                        st.dataframe(res_df, use_container_width=True)
                        
                        # Download Button
                        csv = res_df.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 Download Plan as CSV", data=csv, file_name="allocation_plan.csv", mime="text/csv")
                    else:
                        st.error("No projects fit! Increase your budget or staff limits.")
        else:
            st.error("Invalid Column Headers. Please check the 'Step 1' instructions.")
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.empty()
