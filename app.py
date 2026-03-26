import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from scipy import stats
from statsmodels.stats.power import TTestIndPower # New requirement
from datetime import datetime

# --- 1. Page Configuration ---
st.set_page_config(page_title="Solomon Research - Power Analysis", layout="wide")

# Initialize Groups
if 'group_a' not in st.session_state: st.session_state.group_a = {}
if 'group_b' not in st.session_state: st.session_state.group_b = {}

# --- 2. Professional Header ---
st.title("Solomon Tensile Suite: Research Edition")
st.markdown("**Statistical Power ($1 - β$) & Sample Size Optimization** 🚀")

# --- 3. Sidebar: Global Setup ---
st.sidebar.header("📂 Research Metadata")
area = st.sidebar.number_input("Cross-sectional Area (mm²)", value=16.0)
gauge_length = st.sidebar.number_input("Initial Gauge Length (mm)", value=50.0)

st.sidebar.header("🧪 Group Labels")
name_a = st.sidebar.text_input("Group A Label", "Control (PBAT)")
name_b = st.sidebar.text_input("Group B Label", "Experimental (PBAT/PLA)")

if st.sidebar.button("Reset All Groups"):
    st.session_state.group_a = {}; st.session_state.group_b = {}
    st.rerun()

# --- 4. Data Acquisition (Simplified for brevity) ---
# [Keep the data upload and metric extraction logic from v2.2 here]

# --- 5. T-Test & Power Analysis Engine ---
if st.session_state.group_a and st.session_state.group_b:
    st.divider()
    
    df_a = pd.DataFrame(st.session_state.group_a).T
    df_b = pd.DataFrame(st.session_state.group_b).T
    
    power_analysis_results = []
    analysis = TTestIndPower()

    for col in df_a.columns:
        # Calculate Means and Pooled Std Dev
        mean_a, mean_b = df_a[col].mean(), df_b[col].mean()
        std_a, std_b = df_a[col].std(), df_b[col].std()
        n_a, n_b = len(df_a), len(df_b)
        
        # Calculate Effect Size (Cohen's d)
        pooled_std = np.sqrt(((n_a - 1) * std_a**2 + (n_b - 1) * std_b**2) / (n_a + n_b - 2))
        effect_size = abs(mean_a - mean_b) / pooled_std
        
        # Calculate Observed Power
        observed_power = analysis.solve_power(effect_size=effect_size, nobs1=n_a, ratio=n_b/n_a, alpha=0.05)
        
        # Calculate Recommended N for 80% Power
        required_n = analysis.solve_power(effect_size=effect_size, power=0.80, alpha=0.05)
        
        power_analysis_results.append({
            "Property": col,
            "Effect Size (d)": effect_size,
            "Observed Power": observed_power,
            "Verdict": "💪 Strong" if observed_power > 0.8 else "⚠️ Underpowered",
            "Req. N (for 80% Power)": int(np.ceil(required_n))
        })

    # Display Power Table
    st.subheader("2. Power Analysis & Reliability")
    power_df = pd.DataFrame(power_analysis_results)
    st.dataframe(power_df.style.format({"Effect Size (d)": "{:.2f}", "Observed Power": "{:.2%}"}), use_container_width=True)

    # Visualization: Power Curve
    st.markdown("**Sample Size vs. Statistical Power**")
    fig, ax = plt.subplots(figsize=(10, 4))
    analysis.plot_power(dep_var='nobs', nobs=np.arange(2, 20), effect_size=[0.5, 0.8, 1.2], ax=ax)
    ax.set_title("Power Curves for Different Effect Sizes")
    st.pyplot(fig)

    st.info("💡 **PhD Tip:** If your power is below 80% (0.80), your 'Not Significant' result might just be because the sample size is too small. Check the 'Req. N' column to see how many more samples you should test.")
