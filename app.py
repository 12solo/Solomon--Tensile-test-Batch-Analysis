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

# --- 2. Professional Logo & Header ---
logo_url = "https://raw.githubusercontent.com/12solo/Tensile-test-extrapolator/main/logo%20s.png"
col_logo, col_text = st.columns([1, 5])
with col_logo:
    try: st.image(logo_url, width=150) 
    except: st.header("🔬")
with col_text:
    st.title("Solomon Tensile Suite 2")
    st.markdown("""**Analytical Framework for Bio-Composite Strain Behavior** 🚀""")

# --- 3. Sidebar: Geometry & Calibration ---
st.sidebar.header("📏 Specimen Geometry")
thickness = st.sidebar.number_input("Thickness (mm)", value=4.0, step=0.1)
width = st.sidebar.number_input("Width (mm)", value=4.0, step=0.1)
gauge_length = st.sidebar.number_input("Initial Gauge Length (L0) [mm]", value=25.0, step=1.0)
area = width * thickness 

st.sidebar.header("⚙️ Data Calibration")
unit_input = st.sidebar.selectbox("Raw Displacement Unit", ["Millimeters (mm)", "Micrometers (um)", "Meters (m)"])
u_scale = {"Millimeters (mm)": 1.0, "Micrometers (um)": 0.001, "Meters (m)": 1000.0}[unit_input]
apply_zeroing = st.sidebar.checkbox("Apply Toe-Compensation (Shift to 0,0)", value=True)

st.sidebar.header("🎨 Plot Customization")
line_thickness = st.sidebar.slider("Line Thickness (Journal Plot)", 0.5, 5.0, 1.5, 0.5)
legend_pos = st.sidebar.selectbox("Legend Position", ["lower right", "upper right", "upper left", "lower left", "best", "outside"], index=0)
auto_scale = st.sidebar.checkbox("Enable Auto-Scale", value=True)
if not auto_scale:
    custom_x_max = st.sidebar.number_input("Manual X Max (Strain %)", value=10.0)
    custom_y_max = st.sidebar.number_input("Manual Y Max (Stress MPa)", value=50.0)

def clean_label(name):
    return re.sub(r'\.(txt|csv|xlsx|xls)$', '', name, flags=re.IGNORECASE)

# --- 6. Robust Data Loader ---
def smart_load(file):
    try:
        ext = file.name.split('.')[-1].lower()
        if ext == 'xlsx': return pd.read_excel(file, engine='openpyxl')
        content = file.getvalue().decode("utf-8", errors="ignore")
        lines = content.splitlines()
        start_row = next(i for i, l in enumerate(lines) if len(re.findall(r"[-+]?\d*\.\d+|\d+", l)) >= 2)
        sep = '\t' if '\t' in lines[start_row] else (',' if ',' in lines[start_row] else r'\s+')
        df = pd.read_csv(io.StringIO("\n".join(lines[start_row:])), sep=sep, engine='python', on_bad_lines='skip')
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return None

# --- 7. Main Engine ---
uploaded_files = st.file_uploader("Upload Samples", type=['csv', 'xlsx', 'txt'], accept_multiple_files=True)

