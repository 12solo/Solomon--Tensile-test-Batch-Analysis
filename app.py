import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
import re

# --- 1. Page Config ---
st.set_page_config(page_title="Solomon Tensile Suite Pro", layout="wide")
st.title("Solomon Tensile Suite v2.7")
st.caption("Advanced Header Parsing & Unit Scaling for .txt Files")

# --- 2. Sidebar ---
st.sidebar.header("📏 Specimen Geometry")
thickness = st.sidebar.number_input("Thickness (mm)", value=2.0)
width = st.sidebar.number_input("Width (mm)", value=6.0)
gauge_length = st.sidebar.number_input("Gauge Length (mm)", value=25.0)
area = width * thickness 

st.sidebar.header("⚙️ Analysis Settings")
ym_start = st.sidebar.slider("Modulus Start Strain (%)", 0.0, 5.0, 0.2, 0.1)
ym_end = st.sidebar.slider("Modulus End Strain (%)", 0.1, 10.0, 1.0, 0.1)

# --- 3. Smart Data Loader ---
def smart_load(file):
    ext = file.name.split('.')[-1].lower()
    try:
        if ext in ['xlsx', 'xls']:
            return pd.read_excel(file)
        
        # For CSV and TXT: Read raw lines to find where data starts
        raw_bytes = file.getvalue()
        content = raw_bytes.decode("utf-8", errors="ignore")
        lines = content.splitlines()
        
        # Find the first line that looks like data (contains multiple numbers)
        start_row = 0
        for i, line in enumerate(lines):
            # Check if line has at least 2 numbers separated by tab/comma/space
            nums = re.findall(r"[-+]?\d*\.\d+|\d+", line)
            if len(nums) >= 2:
                start_row = i
                break
        
        sep = '\t' if '\t' in lines[start_row] else (',' if ',' in lines[start_row] else r'\s+')
        
        # Reload only the data part
        df = pd.read_csv(io.StringIO("\n".join(lines[start_row:])), sep=sep, engine='python', on_bad_lines='skip')
        
        # Clean column names
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Fail: {file.name} -> {e}")
        return None

# --- 4. Main Engine ---
uploaded_files = st.file_uploader("Upload Samples", type=['csv', 'xlsx', 'txt'], accept_multiple_files=True)

if uploaded_files:
    all_results = []
    fig = go.Figure()

    for file in uploaded_files:
        df = smart_load(file)
        if df is None or df.empty: continue
        
        # Identify Columns by Keyword or Index
        cols = df.columns.tolist()
        f_col = next((c for c in cols if any(k in c.lower() for k in ['load', 'force', 'n'])), cols[0])
        d_col = next((c for c in cols if any(k in c.lower() for k in ['ext', 'disp', 'mm', 'dist'])), cols[1])
        
        df[f_col] = pd.to_numeric(df[f_col], errors='coerce')
        df[d_col] = pd.to_numeric(df[d_col], errors='coerce')
        df = df.dropna(subset=[f_col, d_col])

        # UNIT SCALING: Check if displacement is in meters (very small values)
        if df[d_col].max() < 0.1 and df[d_col].max() > 0:
            df[d_col] = df[d_col] * 1000  # Convert m to mm
            st.info(f"💡 {file.name}: Converted Displacement from meters to mm.")

        # Calculations
        stress = df[f_col] / area
        strain = (df[d_col] / gauge_length) * 100
        
        # Validating Range
        mask_e = (strain >= ym_start) & (strain <= ym_end)
        
        if np.sum(mask_e) < 5:
            st.error(f"❌ {file.name}: Range Error. Max Strain is {strain.max():.2f}%. Adjust sliders.")
            fig.add_trace(go.Scatter(x=strain, y=stress, name=f"ERR: {file.name}"))
            continue

        # Modulus Fit
        E_slope, inter = np.polyfit(strain[mask_e], stress[mask_e], 1)
        
        all_results.append({
            "Sample": file.name,
            "Modulus (MPa)": round(E_slope * 100, 1),
            "UTS (MPa)": round(stress.max(), 2),
            "Elongation (%)": round(strain.iloc[-1], 2)
        })

        fig.add_trace(go.Scatter(x=strain, y=stress, name=file.name))

    st.plotly_chart(fig, use_container_width=True)
    if all_results:
        st.dataframe(pd.DataFrame(all_results))
