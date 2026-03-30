import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import io
import re
import requests
import base64
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# --- 1. Page Configuration ---
st.set_page_config(page_title="Solomon Tensile Suite", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"], .stMarkdown, .stText, .stButton, .stSelectbox, .stTable {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Professional Header ---
logo_url = "https://raw.githubusercontent.com/12solo/Tensile-test-extrapolator/main/logo%20s.png"
col_logo, col_text = st.columns([1, 5])

with col_logo:
    try: st.image(logo_url, width=150) 
    except: st.header("🔬")

with col_text:
    st.title("Solomon Tensile Suite 2")
    st.markdown("""**Analytical Framework for Bio-Composite Strain Behavior** 🚀""")

# --- 3. Sidebar: Specimen & Calibration ---
st.sidebar.header("📝 Project Metadata")
project_name = st.sidebar.text_input("Research Topic", "PBAT-PLA-Biocomposites")

st.sidebar.header("📏 Specimen Geometry")
thickness = st.sidebar.number_input("Thickness (mm)", value=4.0, step=0.1)
width = st.sidebar.number_input("Width (mm)", value=4.0, step=0.1)
gauge_length = st.sidebar.number_input("Initial Gauge Length (L0) [mm]", value=25.0, step=1.0)
area = width * thickness 

st.sidebar.header("⚙️ Data Calibration")
unit_input = st.sidebar.selectbox("Raw Displacement Unit", ["Millimeters (mm)", "Micrometers (um)", "Meters (m)"])
scale_map = {"Millimeters (mm)": 1.0, "Micrometers (um)": 0.001, "Meters (m)": 1000.0}
u_scale = scale_map[unit_input]

apply_zeroing = st.sidebar.checkbox("Apply Toe-Compensation (Shift to 0,0)", value=True)

st.sidebar.header("🎨 Plot Customization")
line_thickness = st.sidebar.slider("Line Thickness (Journal Plot)", 0.5, 5.0, 2.5, 0.5)
legend_pos = st.sidebar.selectbox("Legend Position", ["lower right", "upper right", "upper left", "lower left", "best", "outside"], index=0)

auto_scale = st.sidebar.checkbox("Enable Auto-Scale", value=True)
if not auto_scale:
    custom_x_max = st.sidebar.number_input("Manual X Max (Strain %)", value=100.0)
    custom_y_max = st.sidebar.number_input("Manual Y Max (Stress MPa)", value=50.0)

def clean_label(name):
    return re.sub(r'\.(txt|csv|xlsx|xls)$', '', name, flags=re.IGNORECASE)

# --- 4. Loaders & Digitizer ---
class DigitizedFile:
    def __init__(self, name, df):
        self.name = name
        self.df = df
    def getvalue(self): return None 

def smart_load(file):
    if hasattr(file, 'df'): return file.df 
    try:
        ext = file.name.split('.')[-1].lower()
        if ext == 'xlsx': return pd.read_excel(file, engine='openpyxl')
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
    except Exception as e:
        st.error(f"Error loading {file.name}: {e}")
        return None

# --- 5. Main Input ---
input_mode = st.radio("Select Input Source", ["Standard Files (CSV/XLSX)", "Image Digitizer"], horizontal=True)
uploaded_files = []
if input_mode == "Standard Files (CSV/XLSX)":
    uploaded_files = st.file_uploader("Upload Samples", type=['csv', 'xlsx', 'txt'], accept_multiple_files=True, key="main_loader")

# --- 6. Core Processing Engine ---
if uploaded_files:
    all_results = []
    plot_data_storage = {} 
    yield_point_storage = {} 

    st.subheader("🛠️ Individual Sample Validation (Modulus Fit & Yield Search)")
    
    for file in uploaded_files:
        if file is None: continue
        df = smart_load(file)
        if df is None or df.empty: continue
        
        cols = df.columns.tolist()
        f_col = st.sidebar.selectbox(f"Force/Stress ({file.name})", cols, index=0, key=f"f_{file.name}")
        d_col = st.sidebar.selectbox(f"Disp/Strain ({file.name})", cols, index=1 if len(cols)>1 else 0, key=f"d_{file.name}")
        
        df_clean = df[[f_col, d_col]].apply(pd.to_numeric, errors='coerce').dropna()
        disp_all = df_clean[d_col].values * u_scale
        stress_all = df_clean[f_col].values / area
        strain_all = (disp_all / gauge_length) * 100

        peak_idx = np.argmax(stress_all)
        stress_raw = stress_all[:peak_idx + 1]
        strain_raw = strain_all[:peak_idx + 1]

        with st.expander(f"Analysis & Modulus Fit: {file.name}", expanded=False):
            custom_name = st.text_input("Display Name", value=clean_label(file.name), key=f"name_{file.name}")
            c_left, c_right = st.columns([1, 2])
            
            # Modulus Fit Range Selection
            fit_range = c_left.slider("Modulus Fit Range (%)", 0.0, 10.0, (0.2, 1.0), key=f"range_{file.name}")
            mask_fit = (strain_raw >= fit_range[0]) & (strain_raw <= fit_range[1])
            
            if np.sum(mask_fit) >= 3:
                E_slope, intercept = np.polyfit(strain_raw[mask_fit], stress_raw[mask_fit], 1)
                
                if apply_zeroing:
                    shift = -intercept / E_slope
                    strain_plot = strain_raw - shift
                    mask_pos = (strain_plot >= 0)
                    strain_plot, stress_plot = strain_plot[mask_pos], stress_raw[mask_pos]
                else:
                    strain_plot, stress_plot = strain_raw, stress_raw

                plot_data_storage[custom_name] = (strain_plot, stress_plot)
                
                # --- YIELD SEARCH (0.2% Offset) ---
                offset_strain = 0.2
                offset_line = E_slope * (strain_plot - offset_strain)
                idx_yield = np.where(stress_plot < offset_line)[0]
                
                if len(idx_yield) > 0:
                    y_stress, y_strain = stress_plot[idx_yield[0]], strain_plot[idx_yield[0]]
                    mat_class = "Ductile"
                    yield_point_storage[custom_name] = (y_strain, y_stress)
                else:
                    y_stress, y_strain = "N/A", "N/A"
                    mat_class = "Brittle"
                    yield_point_storage[custom_name] = (None, None)

                # Individual Plot with Modulus Fit
                fig_ind = go.Figure()
                fig_ind.add_trace(go.Scatter(x=strain_plot, y=stress_plot, name="Data", line=dict(color='#1f77b4')))
                
                # Show Modulus Fit line only here
                fit_x_vals = np.linspace(0, fit_range[1] * 2, 20)
                fit_y_vals = E_slope * fit_x_vals + (0 if apply_zeroing else intercept)
                fig_ind.add_trace(go.Scatter(x=fit_x_vals, y=fit_y_vals, name="Modulus Fit", line=dict(dash='dot', color='#d62728')))
                
                if mat_class == "Ductile":
                    fig_ind.add_trace(go.Scatter(x=[y_strain], y=[y_stress], mode='markers', marker=dict(size=10, color='#2ca02c'), name="Yield Point"))
                
                fig_ind.update_layout(height=300, margin=dict(l=0, r=0, t=20, b=0), template="plotly_white", title="Individual Modulus Fit Check")
                c_right.plotly_chart(fig_ind, use_container_width=True)

                all_results.append({
                    "Sample": custom_name, "Class": mat_class,
                    "Modulus (E) [MPa]": round(E_slope * 100, 1),
                    "Yield Stress [MPa]": y_stress, "Yield Strain [%]": y_strain,
                    "Stress @ Peak [MPa]": round(stress_plot[-1], 2), "Strain @ Peak [%]": round(strain_plot[-1], 2)
                })

    # --- 7. Summary Visualizations (CLEAN - No Fit Lines) ---
    if all_results:
        res_df = pd.DataFrame(all_results)
        st.divider()
        st.subheader("📊 Summary Batch Plot")
        
        distinct_20 = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf', '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5', '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d', '#9edae5']

        fig_main = go.Figure()
        for i, (name, data) in enumerate(plot_data_storage.items()):
            color = distinct_20[i % 20]
            fig_main.add_trace(go.Scatter(x=data[0], y=data[1], name=name, mode='lines', line=dict(width=line_thickness, color=color)))
            # Optional: Show Yield marker on summary plot
            ys, yst = yield_point_storage[name]
            if ys:
                fig_main.add_trace(go.Scatter(x=[ys], y=[yst], mode='markers', marker=dict(color='#2ca02c', size=8, line=dict(width=1, color='black')), showlegend=False))
        
        x_lim = res_df["Strain @ Peak [%]"].max() * 1.05 if auto_scale else custom_x_max
        y_lim = res_df["Stress @ Peak [MPa]"].max() * 1.1 if auto_scale else custom_y_max
        fig_main.update_layout(template="simple_white", xaxis=dict(title="Strain (%)", range=[0, x_lim]), yaxis=dict(title="Stress (MPa)", range=[0, y_lim]), height=600)
        st.plotly_chart(fig_main, use_container_width=True)

        # --- 8. Tables & Comparison ---
        st.divider()
        st.subheader("⚖️ Batch Comparison")
        control_sample = st.selectbox("Select Control Sample (Baseline)", res_df["Sample"].tolist(), key="ctrl_select")
        
        if control_sample:
            baseline = res_df[res_df["Sample"] == control_sample].iloc[0]
            comp_df = res_df.copy()
            for prop in ["Modulus (E) [MPa]", "Stress @ Peak [MPa]"]:
                comp_df[f"{prop.split(' ')[0]} Δ (%)"] = ((pd.to_numeric(comp_df[prop], errors='coerce') - float(baseline[prop])) / float(baseline[prop])) * 100
            
            st.dataframe(comp_df.style.format("{:+.1f}%", subset=[c for c in comp_df.columns if "Δ" in c]).background_gradient(cmap="RdYlGn", subset=[c for c in comp_df.columns if "Δ" in c]), hide_index=True, use_container_width=True)

        st.subheader("📋 Final Individual Records")
        st.dataframe(res_df, use_container_width=True, hide_index=True)

        # Export
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            res_df.to_excel(writer, sheet_name='Summary', index=False)
        st.download_button("📥 Download Excel Report", data=output.getvalue(), file_name=f"{project_name}_Full_Report.xlsx", key="final_dl")
