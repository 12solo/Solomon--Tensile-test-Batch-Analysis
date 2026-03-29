import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
import re
import requests

# --- 1. Page Configuration ---
st.set_page_config(page_title="Solomon Tensile Suite", layout="wide")

# --- 2. Professional Logo & Header ---
logo_url = "https://raw.githubusercontent.com/12solo/Tensile-test-extrapolator/main/logo%20s.png"
col_logo, col_text = st.columns([1, 5])
with col_logo:
    try: st.image(logo_url, width=150) 
    except: st.header("🔬")

with col_text:
    st.title("Solomon Tensile Suite 2")
    st.markdown("**Precision Mechanical Characterization Framework** 🚀")

# --- 3. Sidebar: Global Geometry ---
st.sidebar.header("📏 Global Geometry")
thickness = st.sidebar.number_input("Thickness (mm)", value=4.0, step=0.1)
width = st.sidebar.number_input("Width (mm)", value=4.0, step=0.1)
gauge_length = st.sidebar.number_input("Gauge Length (L0) [mm]", value=25.0, step=1.0)
area = width * thickness 

st.sidebar.header("⚙️ Global Units")
unit_input = st.sidebar.selectbox("Raw Displacement Unit", ["Millimeters (mm)", "Micrometers (um)", "Meters (m)"])
scale_map = {"Millimeters (mm)": 1.0, "Micrometers (um)": 0.001, "Meters (m)": 1000.0}
u_scale = scale_map[unit_input]

# --- 4. Robust Data Loader ---
def smart_load(file):
    try:
        raw_bytes = file.getvalue()
        content = raw_bytes.decode("utf-8", errors="ignore")
        lines = content.splitlines()
        start_row = 0
        for i, line in enumerate(lines):
            if len(re.findall(r"[-+]?\d*\.\d+|\d+", line)) >= 2:
                start_row = i
                break
        sep = '\t' if '\t' in lines[start_row] else (',' if ',' in lines[start_row] else r'\s+')
        df = pd.read_csv(io.StringIO("\n".join(lines[start_row:])), sep=sep, engine='python', on_bad_lines='skip')
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return None

# --- 5. Main Engine ---
uploaded_files = st.file_uploader("Upload Samples", type=['csv', 'xlsx', 'txt'], accept_multiple_files=True)

if uploaded_files:
    all_results = []
    fig_main = go.Figure()
    fig_modulus = go.Figure()

    # Create dynamic UI for each sample
    st.subheader("🛠️ Sample Configuration Manager")
    cols_ui = st.columns(len(uploaded_files)) if len(uploaded_files) > 0 else []

    for idx, file in enumerate(uploaded_files):
        df = smart_load(file)
        if df is None or df.empty: continue
        
        # Per-sample UI in a column or expander
        with st.expander(f"Adjust {file.name}", expanded=False):
            u_col1, u_col2 = st.columns(2)
            raw_cols = df.columns.tolist()
            f_col = u_col1.selectbox(f"Force Col", raw_cols, index=0, key=f"f_{file.name}")
            d_col = u_col2.selectbox(f"Disp Col", raw_cols, index=1, key=f"d_{file.name}")
            
            # Individual Modulus Control
            sample_ym = st.slider(f"Modulus Fit Range (%)", 0.0, 10.0, (0.2, 1.0), key=f"ym_{file.name}")
            sample_zero = st.checkbox("Apply Toe-Compensation", value=True, key=f"zero_{file.name}")

        # Data Processing
        df[f_col] = pd.to_numeric(df[f_col], errors='coerce')
        df[d_col] = pd.to_numeric(df[d_col], errors='coerce')
        df = df.dropna(subset=[f_col, d_col])

        disp_mm = df[d_col].values * u_scale
        stress_raw = df[f_col].values / area
        strain_raw = (disp_mm / gauge_length) * 100
        
        # Individual Modulus Fit
        mask_e = (strain_raw >= sample_ym[0]) & (strain_raw <= sample_ym[1])
        if np.sum(mask_e) < 3:
            st.warning(f"⚠️ {file.name}: Range Error. Insufficient data.")
            continue
            
        E_slope, intercept_y = np.polyfit(strain_raw[mask_e], stress_raw[mask_e], 1)
        
        # Toe-Compensation
        if sample_zero:
            shift = -intercept_y / E_slope
            strain = strain_raw - shift
            mask_pos = strain >= 0
            strain, stress = strain[mask_pos], stress_raw[mask_pos]
            f_final, d_final = df[f_col].values[mask_pos], disp_mm[mask_pos]
        else:
            strain, stress = strain_raw, stress_raw
            f_final, d_final = df[f_col].values, disp_mm

        # Metrics
        offset_line = E_slope * (strain - 0.2)
        idx_yield = np.where((stress - offset_line) < 0)[0]
        y_stress = stress[idx_yield[0]] if len(idx_yield) > 0 else np.nan
        y_strain = strain[idx_yield[0]] if len(idx_yield) > 0 else np.nan

        try: work_j = np.trapezoid(f_final, d_final / 1000.0)
        except: work_j = np.trapz(f_final, d_final / 1000.0)
        toughness = (work_j / ((area * gauge_length) * 1e-9)) / 1e6

        all_results.append({
            "Sample": file.name,
            "Modulus (E) [MPa]": round(E_slope * 100, 1),
            "Yield Stress [MPa]": round(y_stress, 2),
            "Strain @ Break [%]": round(strain[-1], 2),
            "Toughness [MJ/m³]": round(toughness, 3)
        })

        # Plotting
        fig_main.add_trace(go.Scatter(x=strain, y=stress, name=file.name))
        fig_modulus.add_trace(go.Scatter(x=strain, y=stress, name=file.name, opacity=0.4))
        
        fit_x = np.linspace(0, sample_ym[1] * 1.5, 20)
        fit_y = E_slope * fit_x + (0 if sample_zero else intercept_y)
        fig_modulus.add_trace(go.Scatter(x=fit_x, y=fit_y, name=f"Fit {file.name}", line=dict(dash='dot'), showlegend=False))

    # --- 6. Results & Plots ---
    st.divider()
    c1, c2 = st.columns([2, 1])
    with c1:
        fig_main.update_layout(xaxis_title="Strain (%)", yaxis_title="Stress (MPa)", template="plotly_white")
        st.plotly_chart(fig_main, use_container_width=True)
    with c2:
        fig_modulus.update_layout(xaxis_title="Strain (%)", yaxis_title="Stress (MPa)", xaxis_range=[0, 5], template="plotly_white")
        st.plotly_chart(fig_modulus, use_container_width=True)

    if all_results:
        res_df = pd.DataFrame(all_results)
        st.subheader("📊 Batch Report")
        st.dataframe(res_df, hide_index=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            res_df.to_excel(writer, sheet_name='Summary', index=False)
        st.download_button("📥 Export Report", output.getvalue(), "Solomon_Batch_Analysis.xlsx")
