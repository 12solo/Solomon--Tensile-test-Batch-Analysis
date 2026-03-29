import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io

# --- 1. Page Configuration ---
st.set_page_config(page_title="Solomon Tensile Suite Pro", layout="wide")

st.title("Solomon Tensile Suite v2.3")
st.caption("Empirical Batch Analysis for Material Science")

# --- 2. Sidebar: Specimen & Analysis Setup ---
st.sidebar.header("📏 Specimen Geometry")
thickness = st.sidebar.number_input("Thickness (mm)", value=2.0, step=0.1)
width = st.sidebar.number_input("Width (mm)", value=6.0, step=0.1)
gauge_length = st.sidebar.number_input("Gauge Length (mm)", value=25.0, step=1.0)
area = width * thickness 

st.sidebar.header("⚙️ Modulus Calculation")
ym_start = st.sidebar.slider("Start Strain (%)", 0.0, 2.0, 0.2)
ym_end = st.sidebar.slider("End Strain (%)", 0.5, 5.0, 1.0)

# --- 3. Data Loading Engine ---
def load_data(file):
    ext = file.name.split('.')[-1].lower()
    try:
        if ext == 'csv':
            return pd.read_csv(file)
        elif ext in ['xlsx', 'xls']:
            return pd.read_excel(file)
        elif ext == 'txt':
            content = file.getvalue().decode("utf-8")
            sep = '\t' if '\t' in content else ','
            return pd.read_csv(io.StringIO(content), sep=sep, skipinitialspace=True, on_bad_lines='skip')
    except Exception as e:
        st.error(f"Error reading {file.name}: {e}")
        return None

# --- 4. Main Application Logic ---
uploaded_files = st.file_uploader("Upload Samples (CSV, XLSX, TXT)", type=['csv', 'xlsx', 'txt'], accept_multiple_files=True)

if uploaded_files:
    all_results = []
    fig = go.Figure()

    for file in uploaded_files:
        df = load_data(file)
        if df is None or df.empty:
            continue
        
        # Mapping columns (Force = 1st, Displacement = 2nd)
        f_col, d_col = df.columns[0], df.columns[1]
        
        # Data Cleaning
        df[f_col] = pd.to_numeric(df[f_col], errors='coerce')
        df[d_col] = pd.to_numeric(df[d_col], errors='coerce')
        df = df.dropna(subset=[f_col, d_col])

        # --- Empirical Calculations ---
        df['Stress (MPa)'] = df[f_col] / area
        df['Strain (%)'] = (df[d_col] / gauge_length) * 100
        
        # 1. Young's Modulus (E)
        mask_e = (df['Strain (%)'] >= ym_start) & (df['Strain (%)'] <= ym_end)
        if mask_e.any():
            E, _ = np.polyfit(df.loc[mask_e, 'Strain (%)'] / 100, df.loc[mask_e, 'Stress (MPa)'], 1)
        else:
            E = 0
        
        # 2. Toughness (MJ/m³) - NumPy 2.0 Compatible
        try:
            energy_j = np.trapezoid(df[f_col], df[d_col] / 1000)
        except AttributeError:
            energy_j = np.trapz(df[f_col], df[d_col] / 1000)
            
        volume_m3 = (area * gauge_length) * 1e-9
        toughness = (energy_j / volume_m3) / 1e6

        # 3. Compile Metrics
        all_results.append({
            "Sample": file.name,
            "Modulus (MPa)": round(E, 2),
            "UTS (MPa)": round(df['Stress (MPa)'].max(), 2),
            "Strain @ Break (%)": round(df['Strain (%)'].iloc[-1], 2),
            "Toughness (MJ/m³)": round(toughness, 3)
        })

        # 4. Add to Interactive Plot
        fig.add_trace(go.Scatter(
            x=df['Strain (%)'], 
            y=df['Stress (MPa)'], 
            name=file.name,
            hovertemplate='Strain: %{x:.2f}%<br>Stress: %{y:.2f} MPa'
        ))

    # --- 5. Display Dashboard ---
    fig.update_layout(
        xaxis_title="Strain (%)",
        yaxis_title="Stress (MPa)",
        template="plotly_white",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    res_df = pd.DataFrame(all_results)
    
    if not res_df.empty:
        # Statistical Summary Table
        st.subheader("📊 Batch Statistics (Mean ± SD)")
        stats_summary = res_df.drop(columns='Sample').agg(['mean', 'std']).T
        st.table(stats_summary.style.format("{:.2f}"))
