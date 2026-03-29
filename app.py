import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
import re

# --- 1. Page Config ---
st.set_page_config(page_title="Solomon Tensile Suite Pro", layout="wide")
st.title("Solomon Tensile Suite v3.3")
st.caption("Comprehensive Mechanical Property Reporting & Batch Analysis")

# --- 2. Sidebar Settings ---
st.sidebar.header("📝 Project Info")
project_name = st.sidebar.text_input("Project Name", "PBAT-PLA-Study")
batch_id = st.sidebar.text_input("Batch/Lot ID", "Sample-Set-01")

st.sidebar.header("📏 Specimen Geometry")
thickness = st.sidebar.number_input("Thickness (mm)", value=2.0)
width = st.sidebar.number_input("Width (mm)", value=6.0)
gauge_length = st.sidebar.number_input("Gauge Length (mm)", value=25.0)
area = width * thickness 
volume_mm3 = area * gauge_length

st.sidebar.header("⚙️ Unit & Analysis Settings")
manual_scale = st.sidebar.number_input("Displacement Scale Factor", value=0.001, format="%.3f")
apply_zeroing = st.sidebar.checkbox("Apply Toe-Compensation", value=True)
ym_start = st.sidebar.slider("Modulus Start Strain (%)", 0.0, 5.0, 0.2)
ym_end = st.sidebar.slider("Modulus End Strain (%)", 0.1, 20.0, 1.0)

# --- 3. Smart Data Loader ---
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

        # Core Units
        disp_mm = df[d_col].values * manual_scale
        raw_stress = df[f_col].values / area
        raw_strain = (disp_mm / gauge_length) * 100
        
        # Validation
        mask_e = (raw_strain >= ym_start) & (raw_strain <= ym_end)
        if np.sum(mask_e) < 3:
            st.warning(f"⚠️ {file.name}: Check units. Max Strain: {raw_strain.max():.1f}%")
            continue

        # Modulus & Zeroing
        E_slope, intercept_y = np.polyfit(raw_strain[mask_e], raw_stress[mask_e], 1)
        if apply_zeroing:
            shift = -intercept_y / E_slope
            strain = raw_strain - shift
            mask_pos = strain >= 0
            # FIX: Properly closed logic
            strain = strain[mask_pos]
            stress = raw_stress[mask_pos]
            force_vals = df[f_col].values[mask_pos]
            disp_vals = disp_mm[mask_pos]
        else:
            strain, stress = raw_strain, raw_stress
            force_vals = df[f_col].values
            disp_vals = disp_mm

        # 0.2% Offset Yield
        offset_line = E_slope * (strain - 0.2)
        idx_yield = np.where((stress - offset_line) < 0)[0]
        y_stress = stress[idx_yield[0]] if len(idx_yield) > 0 else np.nan
        y_strain = strain[idx_yield[0]] if len(idx_yield) > 0 else np.nan

        # Energy & Toughness (NumPy 2.0 compatible)
        try: 
            work_done_j = np.trapezoid(force_vals, disp_vals / 1000.0)
        except AttributeError: 
            work_done_j = np.trapz(force_vals, disp_vals / 1000.0)
        
        toughness = (work_done_j / (volume_mm3 * 1e-9)) / 1e6

        # --- Report Metrics ---
        all_results.append({
            "Sample": file.name,
            "Modulus (E) [MPa]": round(E_slope * 100, 1),
            "Yield Stress [MPa]": round(y_stress, 2),
            "Yield Strain [%]": round(y_strain, 2),
            "Stress @ Break [MPa]": round(stress[-1], 2),
            "Strain @ Break [%]": round(strain[-1], 2),
            "Work Done [J]": round(work_done_j, 4),
            "Toughness [MJ/m³]": round(toughness, 3)
        })

        fig.add_trace(go.Scatter(x=strain, y=stress, name=file.name))

    # --- 5. Visualization & Reporting ---
    st.plotly_chart(fig, use_container_width=True)
    
    if all_results:
        res_df = pd.DataFrame(all_results)
        
        st.subheader("📊 Statistical Analysis (Batch Mean ± SD)")
        stats_df = res_df.drop(columns='Sample').agg(['mean', 'std']).T
        st.table(stats_df.style.format("{:.2f}"))

        st.subheader("📋 Comprehensive Property Report")
        st.dataframe(res_df, hide_index=True)

        # Excel Export Engine
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            res_df.to_excel(writer, sheet_name='Sample Data', index=False)
            stats_df.to_excel(writer, sheet_name='Statistical Summary')
            
            # Formatting
            workbook = writer.book
            worksheet = writer.sheets['Sample Data']
            header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
            for col_num, value in enumerate(res_df.columns.values):
                worksheet.write(0, col_num, value, header_format)

        st.download_button(
            label=f"📥 Download Full {project_name} Report",
            data=output.getvalue(),
            file_name=f"{project_name}_{batch_id}_Final_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