if uploaded_files:
    all_results, plot_data_storage, yield_points_storage = [], {}, {}

    st.subheader("🛠️ Sample Configuration")
    with st.expander("⚡ Bulk Update"):
        b1, b2, b3, b4 = st.columns([2, 2, 2, 1])
        bulk_range = b1.slider("Global Modulus Range (%)", 0.0, 20.0, (0.2, 1.0), key="bulk_slider")
        bulk_method = b2.selectbox("Global Yield Method", ["Offset Method", "Departure from Linearity"], key="bulk_method")
        bulk_val = b3.slider("Global Sensitivity/Offset (%)", 0.0, 5.0, 0.2, 0.05, key="bulk_val")
        if b4.button("Apply to All"):
            for f in uploaded_files:
                st.session_state[f"range_{f.name}"] = bulk_range
                st.session_state[f"meth_{f.name}"] = bulk_method
                st.session_state[f"val_{f.name}"] = bulk_val
            st.rerun()

    for file in uploaded_files:
        df = smart_load(file)
        if df is None: continue
        cols = df.columns.tolist()
        f_col = st.sidebar.selectbox(f"Force ({file.name})", cols, key=f"f_{file.name}")
        d_col = st.sidebar.selectbox(f"Disp ({file.name})", cols, key=f"d_{file.name}")
        
        df_clean = df[[f_col, d_col]].apply(pd.to_numeric, errors='coerce').dropna()
        disp_all = df_clean[d_col].values * u_scale
        stress_all = df_clean[f_col].values / area
        strain_all = (disp_all / gauge_length) * 100

        peak_idx = np.argmax(stress_all)
        stress_raw, strain_raw = stress_all[:peak_idx + 1], strain_all[:peak_idx + 1]

        with st.expander(f"Adjust: {file.name}", expanded=False):
            custom_name = st.text_input("Display Name", value=clean_label(file.name), key=f"name_{file.name}")
            c1, c2, c3, prev_col = st.columns([1.2, 1.2, 1.2, 3])
            
            fit_range = c1.slider("Modulus Range (%)", 0.0, 20.0, (0.2, 1.0), key=f"range_{file.name}")
            yield_method = c2.selectbox("Yield Method", ["Offset Method", "Departure from Linearity"], key=f"meth_{file.name}")
            yield_val = c3.slider("Offset/Sensitivity (%)", 0.0, 5.0, 0.2, 0.05, key=f"val_{file.name}")
            
            mask_e = (strain_raw >= fit_range[0]) & (strain_raw <= fit_range[1])
            if np.sum(mask_e) >= 3:
                E_slope, intercept_y = np.polyfit(strain_raw[mask_e], stress_raw[mask_e], 1)
                shift = -intercept_y / E_slope if apply_zeroing else 0
                strain_plot, stress_plot = strain_raw - shift, stress_raw
                mask_pos = (strain_plot >= 0); strain_plot, stress_plot = strain_plot[mask_pos], stress_plot[mask_pos]
                
                # Force Origin Start
                strain_plot, stress_plot = np.insert(strain_plot, 0, 0), np.insert(stress_plot, 0, 0)
                plot_data_storage[custom_name] = (strain_plot, stress_plot)

                # Yield Detection
                if yield_method == "Offset Method":
                    offset_line = E_slope * (strain_plot - yield_val)
                    idx = np.where(stress_plot < offset_line)[0]
                else:
                    deviation = ((E_slope * strain_plot) - stress_plot) / (E_slope * strain_plot + 1e-9)
                    idx = np.where(deviation > (yield_val/10))[0]

                if len(idx) > 0:
                    y_stress, y_strain = round(stress_plot[idx[0]], 2), round(strain_plot[idx[0]], 2)
                    yield_points_storage[custom_name] = (y_strain, y_stress)
                else: y_stress, y_strain = "N/A", "N/A"

                fig_mini = go.Figure()
                fig_mini.add_trace(go.Scatter(x=strain_plot, y=stress_plot, name="Data"))
                if y_stress != "N/A":
                    fig_mini.add_trace(go.Scatter(x=[y_strain], y=[y_stress], mode='markers', marker=dict(size=10, color='orange')))
                fig_mini.update_layout(height=250, margin=dict(l=0,r=0,t=0,b=0), template="plotly_white")
                prev_col.plotly_chart(fig_mini, use_container_width=True)

                all_results.append({"Sample": custom_name, "Modulus (E) [MPa]": round(E_slope*100, 1), "Yield Stress [MPa]": y_stress, "Yield Strain [%]": y_strain, "Peak Stress [MPa]": round(stress_plot[-1], 2)})

    # --- 9. Final Visualizations ---
    if all_results:
        res_df = pd.DataFrame(all_results)
        st.divider()
        view_mode = st.radio("View Mode", ["Interactive", "Static (Journal TIFF)"], horizontal=True)
        colors = ['#000000', '#FF0000', '#0000FF', '#008000', '#A52A2A', '#800080']

        if view_mode == "Interactive":
            fig_main = go.Figure()
            for i, (name, (x, y)) in enumerate(plot_data_storage.items()):
                fig_main.add_trace(go.Scatter(x=x, y=y, name=name, line=dict(color=colors[i%len(colors)])))
                if name in yield_points_storage:
                    yx, yy = yield_points_storage[name]
                    fig_main.add_trace(go.Scatter(x=[yx], y=[yy], mode='markers', name=f"Yield {name}", marker=dict(color=colors[i%len(colors)], symbol='circle-open', size=12)))
            st.plotly_chart(fig_main, use_container_width=True)
        else:
            plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman"], "font.size": 12, "axes.linewidth": 1.5, "xtick.direction": "in", "ytick.direction": "in", "xtick.top": True, "ytick.right": True})
            fig, ax = plt.subplots(figsize=(7, 6), dpi=600)
            for i, (name, (x, y)) in enumerate(plot_data_storage.items()):
                color = colors[i%len(colors)]
                ax.plot(x, y, label=name, color=color, lw=line_thickness)
                if name in yield_points_storage:
                    yx, yy = yield_points_storage[name]
                    ax.scatter(yx, yy, facecolors='none', edgecolors=color, s=80, lw=1.5, zorder=5) # Yield Point Mark
            
            ax.set_xbound(lower=0); ax.set_ybound(lower=0)
            ax.margins(x=0, y=0)
            ax.set_xlabel('Strain (%)', fontweight='bold'); ax.set_ylabel('Stress (MPa)', fontweight='bold')
            ax.legend(loc=legend_pos, frameon=False)
            st.pyplot(fig)
            
            img_buf = io.BytesIO()
            fig.savefig(img_buf, format='png', dpi=600, bbox_inches='tight')
            img_buf.seek(0)
            pil_img = Image.open(img_buf)
            tiff_buf = io.BytesIO()
            pil_img.save(tiff_buf, format='TIFF', compression='tiff_lzw', dpi=(600, 600))
            st.download_button("📥 Download 600DPI TIFF", data=tiff_buf.getvalue(), file_name="Journal_Plot.tiff")

        st.subheader("📋 Results")
        st.dataframe(res_df, hide_index=True, use_container_width=True)
