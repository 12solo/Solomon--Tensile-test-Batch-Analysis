import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
import requests

# --- 1. Page Configuration ---
st.set_page_config(page_title="Solomon Tensile Suite Pro", layout="wide")

# --- 2. Styling & Header ---
logo_url = "https://raw.githubusercontent.com/12solo/Tensile-test-extrapolator/main/logo%20s.png"
col_logo, col_text = st.columns([1, 5])
with col_logo:
    try: st.image(logo_url, width=120)
    except: st.header("🔬")
with col_text:
    st.title("Solomon Tensile Suite v2.0")
    st.caption("Research-Grade Multi-Sample Analysis & Extrapolation")

# --- 3. Sidebar: Global Research Parameters ---
st.sidebar.header("📁 Global Metadata")
project_name = st.sidebar.text_input("Project Name", "PBAT/PLA Blend Study")

with st.sidebar.expander("⚙️ Specimen Geometry (ASTM D638)", expanded=True):
    gauge_length = st.number_input("Initial Gauge Length (mm)", value=25.0)
    thickness = st.number_input("Thickness (mm)", value=2.0)
    width = st.number_input("Width (mm)", value=6.0)
    area = width * thickness
    st.caption(f"Calculated Area: {area:.2f} mm²")

with st.sidebar.expander("🎯 Analysis Settings"):
    target_def = st.number_input("Target Extrapolation (mm)", value=400.0)
    ym_range = st.slider("Modulus Strain Range (%)", 0.0, 5.0, (0.2, 1.0))
    apply_noise = st.checkbox("Simulate Plateau Noise", value=True)
    noise_lvl = st.number_input("Noise Std Dev (N)", value=0.05)

# --- 4. Batch File Uploader ---
st.subheader("📤 Data Import")
uploaded_files = st.file_uploader("Upload Multiple Samples (CSV/Excel)", type=['csv', 'xlsx'], accept_multiple_files=True)

if uploaded_files:
    all_results = []
    fig = go.Figure()

    # Process each file
    for file in uploaded_files:
        try:
            # Load data
            df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
            # Standardizing columns (Assumes Force is 1st, Def is 2nd - adjust as needed)
            f_col, d_col = df.columns[0], df.columns[1]
            
            # --- Extrapolation Logic ---
            ref_pts = 50
            last_n = df.tail(ref_pts)
            slope, intercept = np.polyfit(last_n[d_col], last_n[f_col], 1)
            d_stop, f_stop = df[d_col].iloc[-1], df[f_col].iloc[-1]
            
            # Generate extrapolation if needed
            if d_stop < target_def:
                d_ext = np.linspace(d_stop, target_def, 100)
                noise = np.random.normal(0, noise_lvl, len(d_ext)) if apply_noise else 0
                f_ext = f_stop + slope * (d_ext - d_stop) + noise
                
                df_ext = pd.DataFrame({f_col: f_ext, d_col: d_ext})
                df_full = pd.concat([df[[f_col, d_col]], df_ext], ignore_index=True)
            else:
                df_full = df

            # --- Engineering Calculations ---
            df_full['Stress'] = df_full[f_col] / area
            df_full['Strain'] = (df_full[d_col] / gauge_length) * 100
            
            # Young's Modulus (E)
            mask_e = (df_full['Strain'] >= ym_range[0]) & (df_full['Strain'] <= ym_range[1])
            E, _ = np.polyfit(df_full.loc[mask_e, 'Strain']/100, df_full.loc[mask_e, 'Stress'], 1)
            
            # Yield (Max Stress in early region)
            yield_idx = df_full[df_full['Strain'] < 40]['Stress'].idxmax()
            y_stress = df_full.loc[yield_idx, 'Stress']
            
            # Toughness (Area under curve in MJ/m^3)
            # Energy (J) = Integral of Force (N) wrt Displacement (m)
            energy_j = np.trapz(df_full[f_col], df_full[d_col] / 1000)
            volume_m3 = (area * gauge_length) * 1e-9
            toughness = (energy_j / volume_m3) / 1e6 # Convert to MJ/m^3

            # --- Store Metrics ---
            all_results.append({
                "Sample": file.name,
                "E (MPa)": round(E, 2),
                "Yield (MPa)": round(y_stress, 2),
                "Break Strain (%)": round(df_full['Strain'].iloc[-1], 1),
                "Toughness (MJ/m³)": round(toughness, 3)
            })

            # --- Add to Plotly ---
            fig.add_trace(go.Scatter(
                x=df_full['Strain'], 
                y=df_full['Stress'], 
                name=file.name,
                mode='lines',
                hovertemplate='%{x:.1f}%, %{y:.2f} MPa'
            ))

        except Exception as e:
            st.error(f"Error processing {file.name}: {e}")

    # --- 5. Visualization Dashboard ---
    col_plot, col_stats = st.columns([2, 1])

    with col_plot:
        st.subheader("Comparison Plot")
        fig.update_layout(
            xaxis_title="Strain (%)",
            yaxis_title="Engineering Stress (MPa)",
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            margin=dict(l=0, r=0, t=30, b=0),
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_stats:
        st.subheader("Batch Metrics")
        res_df = pd.DataFrame(all_results)
        st.dataframe(res_df, hide_index=True)
        
        # Download results as CSV
        csv = res_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Summary CSV", csv, "batch_summary.csv", "text/csv")

    # --- 6. Statistical Summary ---
    st.divider()
    st.subheader("📈 Statistical Analysis")
    if not res_df.empty:
        stats_summary = res_df.describe().loc[['mean', 'std']]
        st.table(stats_summary)

else:
    st.info("Please upload one or more tensile data files to begin analysis.")
