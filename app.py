import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io

# --- 1. Page Config ---
st.set_page_config(page_title="Solomon Tensile Suite Pro", layout="wide")

st.title("Solomon Tensile Suite v2.6")
st.caption("Standardized 0.2% Offset Yield & Robust Data Validation")

# --- 2. Sidebar ---
st.sidebar.header("📏 Specimen Geometry")
thickness = st.sidebar.number_input("Thickness (mm)", value=2.0)
width = st.sidebar.number_input("Width (mm)", value=6.0)
gauge_length = st.sidebar.number_input("Gauge Length (mm)", value=25.0)
area = width * thickness 

st.sidebar.header("⚙️ Analysis Settings")
apply_zeroing = st.sidebar.checkbox("Apply Toe-Compensation", value=True)
show_offset_line = st.sidebar.checkbox("Show 0.2% Offset Yield Line", value=True)
ym_start = st.sidebar.slider("Modulus Start Strain (%)", 0.0, 2.0, 0.2)
ym_end = st.sidebar.slider("Modulus End Strain (%)", 0.5, 5.0, 1.0)

# --- 3. Data Loader ---
def load_data(file):
    ext = file.name.split('.')[-1].lower()
    try:
        if ext == 'csv': return pd.read_csv(file)
        elif ext in ['xlsx', 'xls']: return pd.read_excel(file)
        elif ext == 'txt':
            content = file.getvalue().decode("utf-8")
            sep = '\t' if '\t' in content else ','
            return pd.read_csv(io.StringIO(content), sep=sep, skipinitialspace=True, on_bad_lines='skip')
    except: return None

# --- 4. Main Engine ---
uploaded_files = st.file_uploader("Upload Samples", type=['csv', 'xlsx', 'txt'], accept_multiple_files=True)

if uploaded_files:
    all_results = []
    fig = go.Figure()

    for file in uploaded_files:
        df = load_data(file)
        if df is None or df.empty: continue
        
        # Mapping columns (Force = 1st, Displacement = 2nd)
        f_col, d_col = df.columns[0], df.columns[1]
        df[f_col] = pd.to_numeric(df[f_col], errors='coerce')
        df[d_col] = pd.to_numeric(df[d_col], errors='coerce')
        df = df.dropna()

        # Raw Stress/Strain
        raw_stress = df[f_col] / area
        raw_strain = (df[d_col] / gauge_length) * 100
        
        # --- ROBUST VALIDATION ---
        mask_e = (raw_strain >= ym_start) & (raw_strain <= ym_end)
        
        # Check if we have at least 2 points to fit a line
        if np.sum(mask_e) < 2:
            st.warning(f"⚠️ Skipping {file.name}: No data found between {ym_start}% and {ym_end}% strain.")
            continue

        # --- Toe-Compensation & Modulus ---
        E_slope, intercept_y = np.polyfit(raw_strain[mask_e], raw_stress[mask_e], 1)
        strain_shift = -intercept_y / E_slope
        
        if apply_zeroing:
            final_strain = raw_strain - strain_shift
            mask_pos = final_strain >= 0
            final_strain, final_stress = final_strain[mask_pos], raw_stress[mask_pos]
        else:
            final_strain, final_stress = raw_strain, raw_stress

        # --- 0.2% Offset Yield Calculation ---
        offset_strain = final_strain - 0.2
        offset_stress_line = E_slope * offset_strain
        diff = final_stress - offset_stress_line
        idx_yield = np.where(diff < 0)[0]
        
        if len(idx_yield) > 0:
            y_idx = idx_yield[0]
            yield_stress = final_stress.iloc[y_idx]
            yield_strain = final_strain.iloc[y_idx]
        else:
            yield_stress, yield_strain = np.nan, np.nan

        # --- Toughness ---
        try: energy_j = np.trapezoid(final_stress * area, (final_strain / 100 * gauge_length) / 1000)
        except: energy_j = np.trapz(final_stress * area, (final_strain / 100 * gauge_length) / 1000)
        toughness = (energy_j / ((area * gauge_length) * 1e-9)) / 1e6

        # --- Results Store ---
        all_results.append({
            "Sample": file.name,
            "Modulus (MPa)": round(E_slope * 100, 2),
            "Yield Strength (MPa)": round(yield_stress, 2),
            "UTS (MPa)": round(final_stress.max(), 2),
            "Break Strain (%)": round(final_strain.iloc[-1], 2),
            "Toughness (MJ/m³)": round(toughness, 3)
        })

        # --- Plotting ---
        fig.add_trace(go.Scatter(x=final_strain, y=final_stress, name=f"{file.name}"))
        
        if show_offset_line and not np.isnan(yield_strain):
            line_x = np.linspace(0.2, yield_strain * 1.5, 20)
            line_y = E_slope * (line_x - 0.2)
            fig.add_trace(go.Scatter(x=line_x, y=line_y, name=f"Offset {file.name}", 
                                     line=dict(dash='dot', width=1), showlegend=False))
            fig.add_trace(go.Scatter(x=[yield_strain], y=[yield_stress], mode='markers', 
                                     name=f"Yield {file.name}", marker=dict(size=8)))

    # --- 5. Visualizations ---
    fig.update_layout(xaxis_title="Corrected Strain (%)", yaxis_title="Stress (MPa)", 
                      template="plotly_white", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
    
    if all_results:
        res_df = pd.DataFrame(all_results)
        st.subheader("📊 Research Statistics")
        st.table(res_df.drop(columns='Sample').agg(['mean', 'std']).T.style.format("{:.2f}"))
        st.dataframe(res_df, hide_index=True)

        # Excel Export
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            res_df.to_excel(writer, sheet_name='Summary', index=False)
        st.download_button("📥 Download Research Report", output.getvalue(), "Tensile_Analysis_v2.6.xlsx")
    else:
        st.error("No valid samples were processed. Please check your data ranges.")
