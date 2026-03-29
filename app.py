import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
import re

# --- 1. Page Config ---
st.set_page_config(page_title="Solomon Tensile Suite Pro", layout="wide")
st.title("Solomon Tensile Suite v3.0")
st.caption("Professional Batch Analysis | Toe-Compensation | Yield Detection")

# --- 2. Sidebar ---
st.sidebar.header("📝 Project Info")
project_name = st.sidebar.text_input("Project Name", "PBAT-PLA-Research")

st.sidebar.header("📏 Specimen Geometry")
thickness = st.sidebar.number_input("Thickness (mm)", value=2.0)
width = st.sidebar.number_input("Width (mm)", value=6.0)
gauge_length = st.sidebar.number_input("Gauge Length (mm)", value=25.0)
area = width * thickness 

st.sidebar.header("⚙️ Unit & Analysis Settings")
manual_scale = st.sidebar.number_input("Displacement Scale Factor", value=1.0, help="Multiply raw displacement by this value (e.g., 0.001 if data is in um)")
apply_zeroing = st.sidebar.checkbox("Apply Toe-Compensation", value=True)
ym_start = st.sidebar.slider("Modulus Start Strain (%)", 0.0, 5.0, 0.2)
ym_end = st.sidebar.slider("Modulus End Strain (%)", 0.1, 20.0, 1.0)

# --- 3. Robust Data Loader ---
def smart_load(file):
    try:
        raw_bytes = file.getvalue()
        content = raw_bytes.decode("utf-8", errors="ignore")
        lines = content.splitlines()
        
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
        
        cols = df.columns.tolist()
        f_col = next((c for c in cols if any(k in c.lower() for k in ['load', 'force', 'n'])), cols[0])
        d_col = next((c for c in cols if any(k in c.lower() for k in ['ext', 'disp', 'mm', 'dist', 'pos'])), cols[1])
        
        df[f_col] = pd.to_numeric(df[f_col], errors='coerce')
        df[d_col] = pd.to_numeric(df[d_col], errors='coerce')
        df = df.dropna(subset=[f_col, d_col])

        # Apply Scaling
        disp_mm = df[d_col].values * manual_scale
        raw_stress = df[f_col].values / area
        raw_strain = (disp_mm / gauge_length) * 100
        
        # Range Check
        mask_e = (raw_strain >= ym_start) & (raw_strain <= ym_end)
        if np.sum(mask_e) < 3:
            st.error(f"❌ {file.name}: Range mismatch. Max Strain: {raw_strain.max():.1f}%. Adjust Scale Factor.")
            continue

        # --- Modulus & Toe-Compensation ---
        E_slope, intercept_y = np.polyfit(raw_strain[mask_e], raw_stress[mask_e], 1)
        
        if apply_zeroing:
            shift = -intercept_y / E_slope
            strain = raw_strain - shift
            mask_pos = strain >= 0
            # FIX: Properly indexed filtering
            strain = strain[mask_pos]
            stress = raw_stress[mask_pos]
        else:
            strain, stress = raw_strain, raw_stress

        # 0.2% Offset Yield
        offset_line = E_slope * (strain - 0.2)
        idx_yield = np.where((stress - offset_line) < 0)[0]
        y_stress = stress[idx_yield[0]] if len(idx_yield) > 0 else np.nan

        # Toughness
        try: energy_j = np.trapezoid(stress * area, (strain / 100 * gauge_length) / 1000)
        except: energy_j = np.trapz(stress * area, (strain / 100 * gauge_length) / 1000)
        toughness = (energy_j / ((area * gauge_length) * 1e-9)) / 1e6

        # --- Results ---
        all_results.append({
            "Sample": file.name,
            "Modulus (MPa)": round(E_slope * 100, 1),
            "Yield (MPa)": round(y_stress, 2),
            "UTS (MPa)": round(np.max(stress), 2),
            "Break Strain (%)": round(strain[-1], 2),
            "Toughness (MJ/m³)": round(toughness, 3)
        })

        fig.add_trace(go.Scatter(x=strain, y=stress, name=file.name))

    # --- 5. Display Dashboard ---
    fig.update_layout(xaxis_title="Corrected Strain (%)", yaxis_title="Stress (MPa)", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)
    
    if all_results:
        res_df = pd.DataFrame(all_results)
        st.subheader(f"📊 {project_name} Statistics")
        st.table(res_df.drop(columns='Sample').agg(['mean', 'std']).T.style.format("{:.2f}"))
        st.dataframe(res_df, hide_index=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            res_df.to_excel(writer, sheet_name='Summary', index=False)
        st.download_button(f"📥 Download {project_name} Report", output.getvalue(), f"{project_name}_Analysis.xlsx")
