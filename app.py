import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
import re

# --- 1. Page Config ---
st.set_page_config(page_title="Solomon Tensile Suite Pro", layout="wide")
st.title("Solomon Tensile Suite v2.8")
st.caption("Auto-Unit Scaling & Professional Batch Analysis")

# --- 2. Sidebar ---
st.sidebar.header("📏 Specimen Geometry")
thickness = st.sidebar.number_input("Thickness (mm)", value=2.0)
width = st.sidebar.number_input("Width (mm)", value=6.0)
gauge_length = st.sidebar.number_input("Gauge Length (mm)", value=25.0)
area = width * thickness 

st.sidebar.header("⚙️ Analysis Settings")
apply_zeroing = st.sidebar.checkbox("Apply Toe-Compensation", value=True)
ym_start = st.sidebar.slider("Modulus Start Strain (%)", 0.0, 5.0, 0.2)
ym_end = st.sidebar.slider("Modulus End Strain (%)", 0.1, 20.0, 1.0)

# --- 3. Robust Data Loader ---
def smart_load(file):
    try:
        raw_bytes = file.getvalue()
        content = raw_bytes.decode("utf-8", errors="ignore")
        lines = content.splitlines()
        
        # Skip headers until numeric data block starts
        start_row = 0
        for i, line in enumerate(lines):
            nums = re.findall(r"[-+]?\d*\.\d+|\d+", line)
            if len(nums) >= 2:
                start_row = i
                break
        
        sep = '\t' if '\t' in lines[start_row] else (',' if ',' in lines[start_row] else r'\s+')
        df = pd.read_csv(io.StringIO("\n".join(lines[start_row:])), sep=sep, engine='python', on_bad_lines='skip')
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return None

# --- 4. Main Engine ---
uploaded_files = st.file_uploader("Upload Samples", type=['csv', 'xlsx', 'txt'], accept_multiple_files=True)

if uploaded_files:
    all_results = []
    fig = go.Figure()

    for file in uploaded_files:
        df = smart_load(file)
        if df is None or df.empty: continue
        
        # Auto-detect Force and Displacement columns
        cols = df.columns.tolist()
        f_col = next((c for c in cols if any(k in c.lower() for k in ['load', 'force', 'n'])), cols[0])
        d_col = next((c for c in cols if any(k in c.lower() for k in ['ext', 'disp', 'mm', 'dist', 'pos'])), cols[1])
        
        df[f_col] = pd.to_numeric(df[f_col], errors='coerce')
        df[d_col] = pd.to_numeric(df[d_col], errors='coerce')
        df = df.dropna(subset=[f_col, d_col])

        # --- SMART UNIT SCALING ---
        # If max displacement is huge (e.g. 1120), it's likely already % strain or micrometers
        raw_disp = df[d_col].values
        
        # Logic: If raw displacement / gauge_length * 100 > 5000%, the unit is wrong.
        test_strain = (raw_disp / gauge_length) * 100
        if test_strain.max() > 2000:
            # Case A: Data was actually in micrometers
            strain = (raw_disp / 1000) / gauge_length * 100
            st.info(f"⚡ {file.name}: Scaling displacement from µm to mm.")
        elif raw_disp.max() > 100 and gauge_length < 50:
            # Case B: The column was already 'Strain %'
            strain = raw_disp
            st.info(f"⚡ {file.name}: Using column 2 as direct Strain %.")
        else:
            strain = test_strain
        
        stress = df[f_col] / area

        # --- Toe-Compensation & Yield ---
        mask_e = (strain >= ym_start) & (strain <= ym_end)
        
        if np.sum(mask_e) < 3:
            st.error(f"❌ {file.name}: Range mismatch. Strain found: 0 to {strain.max():.1f}%. Adjust sliders.")
            continue

        E_slope, intercept_y = np.polyfit(strain[mask_e], stress[mask_e], 1)
        
        if apply_zeroing:
            shift = -intercept_y / E_slope
            strain = strain - shift
            mask_pos = strain >= 0
            strain, stress = strain[mask_pos], stress[mask_pos]

        # 0.2% Offset Yield
        offset_line = E_slope * (strain - 0.2)
        idx_yield = np.where((stress - offset_line) < 0)[0]
        y_stress = stress.iloc[idx_yield[0]] if len(idx_yield) > 0 else np.nan

        all_results.append({
            "Sample": file.name,
            "Modulus (MPa)": round(E_slope * 100, 1),
            "Yield (MPa)": round(y_stress, 2),
            "UTS (MPa)": round(stress.max(), 2),
            "Elongation (%)": round(strain.iloc[-1], 2)
        })

        fig.add_trace(go.Scatter(x=strain, y=stress, name=file.name))

    st.plotly_chart(fig, use_container_width=True)
    if all_results:
        res_df = pd.DataFrame(all_results)
        st.subheader("📊 Batch Metrics")
        st.table(res_df.drop(columns='Sample').agg(['mean', 'std']).T)
        st.dataframe(res_df)
