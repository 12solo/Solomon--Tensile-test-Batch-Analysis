"""
Solomon Tensile Master Pro v4.7
─────────────────────────────────────────────────────────────────────────────
Integrated platform:
  Page 1 — Tensile Analysis      (Anti-Scribble Sorting + CSS Dropdown Fix)
  Page 2 — Ageing Trend Analysis (Fully restored Analytics & Export Engine)
─────────────────────────────────────────────────────────────────────────────
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io, re, os, base64, warnings
from PIL import Image

warnings.filterwarnings('ignore')

try:
    from scipy.optimize import curve_fit
    from scipy.stats import t as t_dist, f_oneway
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    from streamlit_drawable_canvas import st_canvas
    HAS_CANVAS = True
except ImportError:
    HAS_CANVAS = False

# ═══════════════════════════════════════════════════════════════════════════
# PAGE CONFIG & CSS
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Tensile Master Pro 4.7 | Solomon Scientific",
    page_icon="LOGO.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

:root {
    --navy:    #002244;  --navy2:   #003366;
    --gold:    #c9a84c;  --gold2:   #9c7a32;
    --white:   #ffffff;  --off:     #f7f9fc;
    --border:  #dde3ec;  --text:    #0f1923;  --muted: #5a6a7e;
    --red:     #c0392b;  --green:   #1e8449;  --amber: #d97706;
    --oven:    #e07b39;  --uv:      #5b4fcf;
    --font-h: 'Playfair Display', Georgia, serif;
    --font-m: 'IBM Plex Mono', 'Courier New', monospace;
    --font-b: 'IBM Plex Sans', 'Segoe UI', sans-serif;
}
html, body, [class*="css"] { font-family: var(--font-b); color: var(--text); }
.stApp { background: var(--white) !important; }
#MainMenu, .stDeployButton, footer { display:none !important; }
header { background:transparent !important; box-shadow:none !important; }
[data-testid="block-container"] { padding-top:0.75rem !important; }
div[data-testid="InputInstructions"], div[data-baseweb="tooltip"], [data-testid="stTooltipHoverTarget"] { display:none !important; }
[data-testid="stFileUploadDropzone"] svg, [data-testid="stFileUploadDropzone"] small { display:none !important; }
input[type="number"]::-webkit-inner-spin-button, input[type="number"]::-webkit-outer-spin-button { -webkit-appearance:none; }
input[type="number"] { -moz-appearance:textfield; }

[data-testid="stSidebar"] { background:var(--off) !important; border-right:1px solid var(--border) !important; }
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 {
    font-family:var(--font-b) !important; font-size:0.68rem !important; font-weight:700 !important; letter-spacing:0.15em !important;
    text-transform:uppercase !important; color:var(--navy2) !important; margin:0.75rem 0 0.15rem !important;
}
[data-testid="stSidebar"] hr { border:none !important; border-top:1px solid var(--border) !important; margin:0.6rem 0 !important; }

[data-testid="stSidebar"] input,[data-testid="stSidebar"] textarea,[data-testid="stSidebar"] select,
.stSelectbox>div>div,.stTextInput>div>div>input,.stNumberInput>div>div>input {
    background:var(--white) !important; border:1px solid var(--border) !important; border-radius:3px !important; color:var(--text) !important;
    font-family:var(--font-m) !important; font-size:0.82rem !important;
}
[data-testid="stFileUploadDropzone"] { background:var(--white) !important; border:1.5px dashed var(--border) !important; border-radius:3px !important; }
[data-testid="stFileUploadDropzone"]:hover { border-color:var(--gold) !important; }

/* ── ULTIMATE DROPDOWN VISIBILITY FIX ── */
[data-baseweb="popover"], div[role="listbox"], ul[data-baseweb="menu"] {
    background-color: #ffffff !important;
}
[data-baseweb="menu"] li, [data-baseweb="menu"] li *, div[role="option"], div[role="option"] * {
    color: #002244 !important;
    background-color: transparent !important;
}
[data-baseweb="menu"] li:hover, div[role="option"]:hover, div[role="option"]:focus {
    background-color: #f7f9fc !important;
}
[data-baseweb="menu"] li:hover *, div[role="option"]:hover * {
    color: #c9a84c !important;
}

.stButton>button {
    background:var(--off) !important; color:var(--navy2) !important; border:1px solid var(--border) !important; border-radius:3px !important;
    font-family:var(--font-b) !important; font-weight:600 !important; font-size:0.75rem !important; letter-spacing:0.07em !important;
    text-transform:uppercase !important; padding:0.45rem 0.9rem !important; transition:all 0.15s !important;
}
.stButton>button:hover { background:var(--border) !important; }
.stButton>button[kind="primary"] { background:linear-gradient(135deg,var(--gold2),var(--gold)) !important; color:var(--navy) !important; border:none !important; }
[data-testid="stDownloadButton"]>button { background:var(--off) !important; color:var(--navy2) !important; border:1px solid var(--border) !important; width:100% !important; }

[data-testid="stTabs"] [role="tablist"] { background:var(--off); border-bottom:2px solid var(--border); padding:0; gap:0; }
[data-testid="stTabs"] [role="tab"] { color:var(--muted) !important; font-family:var(--font-b) !important; font-size:0.74rem !important; font-weight:600 !important; letter-spacing:0.07em !important; text-transform:uppercase !important; padding:0.6rem 1.0rem !important; border-bottom:2px solid transparent !important; margin-bottom:-2px !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { border-bottom-color:var(--gold) !important; color:var(--navy) !important; background:var(--white) !important; }
[data-testid="stDataFrame"] { border:1px solid var(--border) !important; border-radius:3px !important; overflow:hidden !important; }
[data-testid="stDataFrame"] th { background:var(--off) !important; color:var(--navy2) !important; font-weight:700 !important; text-transform:uppercase !important; font-size:0.7rem !important; letter-spacing:0.06em !important; }
[data-testid="stDataFrame"] td { color:var(--text) !important; font-family:var(--font-m) !important; font-size:0.8rem !important; }
[data-testid="stExpander"] { border:1px solid var(--border) !important; border-radius:3px !important; background:var(--white) !important; }
[data-testid="stExpander"] summary p { color:var(--navy2) !important; font-weight:700 !important; font-size:0.82rem !important; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS & UI HELPERS
# ═══════════════════════════════════════════════════════════════════════════
PALETTE = [
    "#002244","#c9a84c","#c0392b","#2471a3","#1e8449",
    "#7d3c98","#d35400","#7f8c8d","#117a65","#a04000",
    "#1a5276","#e74c3c","#6c3483","#d97706","#922b21",
]
OVEN_SHADES = ["#e07b39","#c45e1e","#a04000","#7d2d00","#5a1e00"]
UV_SHADES   = ["#7e6fdf","#5b4fcf","#3d34b0","#2a228f","#1a1560"]
OVEN_COL, UV_COL = "#e07b39", "#5b4fcf"

AXIS = dict(mirror=True, ticks='inside', showline=True, linecolor='#000000', linewidth=2, showgrid=False, zeroline=False,
            title_font=dict(family="Times New Roman", size=15, color='#000000'), tickfont=dict(family="Times New Roman", size=12, color='#000000'))
JCFG = {'toImageButtonOptions': {'format':'png','filename':'Tensile_v4','scale':5}, 'displayModeBar':True,'displaylogo':False, 'modeBarButtonsToRemove':['select2d','lasso2d']}

AGEING_PROPS = {
    "E_MPa":("Modulus","MPa"), "UTS_MPa":("UTS","MPa"), "Yield_MPa":("Yield Stress","MPa"),
    "Elongation_pct":("Elongation at Break","%"), "Toughness_MJm3":("Toughness","MJ/m³"), "Resilience_MJm3":("Resilience","MJ/m³"),
}
AGEING_PROP_LABELS = {k: v[0] for k, v in AGEING_PROPS.items()}
AGEING_PROP_UNITS  = {k: v[1] for k, v in AGEING_PROPS.items()}

TENSILE_TO_AGEING = {
    "Modulus [MPa]": "E_MPa", "UTS [MPa]": "UTS_MPa", "Yield Stress [MPa]": "Yield_MPa",
    "Elongation at Break [%]": "Elongation_pct", "Toughness [MJ/m³]": "Toughness_MJm3", "Resilience [MJ/m³]": "Resilience_MJm3",
}
AGEING_DAYS = [0, 7, 14, 21, 28]

def get_b64(path):
    if os.path.exists(path):
        with open(path,'rb') as f: return base64.b64encode(f.read()).decode()
    return None

def clean_label(name):
    return re.sub(r'\.(txt|csv|xlsx|xls)$','',str(name),flags=re.IGNORECASE)

def section_hdr(text, icon="", color="#002244"):
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:0.55rem; background:linear-gradient(90deg,{color} 0%,{color}cc 100%);
        padding:0.5rem 1.1rem;border-radius:3px; border-left:4px solid #c9a84c;margin:1.1rem 0 0.75rem;">
      <span style="font-size:1rem;color:#f0f4fb;">{icon}</span>
      <span style="font-family:'IBM Plex Sans',sans-serif;font-size:0.74rem;font-weight:700;color:#f0f4fb;letter-spacing:0.15em;text-transform:uppercase;">{text}</span>
    </div>""", unsafe_allow_html=True)

def render_header(page_label=""):
    img = get_b64("LOGO.png")
    icon = (f'<img src="data:image/png;base64,{img}" style="height:50px;width:50px;object-fit:contain;border-radius:7px;background:#fff;flex-shrink:0;">') if img else '<div style="width:50px;height:50px;background:linear-gradient(135deg,#9c7a32,#c9a84c);border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:1.4rem;flex-shrink:0;">🔬</div>'
    badge = f'<span style="margin-left:1rem;background:rgba(201,168,76,0.2);color:#c9a84c;padding:0.2rem 0.75rem;border-radius:20px;font-size:0.68rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;border:1px solid rgba(201,168,76,0.4);">{page_label}</span>' if page_label else ""
    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;padding:1.2rem 2rem;background:#002244;border-radius:4px;margin-bottom:1.25rem;">
      <div style="display:flex;align-items:center;gap:1.2rem;">{icon}
        <div><div style="font-family:'Playfair Display',Georgia,serif;font-size:1.6rem;font-weight:700;color:#f0f4fb;line-height:1.1;">Solomon Tensile Master Pro<span style="color:#c9a84c;"> 4.7</span>{badge}</div>
        <div style="font-family:'IBM Plex Sans',sans-serif;font-size:0.66rem;color:#a8b4c8;letter-spacing:0.18em;text-transform:uppercase;margin-top:3px;">Advanced Mechanical &amp; Ageing Analysis Framework &nbsp;·&nbsp; Solomon Scientific</div></div>
      </div>
    </div>""", unsafe_allow_html=True)

def render_sidebar_brand():
    img = get_b64("LOGO.png")
    icon = (f'<img src="data:image/png;base64,{img}" style="width:44px;height:44px;object-fit:contain;border-radius:8px;background:#fff;margin:0 auto 0.5rem;display:block;">') if img else '<div style="width:44px;height:44px;background:linear-gradient(135deg,#9c7a32,#c9a84c);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1.2rem;margin:0 auto 0.5rem;">🔬</div>'
    st.markdown(f"""
    <div style="padding:0.75rem 0 0.3rem;text-align:center;">{icon}
      <div style="font-family:'IBM Plex Sans',sans-serif;font-size:0.58rem;color:#9c7a32;letter-spacing:0.2em;text-transform:uppercase;font-weight:700;">Solomon Scientific</div>
      <div style="font-family:'Playfair Display',Georgia,serif;font-size:0.9rem;font-weight:700;color:#002244;">Master Pro <span style="color:#c9a84c;">4.7</span></div>
    </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# FILE LOADING ENGINE
# ═══════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def _load_file_clean(file_bytes: bytes, file_name: str, skip_rows: int):
    try:
        ext = file_name.rsplit('.', 1)[-1].lower()
        if ext in ['xlsx', 'xls']:
            return pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl', skiprows=skip_rows)
        content = file_bytes.decode("utf-8", errors="ignore")
        lines = content.splitlines()
        if skip_rows >= len(lines): return None
        header_line = lines[skip_rows]
        sep = '\t' if '\t' in header_line else (';' if ';' in header_line else ',')
        df = pd.read_csv(io.StringIO(content), sep=sep, skiprows=skip_rows, engine='python', on_bad_lines='skip')
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception:
        return None

def smart_load(file, skip_rows):
    if hasattr(file, 'df'): return file.df
    df = _load_file_clean(file.getvalue(), file.name, skip_rows)
    if df is None: st.error(f"Could not parse {file.name}.")
    return df

# ═══════════════════════════════════════════════════════════════════════════
# DATA PROCESSING ENGINE
# ═══════════════════════════════════════════════════════════════════════════
def process_sample(strain_raw, stress_raw, fit_range, yield_method, yield_val, apply_zeroing):
    if len(strain_raw) < 8: return None
    peak_idx = int(np.argmax(stress_raw))
    stress = stress_raw[:peak_idx+1].astype(float).copy()
    strain = strain_raw[:peak_idx+1].astype(float).copy()
    mask_e = (strain >= fit_range[0]) & (strain <= fit_range[1])
    if np.sum(mask_e) < 3:
        n_fb = max(3, len(strain)//10)
        mask_e = np.zeros(len(strain), bool); mask_e[:n_fb] = True
    try: E_slope, intercept_y = np.polyfit(strain[mask_e], stress[mask_e], 1)
    except Exception: return None
    if E_slope <= 0: return None
    
    if apply_zeroing:
        shift = -intercept_y / E_slope
        strain = strain - shift
        pos = strain >= 0
        if not np.any(pos): return None
        strain, stress = strain[pos], stress[pos]
        if len(strain) > 0 and strain[0] > 1e-6:
            strain = np.insert(strain, 0, 0.0); stress = np.insert(stress, 0, 0.0)
        mask_e2 = (strain >= fit_range[0]) & (strain <= fit_range[1])
        if np.sum(mask_e2) >= 3:
            E_slope, _ = np.polyfit(strain[mask_e2], stress[mask_e2], 1)
            
    E_MPa = E_slope * 100.0
    if yield_method == "0.2% Offset Method":
        off_line = E_slope * (strain - yield_val)
        iy_arr = np.where((stress < off_line) & (strain >= yield_val))[0]
    else:
        theoretical = E_slope * strain
        with np.errstate(divide='ignore', invalid='ignore'):
            dev = np.where(theoretical > 0, np.abs(theoretical-stress)/theoretical, 0.0)
        iy_arr = np.where((dev > yield_val/100.0) & (strain > 0.1))[0]
        
    if len(iy_arr) > 0: iy = int(iy_arr[0]); y_stress = float(stress[iy]); y_strain = float(strain[iy])
    else: y_stress = y_strain = np.nan
        
    eps_frac = strain / 100.0
    true_strain = np.log(1.0 + eps_frac); true_stress = stress * (1.0 + eps_frac)
    h_n = h_K = h_r2 = np.nan
    if not np.isnan(y_strain) and y_strain < strain[-1]:
        pm = strain >= y_strain; ts_p = true_stress[pm]; te_p = true_strain[pm]
        v = (ts_p > 0) & (te_p > 0)
        if v.sum() >= 4:
            try:
                lx = np.log(te_p[v]); ly = np.log(ts_p[v])
                c = np.polyfit(lx, ly, 1); h_n = float(c[0]); h_K = float(np.exp(c[1]))
                res = ly - np.polyval(c, lx); ss_tot = np.sum((ly-ly.mean())**2)
                h_r2 = float(1 - np.sum(res**2)/ss_tot) if ss_tot > 0 else np.nan
            except Exception: pass
            
    secant = {}
    for ts in [0.25, 0.5, 1.0, 2.0, 5.0, 10.0]:
        if ts <= strain[-1] and ts > 0: secant[ts] = round(float(np.interp(ts, strain, stress)) / (ts/100.0), 1)
            
    try: toughness = float(np.trapezoid(stress, strain/100.0))
    except AttributeError: toughness = float(np.trapz(stress, strain/100.0))
    resilience = float(y_stress**2/(2.0*E_MPa)) if (not np.isnan(y_stress) and E_MPa > 0) else np.nan
    ductility_idx = float(strain[-1]/y_strain) if (not np.isnan(y_strain) and y_strain > 0) else np.nan
    fit_x = np.array([0.0, fit_range[1]*2.5]); fit_y = E_slope * fit_x
    
    return dict(
        strain=strain, stress=stress, true_strain=true_strain, true_stress=true_stress, E_MPa=round(E_MPa,1), E_slope=E_slope,
        y_stress=round(y_stress,2) if not np.isnan(y_stress) else np.nan, y_strain=round(y_strain,3) if not np.isnan(y_strain) else np.nan,
        uts=round(float(stress.max()),2), stress_break=round(float(stress[-1]),2), strain_break=round(float(strain[-1]),3),
        toughness=round(toughness,4), resilience=round(resilience,5) if not np.isnan(resilience) else np.nan,
        ductility_idx=round(ductility_idx,2) if not np.isnan(ductility_idx) else np.nan,
        h_n=round(h_n,3) if not np.isnan(h_n) else np.nan, h_K=round(h_K,2) if not np.isnan(h_K) else np.nan,
        h_r2=round(h_r2,4) if not np.isnan(h_r2) else np.nan, secant=secant, fit_x=fit_x, fit_y=fit_y, mat_class="Brittle" if np.isnan(y_stress) else "Ductile",
    )

def compute_weibull(uts_values):
    arr = np.array([v for v in uts_values if not np.isnan(v) and v > 0])
    n = len(arr)
    if n < 3: return None
    s = np.sort(arr); P = (np.arange(1,n+1)-0.3)/(n+0.4)
    y = np.log(np.log(1.0/(1.0-P))); x = np.log(s)
    try: slope, intercept = np.polyfit(x, y, 1)
    except Exception: return None
    m = slope; sigma_0 = np.exp(-intercept/m)
    fx = np.linspace(x.min(), x.max(), 80); fy = slope*fx + intercept
    res_w = y - np.polyval([slope,intercept],x); ss_tot = np.sum((y-y.mean())**2)
    r2 = float(1 - np.sum(res_w**2)/ss_tot) if ss_tot > 0 else 0.0
    sigma_90 = sigma_0 * (-np.log(0.10))**(1.0/m) if m > 0 else np.nan
    return dict(m=round(m,2), sigma_0=round(sigma_0,2), r2=round(r2,4), sigma_90=round(sigma_90,2) if not np.isnan(sigma_90) else np.nan, n=n, x=x, y=y, fx=fx, fy=fy, P=P, sorted_uts=s)

def compute_mean_curve(results_dict):
    if len(results_dict) < 2: return None
    min_max = min(r["strain"][-1] for r in results_dict.values())
    if min_max <= 0: return None
    grid = np.linspace(0, min_max, 400)
    stacked = np.array([np.interp(grid,r["strain"],r["stress"]) for r in results_dict.values()])
    return dict(strain=grid, mean=stacked.mean(0), std=stacked.std(0), upper=stacked.mean(0)+stacked.std(0), lower=np.maximum(stacked.mean(0)-stacked.std(0),0))

def generate_journal_fig(results_dict, sample_colors, settings):
    plt.rcParams.update({"font.family":"serif","font.serif":["Times New Roman"],"font.size":12,"axes.linewidth":1.5,"xtick.direction":"in","ytick.direction":"in","xtick.major.size":6,"ytick.major.size":6,"xtick.minor.size":3,"ytick.minor.size":3,"xtick.top":True,"ytick.right":True,"xtick.minor.visible":True,"ytick.minor.visible":True})
    fig, ax = plt.subplots(figsize=(7,6), dpi=600)
    lw = settings.get("lw",2.0)
    for name, r in results_dict.items():
        ax.plot(r["strain"],r["stress"],label=name, color=sample_colors.get(name,"#002244"),lw=lw,solid_capstyle='round')
    if settings.get("show_mean") and len(results_dict) >= 2:
        mc = compute_mean_curve(results_dict)
        if mc:
            ax.plot(mc["strain"],mc["mean"],'k--',lw=max(lw*0.7,1.0),label="Mean",zorder=5)
            ax.fill_between(mc["strain"],mc["lower"],mc["upper"],alpha=0.12,color='#555',label="±1 SD")
    ax.set_xbound(lower=0); ax.set_ybound(lower=0)
    if not settings.get("auto_scale",True): ax.set_xlim(0,settings["x_max"]); ax.set_ylim(0,settings["y_max"])
    ax.set_xlabel("Strain (%)",fontweight="bold",labelpad=8); ax.set_ylabel("Stress (MPa)",fontweight="bold",labelpad=8)
    loc = settings.get("legend_pos","lower right")
    if loc == "outside": ax.legend(loc="upper left",bbox_to_anchor=(1.02,1),frameon=False,fontsize=10); fig.tight_layout(rect=[0,0,0.79,1])
    else: ax.legend(loc=loc,frameon=False,fontsize=10); fig.tight_layout()
    return fig

# ═══════════════════════════════════════════════════════════════════════════
# AGEING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def fit_degradation_models(days, retention):
    days = np.array(days, dtype=float); ret = np.array(retention, dtype=float); valid = ret > 0
    if valid.sum() < 3: return None
    d_v = days[valid]; r_v = ret[valid]; results = {}
    try:
        c = np.polyfit(d_v, r_v, 1)
        k_lin = -c[0]; R0_lin = c[1]
        def sl_linear(thresh, k=k_lin, R0=R0_lin): return np.inf if k <= 0 else max((R0 - thresh)/k, 0)
        results["Linear"] = dict(params={"k (MPa/day)": round(k_lin,4), "R0": R0_lin}, pred=np.polyval(c, days), r2=round(float(1 - np.sum((r_v - np.polyval(c, d_v))**2)/np.sum((r_v - r_v.mean())**2)),4), service_life_fn=sl_linear, eq=f"R(t) = {R0_lin:.1f} − {k_lin:.4f}·t")
    except Exception: pass
    try:
        c_exp = np.polyfit(d_v, np.log(np.maximum(r_v, 1e-6)/100.0), 1)
        k_exp = -c_exp[0]
        def sl_exp(thresh, k=k_exp): return np.inf if k <= 0 or (thresh/100.0) <= 0 else np.log(100.0/thresh)/k
        results["First-order"] = dict(params={"k (day⁻¹)": round(k_exp,5), "Half-life (days)": round(np.log(2)/k_exp if k_exp > 0 else np.inf,1)}, pred=100.0 * np.exp(-k_exp * days), r2=round(float(1 - np.sum((r_v - 100.0*np.exp(-k_exp*d_v))**2)/np.sum((r_v - r_v.mean())**2)),4), service_life_fn=sl_exp, eq=f"R(t) = 100·exp(−{k_exp:.5f}·t)")
    except Exception: pass
    try:
        c_pow = np.polyfit(np.log(1.0 + d_v), np.log(np.maximum(r_v,1e-6)/100.0), 1)
        n_pow = -c_pow[0]
        def sl_pow(thresh, n=n_pow): return np.inf if n <= 0 else (100.0/thresh)**(1.0/n) - 1.0
        results["Power-law"] = dict(params={"n (exponent)": round(n_pow,4)}, pred=100.0 * (1.0 + days)**(-n_pow), r2=round(float(1 - np.sum((r_v - 100.0*(1.0+d_v)**(-n_pow))**2)/np.sum((r_v - r_v.mean())**2)),4), service_life_fn=sl_pow, eq=f"R(t) = 100·(1+t)^(−{n_pow:.4f})")
    except Exception: pass
    
    if HAS_SCIPY and len(d_v) >= 5:
        try:
            def two_phase(t, A, k1, k2): return A * np.exp(-k1*t) + (100.0-A) * np.exp(-k2*t)
            popt, _ = curve_fit(two_phase, d_v, r_v, p0=[70, 0.05, 0.005], bounds=([0, 1e-6, 1e-6], [100, 5, 5]), maxfev=5000)
            A2, k1_2, k2_2 = popt
            def sl_2p(thresh, A=A2, k1=k1_2, k2=k2_2):
                t_vals = np.linspace(0, 500, 5000)
                idx = np.where(two_phase(t_vals, A, k1, k2) <= thresh)[0]
                return float(t_vals[idx[0]]) if len(idx) > 0 else np.inf
            results["Two-phase Exp."] = dict(params={"A (fast %)": round(A2,1), "k₁ (fast day⁻¹)": round(k1_2,5), "k₂ (slow day⁻¹)": round(k2_2,6)}, pred=two_phase(days, *popt), r2=round(float(1 - np.sum((r_v - two_phase(d_v, *popt))**2)/np.sum((r_v - r_v.mean())**2)),4), service_life_fn=sl_2p, eq=f"R(t) = {A2:.1f}·exp(−{k1_2:.4f}t) + {100-A2:.1f}·exp(−{k2_2:.5f}t)")
        except Exception: pass

    return results if results else None

def compute_degradation_rate(days, retention):
    try: return round(float(-np.polyfit(np.array(days, float), np.array(retention, float), 1)[0]), 4)
    except Exception: return np.nan

def compute_auc_retention(days, retention):
    try:
        t = np.array(days, float); r = np.array(retention, float)
        return round(float(np.trapz(r, t)) / (100.0 * (t[-1] - t[0]) if t[-1] > t[0] else 1.0) * 100.0, 1)
    except Exception: return np.nan

def compute_ci(mean, sd, n, alpha=0.05):
    if pd.isna(sd) or pd.isna(n) or n < 2: return sd if not pd.isna(sd) else 0.0
    return float(t_dist.ppf(1-alpha/2, df=n-1) * sd / np.sqrt(n)) if HAS_SCIPY else float(1.96 * sd / np.sqrt(n))

def build_ageing_template():
    np.random.seed(42)
    forms = ["Pure PBAT", "PBAT/PLA 80:20", "PBAT/PLA+5%NFC"]
    conds = ["Oven", "UV-Xenon"]
    days = [0, 7, 14, 21, 28]
    rows = []
    base = {
        "Pure PBAT": dict(E=520, UTS=22, Yield=12, Elong=680, Tough=0.12, Resil=0.0014),
        "PBAT/PLA 80:20": dict(E=780, UTS=32, Yield=18, Elong=420, Tough=0.09, Resil=0.0021),
        "PBAT/PLA+5%NFC": dict(E=950, UTS=38, Yield=22, Elong=310, Tough=0.08, Resil=0.0026)
    }
    decay = {
        "Oven": dict(E=0.004, UTS=0.006, Yield=0.005, Elong=-0.003, Tough=0.007, Resil=0.005),
        "UV-Xenon": dict(E=0.006, UTS=0.010, Yield=0.008, Elong=-0.004, Tough=0.011, Resil=0.008)
    }
    for f in forms:
        for c in conds:
            for d in days:
                b = base[f]; dc = decay[c]
                def val(prop, prp): 
                    r = b[prop] * np.exp(-dc[prp] * d)
                    return round(r, 2), round(r * 0.06, 2)
                E_m, E_s = val("E", "E")
                U_m, U_s = val("UTS", "UTS")
                Y_m, Y_s = val("Yield", "Yield")
                T_m, T_s = val("Tough", "Tough")
                R_m, R_s = val("Resil", "Resil")
                rows.append({
                    "Formulation": f, "Condition": c, "Days": d, "n": 5, 
                    "E_MPa": E_m, "E_SD": E_s, "UTS_MPa": U_m, "UTS_SD": U_s, 
                    "Yield_MPa": Y_m, "Yield_SD": Y_s, 
                    "Elongation_pct": round(b["Elong"] * np.exp(dc["Elong"] * d), 1), 
                    "Elongation_SD": round(b["Elong"] * 0.08, 1), 
                    "Toughness_MJm3": T_m, "Toughness_SD": T_s, 
                    "Resilience_MJm3": R_m, "Resilience_SD": R_s
                })
    return pd.DataFrame(rows)

def template_to_excel():
    df, buf = build_ageing_template(), io.BytesIO()
    with pd.ExcelWriter(buf, engine='xlsxwriter') as w:
        df.to_excel(w, index=False, sheet_name='Ageing_Data')
        ws, wb = w.sheets['Ageing_Data'], w.book
        hdr_fmt = wb.add_format({'bold':True,'bg_color':'#002244','font_color':'#f0f4fb','border':1,'align':'center','text_wrap':True,'valign':'vcenter'})
        for i, col in enumerate(df.columns):
            max_val_len = df[col].astype(str).str.len().max()
            ws.set_column(i, i, max(len(str(col)), 0 if pd.isna(max_val_len) else max_val_len) + 3)
            ws.write(0, i, str(col), hdr_fmt)
        ws.freeze_panes(1, 4); notes_ws = wb.add_worksheet('Instructions')
        instructions = [("Formulation", "Name of each composite formulation"), ("Condition", "Ageing condition: 'Oven' or 'UV-Xenon'"), ("Days", "Ageing duration (Day 0 = control)"), ("n", "Number of replicate specimens per group"), ("E_MPa", "Mean Young's Modulus [MPa]"), ("E_SD", "Standard deviation of Young's Modulus"), ("UTS_MPa", "Mean UTS [MPa]"), ("UTS_SD", "Standard deviation of UTS"), ("Yield_MPa", "Mean Yield Stress [MPa]"), ("Yield_SD", "Standard deviation of Yield Stress"), ("Elongation_pct", "Mean Elongation at Break [%]"), ("Elongation_SD", "Standard dev of Elongation"), ("Toughness_MJm3", "Mean Toughness [MJ/m³]"), ("Toughness_SD", "Standard dev of Toughness"), ("Resilience_MJm3", "Mean Modulus of Resilience [MJ/m³]"), ("Resilience_SD", "Standard dev of Resilience")]
        for ri, (col, desc) in enumerate(instructions): notes_ws.write(ri+1, 0, col, wb.add_format({'bold':True})); notes_ws.write(ri+1, 1, desc)
        notes_ws.set_column(0, 0, 20); notes_ws.set_column(1, 1, 80); notes_ws.write(0, 0, "Column", wb.add_format({'bold':True,'underline':True})); notes_ws.write(0, 1, "Description", wb.add_format({'bold':True,'underline':True}))
    buf.seek(0); return buf.getvalue()

def load_ageing_data(file):
    try:
        ext = file.name.rsplit('.',1)[-1].lower()
        df = pd.read_excel(file, engine='openpyxl') if ext in ['xlsx', 'xls'] else pd.read_csv(file)
        df.columns = [str(c).strip() for c in df.columns]
        missing = [c for c in ["Formulation","Condition","Days"] if c not in df.columns]
        if missing: st.error(f"Missing required columns: {missing}"); return None
        df["Days"] = pd.to_numeric(df["Days"], errors='coerce'); df["n"] = pd.to_numeric(df.get("n", pd.Series([5]*len(df))), errors='coerce').fillna(5)
        for col in [c for c in df.columns if c not in ["Formulation","Condition","Days","n"]]: df[col] = pd.to_numeric(df[col], errors='coerce')
        return df.dropna(subset=["Days"])
    except Exception as e: st.error(f"Error loading ageing data: {e}"); return None

def get_retention(df, formulation, condition, prop_col):
    sub = df[(df["Formulation"]==formulation) & (df["Condition"]==condition)].copy().sort_values("Days")
    day0 = sub[sub["Days"]==0][prop_col].values
    if len(day0) == 0 or day0[0] == 0: return sub["Days"].tolist(), [np.nan]*len(sub)
    return sub["Days"].tolist(), (sub[prop_col].fillna(np.nan) / day0[0] * 100.0).tolist()

def compute_dsi(df, formulation, condition):
    weights = {"E_MPa":1.2,"UTS_MPa":1.5,"Yield_MPa":1.0,"Elongation_pct":0.8,"Toughness_MJm3":1.3,"Resilience_MJm3":1.0}; auc_scores = []
    for pcol, w in weights.items():
        if pcol not in df.columns: continue
        days, ret = get_retention(df, formulation, condition, pcol)
        valid = [(d,r) for d,r in zip(days,ret) if not np.isnan(r)]
        if len(valid) >= 2:
            auc = compute_auc_retention([v[0] for v in valid], [v[1] for v in valid])
            if not np.isnan(auc): auc_scores.append(auc * w)
    return round(np.sum(auc_scores)/sum(weights[c] for c in weights if c in df.columns), 1) if auc_scores else np.nan

# ═══════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════
defaults = {"all_results": [], "plot_data": {}, "sample_colors": {}, "ageing_db": pd.DataFrame()}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    render_sidebar_brand()
    st.markdown("---")
    st.markdown("### 🧭 Navigation")
    page = st.radio("", ["🔬 Tensile Analysis", "📅 Ageing Trend Analysis"], label_visibility="collapsed")
    st.markdown("---")

    if page == "🔬 Tensile Analysis":
        st.markdown("### 📥 Data Import Settings")
        skip_header_rows = st.number_input("Metadata Rows to Skip", value=0, min_value=0, step=1, help="If your machine exports text above the column names, enter the number of rows to skip.")
        st.markdown("---")
        st.markdown("### 🏷️ Batch Metadata")
        form_tag = st.text_input("Formulation ID", "Pure PBAT", key="form_tag")
        cond_tag = st.selectbox("Condition", ["Unaged","Oven","UV-Xenon"], key="cond_tag")
        days_tag = st.number_input("Days Aged", 0, 365, 0, key="days_tag")
        n_tag    = st.number_input("Specimens (n)", 1, 50, 5, key="n_tag")
        st.markdown("---")
        st.markdown("### 📏 Specimen Geometry")
        thickness    = st.number_input("Thickness (mm)", value=4.0, step=0.1, format="%.2f")
        width        = st.number_input("Width (mm)",     value=4.0, step=0.1, format="%.2f")
        gauge_length = st.number_input("Gauge Length L₀ (mm)", value=25.0, step=1.0)
        area = width * thickness
        st.caption(f"Area: **{area:.3f} mm²**")
        st.markdown("---")
        st.markdown("### ⚙️ Calibration")
        u_scale = {"mm":1.0,"µm":0.001,"m":1000.0}[st.selectbox("Displacement Unit",["mm","µm","m"])]
        apply_zeroing = st.checkbox("Toe Compensation", value=True)
        st.markdown("---")
        st.markdown("### 📉 Signal Processing")
        smooth_win = st.slider("Smoothing Window (1=off)", 1, 60, 1)
        st.markdown("---")
        st.markdown("### 🎨 Plot Options")
        line_lw      = st.slider("Line Thickness", 0.5, 5.0, 2.0, 0.5)
        legend_pos   = st.selectbox("Legend",["lower right","upper right","upper left","lower left","best","outside"])
        show_mean    = st.checkbox("Mean ± SD Band", False)
        show_E_lines = st.checkbox("Modulus Fit Lines", True)
        auto_scale   = st.checkbox("Auto-Scale Axes", True)
        if not auto_scale:
            cust_xmax = st.number_input("X max (%)", value=10.0)
            cust_ymax = st.number_input("Y max (MPa)", value=50.0)
        st.markdown("---")
        st.markdown("### ✅ QC Thresholds")
        qc_uts   = st.number_input("Min UTS (MPa)",      value=0.0, step=1.0)
        qc_E     = st.number_input("Min Modulus (MPa)",  value=0.0, step=10.0)
        qc_elong = st.number_input("Min Elongation (%)", value=0.0, step=0.5)
    else:
        st.markdown("### ⚙️ Ageing Analysis Options")
        ag_failure_thresh = st.slider("Service Life Failure Threshold (%)", 50, 95, 80)
        ag_show_ci        = st.checkbox("Show 95% Confidence Intervals", True)
        ag_show_fit       = st.checkbox("Show Model Fit Lines", True)
        st.markdown("---")
        st.markdown("### 🌡️ Oven Temp. (Arrhenius)")
        use_arrhenius = st.checkbox("Enable Arrhenius Analysis", False)
        if use_arrhenius:
            arr_temps_str = st.text_input("Oven Temperatures (°C, comma-separated)", "60, 70, 80")

    st.markdown("""<div style="padding:0.6rem 0 0.3rem;text-align:center;font-family:'IBM Plex Sans',sans-serif;font-size:0.6rem;color:#7f8c8d;letter-spacing:0.1em;">Research & Academic Use Only · v4.7</div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# PAGE 1 — TENSILE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════
if page == "🔬 Tensile Analysis":
    render_header("Tensile Analysis")

    class DigitizedFile:
        def __init__(self, n, d): self.name=n; self.df=d

    input_mode = st.radio("Input Source", ["Standard Files (CSV / XLSX / TXT)", "Image Digitizer (legacy plots)"], horizontal=True)
    uploaded_files = []
    
    if input_mode == "Image Digitizer (legacy plots)":
        if HAS_CANVAS:
            dig_file = st.file_uploader("Upload plot image",type=["png","jpg","jpeg"],key="dig")
            if dig_file:
                img = Image.open(dig_file)
                c1,c2 = st.columns([2,1])
                with c2:
                    st.info("Click: 1.Origin  2.Max-X  3.Max-Y  4+.Curve points")
                    rmx = st.number_input("Real Max Strain (%)",value=10.0)
                    rmy = st.number_input("Real Max Stress (MPa)",value=100.0)
                with c1:
                    cr = st_canvas(fill_color="rgba(201,168,76,0.3)",stroke_width=2,stroke_color="#c0392b",background_image=img,height=int(img.height*(800/img.width)),width=800,drawing_mode="point",key="cvs")
                if cr.json_data:
                    pts = pd.json_normalize(cr.json_data["objects"])
                    if len(pts) >= 4:
                        coords = pts[['left','top']].values
                        origin,mX,mY,curve = coords[0],coords[1],coords[2],coords[3:]
                        sX = rmx/max(mX[0]-origin[0],1e-6); sY = rmy/max(origin[1]-mY[1],1e-6)
                        data = [{"Digitized Strain":(p[0]-origin[0])*sX, "Digitized Stress":(origin[1]-p[1])*sY} for p in curve]
                        uploaded_files = [DigitizedFile(f"Digitized_{dig_file.name}",pd.DataFrame(data))]
        else: st.warning("Install `streamlit-drawable-canvas` for this mode.")
    else:
        uploaded_files = st.file_uploader("Upload tensile data files", type=['csv','xlsx','txt'], accept_multiple_files=True, key="main_upload")

    if uploaded_files:
        all_results=[]; plot_data={}; sample_colors={}
        
        first_df = smart_load(uploaded_files[0], skip_header_rows)
        global_cols = first_df.columns.tolist() if first_df is not None else []
        
        force_kws = ['stress', 'sforzo', 'mpa', 'sigma', 'force', 'load', 'n', 'lbf', 'kgf', 'str']
        def_f = next((c for c in global_cols if any(k in str(c).lower() for k in force_kws)), None)
        disp_kws = ['strain', 'disp', 'ext', 'mm', 'elongation', '%', 'pos', 'deformation', 'def']
        def_d = next((c for c in global_cols if any(k in str(c).lower() for k in disp_kws)), None)
        
        if not def_f or not def_d:
            non_time_cols = [c for c in global_cols if 'time' not in str(c).lower() and 'sec' not in str(c).lower()]
            if not def_f: def_f = non_time_cols[-1] if len(non_time_cols) > 0 else (global_cols[-1] if global_cols else None)
            if not def_d: def_d = non_time_cols[0] if len(non_time_cols) > 0 else (global_cols[0] if global_cols else None)

        if "Digitized Strain" in global_cols:
            def_d, def_f = "Digitized Strain", "Digitized Stress"
            
        f_idx = global_cols.index(def_f) if def_f in global_cols else 0
        d_idx = global_cols.index(def_d) if def_d in global_cols else (1 if len(global_cols) > 1 else 0)

        with st.expander("⚡ Global Settings & Bulk Apply", expanded=True):
            st.markdown("**1. Global Column Selection**")
            gc1, gc2 = st.columns(2)
            global_f_col = gc1.selectbox("Global Force/Stress Column", global_cols, index=f_idx, key="glob_f")
            global_d_col = gc2.selectbox("Global Disp/Strain Column", global_cols, index=d_idx, key="glob_d")

            st.markdown("**2. Modulus & Yield Settings**")
            bc1,bc2,bc3,bc4 = st.columns([2,2,2,1])
            bulk_r  = bc1.slider("Global Fit Range (%)",0.0,20.0,(0.2,1.0),key="br")
            bulk_m  = bc2.select_slider("Global Yield Method", options=["0.2% Offset Method","Departure from Linearity"], value="0.2% Offset Method", key="bm")
            bulk_v  = bc3.slider("Global Offset/Sensitivity (%)",0.01,50.0,0.2,0.01,key="bv")
            st.caption("Adjusting sliders updates graphs instantly. Hit 'Apply All' to sync unlinked files.")
            if bc4.button("Apply All", type="primary"):
                for f in uploaded_files:
                    if f:
                        st.session_state[f"range_{f.name}_sl"]=bulk_r
                        st.session_state[f"meth_{f.name}_sl"]=bulk_m
                        st.session_state[f"val_{f.name}_sl"]=bulk_v
                st.rerun()

        for idx, file in enumerate(uploaded_files):
            if file is None: continue
            df_raw = smart_load(file, skip_header_rows)
            if df_raw is None or df_raw.empty: continue
            
            f_col = global_f_col
            d_col = global_d_col
            
            if f_col not in df_raw.columns or d_col not in df_raw.columns:
                st.error(f"File '{file.name}' missing columns '{f_col}' or '{d_col}'. Check your 'Metadata Rows to Skip' setting.")
                continue

            with st.expander(f"📄 {clean_label(file.name)}", expanded=False):
                r1 = st.columns([3, 1])
                custom_name = r1[0].text_input("Display Name", value=clean_label(file.name), key=f"nm_{file.name}")
                chosen_color = r1[1].color_picker("Color", value=PALETTE[idx%len(PALETTE)], key=f"col_{file.name}")
                sample_colors[custom_name] = chosen_color

                r2 = st.columns([2,2,2])
                fit_range = r2[0].slider("Modulus Fit Range (%)",0.0,20.0, st.session_state.get(f"range_{file.name}_sl", bulk_r), key=f"range_{file.name}_sl")
                current_ym_val = st.session_state.get(f"meth_{file.name}_sl", bulk_m)
                if current_ym_val not in ["0.2% Offset Method","Departure from Linearity"]: current_ym_val = "0.2% Offset Method"
                yield_method = r2[1].select_slider("Yield Method", options=["0.2% Offset Method","Departure from Linearity"], value=current_ym_val, key=f"meth_{file.name}_sl")
                yield_val = r2[2].slider("Offset/Sensitivity (%)",0.01,50.0, st.session_state.get(f"val_{file.name}_sl", bulk_v), 0.01, key=f"val_{file.name}_sl")

                # FIXED: Ensure European commas are read as decimals, then sort data strictly by strain to prevent plotting backwards (scribble effect)
                df_c = df_raw[[f_col,d_col]].copy()
                df_c[f_col] = df_c[f_col].astype(str).str.replace(',', '.', regex=False)
                df_c[d_col] = df_c[d_col].astype(str).str.replace(',', '.', regex=False)
                df_c = df_c.apply(pd.to_numeric,errors='coerce').dropna()
                df_c = df_c.sort_values(by=d_col).reset_index(drop=True)
                
                if df_c.empty: st.error("No numeric data found. Check separators."); continue
                
                if "Digitized" in str(file.name):
                    stress_raw_arr = df_c[f_col].values; strain_raw_arr = df_c[d_col].values
                else:
                    is_strain = any(k in str(d_col).lower() for k in ['strain', '%', 'str'])
                    is_stress = any(k in str(f_col).lower() for k in ['stress', 'mpa', 'sigma', 'sforzo'])
                    strain_raw_arr = df_c[d_col].values if is_strain else (df_c[d_col].values * u_scale / gauge_length) * 100.0
                    stress_raw_arr = df_c[f_col].values if is_stress else df_c[f_col].values / area
                    
                if smooth_win > 1:
                    stress_raw_arr = pd.Series(stress_raw_arr).rolling(smooth_win,min_periods=1).mean().values
                    strain_raw_arr = pd.Series(strain_raw_arr).rolling(smooth_win,min_periods=1).mean().values

                r = process_sample(strain_raw_arr,stress_raw_arr,fit_range,yield_method,yield_val,apply_zeroing)
                if r is None: st.error("Processing failed — check columns and fit range."); continue

                fig_mini = go.Figure()
                fig_mini.add_trace(go.Scatter(x=r["strain"],y=r["stress"],mode='lines', line=dict(color=chosen_color,width=2),name="Eng."))
                if show_E_lines: fig_mini.add_trace(go.Scatter(x=r["fit_x"],y=r["fit_y"],mode='lines', line=dict(color='#555',width=1,dash='dot'),showlegend=False,hoverinfo='skip'))
                fig_mini.update_layout(height=210,margin=dict(l=0,r=0,t=0,b=0), plot_bgcolor='#fff',paper_bgcolor='#fff',showlegend=False, xaxis=dict(showgrid=False,linecolor='#dde3ec',range=[0,None],tickfont=dict(size=10)), yaxis=dict(showgrid=False,linecolor='#dde3ec',range=[0,None],tickfont=dict(size=10)))
                st.plotly_chart(fig_mini,use_container_width=True,config={'displayModeBar':False})

                kpi = st.columns(6)
                kpi[0].metric("E (MPa)",      f"{r['E_MPa']:.0f}")
                kpi[1].metric("σᵧ (MPa)",     f"{r['y_stress']:.1f}" if not np.isnan(r['y_stress']) else "—")
                kpi[2].metric("UTS (MPa)",    f"{r['uts']:.1f}")
                kpi[3].metric("εᵦ (%)",       f"{r['strain_break']:.2f}")
                kpi[4].metric("Toughness",    f"{r['toughness']:.3f}")
                kpi[5].metric("n (Hollomon)", f"{r['h_n']:.3f}" if not np.isnan(r['h_n']) else "—")

                try: work_j=float(np.trapezoid(r["stress"]*area,(r["strain"]/100.0)*gauge_length/1000.0))
                except AttributeError: work_j=float(np.trapz(r["stress"]*area,(r["strain"]/100.0)*gauge_length/1000.0))

                plot_data[custom_name] = r
                all_results.append({
                    "Sample": custom_name, "File": file.name, "Class": r["mat_class"],
                    "Modulus [MPa]": r["E_MPa"], "Yield Stress [MPa]": r["y_stress"],
                    "Yield Strain [%]": r["y_strain"], "UTS [MPa]": r["uts"],
                    "Stress at Break [MPa]": r["stress_break"],
                    "Elongation at Break [%]": r["strain_break"], "Work Done [J]": round(work_j,5),
                    "Toughness [MJ/m³]": r["toughness"], "Resilience [MJ/m³]": r["resilience"],
                    "Ductility Index": r["ductility_idx"], "Hollomon n": r["h_n"], "Hollomon K [MPa]": r["h_K"], "Hollomon R²": r["h_r2"]
                })

        if not all_results: st.warning("No samples processed."); st.stop()

        res_df   = pd.DataFrame(all_results)
        num_cols = [c for c in res_df.columns if c not in ("Sample","File","Class")]
        j_settings = dict(lw=line_lw,legend_pos=legend_pos,show_mean=show_mean,auto_scale=auto_scale)
        if not auto_scale: j_settings.update(x_max=cust_xmax,y_max=cust_ymax)
        journal_fig = generate_journal_fig(plot_data,sample_colors,j_settings)
        mean_curve  = compute_mean_curve(plot_data)

        section_hdr("Send Batch to Ageing Database","📤")
        st.markdown(f"Current tag: **{form_tag}** | **{cond_tag}** | **Day {days_tag}** | n = {n_tag}")
        if st.button("➕ Add this batch to Ageing Database", type="primary"):
            num_df = res_df[num_cols].apply(pd.to_numeric,errors='coerce')
            means  = num_df.mean(); sds = num_df.std()
            new_row = {"Formulation":form_tag,"Condition":cond_tag,"Days":days_tag,"n":int(n_tag)}
            for t_col, a_col in TENSILE_TO_AGEING.items():
                if t_col in means.index:
                    new_row[a_col] = round(float(means[t_col]),4) if not np.isnan(means[t_col]) else np.nan
                    new_row[a_col+"_SD"] = round(float(sds[t_col]),4) if not np.isnan(sds[t_col]) else np.nan
            row_df = pd.DataFrame([new_row])
            for a_col in TENSILE_TO_AGEING.values():
                sd_raw  = a_col + "_SD"
                sd_nice = {"E_MPa":"E_SD", "UTS_MPa":"UTS_SD", "Yield_MPa":"Yield_SD", "Elongation_pct":"Elongation_SD", "Toughness_MJm3":"Toughness_SD", "Resilience_MJm3":"Resilience_SD"}.get(a_col, sd_raw)
                if sd_raw in row_df.columns: row_df.rename(columns={sd_raw: sd_nice}, inplace=True)
            st.session_state["ageing_db"] = pd.concat([st.session_state["ageing_db"], row_df], ignore_index=True)
            st.success(f"✓ Added {form_tag} / {cond_tag} / Day {days_tag} → Ageing Database ({len(st.session_state['ageing_db'])} rows total).")

        out_tabs = st.tabs(["📈 Stress-Strain","🔩 Hollomon & True S-S","📐 Secant & Resilience","📉 Weibull & Mean Curve","📊 Statistics & QC","📋 Full Records","💾 Export"])

        with out_tabs[0]:
            section_hdr("Engineering Stress–Strain Curves","📈")
            view_mode = st.radio("Render Mode",["Interactive","Journal Static (600 DPI)"],horizontal=True)
            overlay_true = st.checkbox("Overlay True Stress–Strain (dashed)",False)
            if view_mode == "Interactive":
                fig_m = go.Figure()
                for name,r in plot_data.items():
                    col = sample_colors.get(name,"#002244")
                    fig_m.add_trace(go.Scatter(x=r["strain"],y=r["stress"],name=name,mode='lines', line=dict(width=line_lw,color=col)))
                    if overlay_true: fig_m.add_trace(go.Scatter(x=r["true_strain"]*100,y=r["true_stress"], name=f"{name} (True)",mode='lines', line=dict(width=line_lw*0.75,color=col,dash='dash'),opacity=0.65))
                    if show_E_lines: fig_m.add_trace(go.Scatter(x=r["fit_x"],y=r["fit_y"],mode='lines', line=dict(width=1,color='#aaa',dash='dot'),showlegend=False,hoverinfo='skip'))
                if show_mean and mean_curve:
                    fig_m.add_trace(go.Scatter(x=np.concatenate([mean_curve["strain"],mean_curve["strain"][::-1]]), y=np.concatenate([mean_curve["upper"],mean_curve["lower"][::-1]]), fill='toself',fillcolor='rgba(0,34,68,0.10)', line=dict(width=0),name="±1 SD",hoverinfo='skip'))
                    fig_m.add_trace(go.Scatter(x=mean_curve["strain"],y=mean_curve["mean"],mode='lines', line=dict(color='#000',width=2,dash='dash'),name="Mean"))
                xl = res_df["Elongation at Break [%]"].max()*1.08 if auto_scale else cust_xmax
                yl = res_df["UTS [MPa]"].max()*1.12 if auto_scale else cust_ymax
                fig_m.update_layout(plot_bgcolor='#fff',paper_bgcolor='#fff',height=640, xaxis=dict(title="<b>Strain (%)</b>",range=[0,xl],**AXIS), yaxis=dict(title="<b>Stress (MPa)</b>",range=[0,yl],**AXIS), legend=dict(font=dict(family="Times New Roman",size=12)), margin=dict(l=60,r=40,t=25,b=60))
                st.plotly_chart(fig_m,use_container_width=True,config=JCFG)
            else:
                st.pyplot(journal_fig)
                bp=io.BytesIO(); journal_fig.savefig(bp,format='png',dpi=600,bbox_inches='tight')
                bp.seek(0); pi=Image.open(bp); bt=io.BytesIO()
                pi.save(bt,format='TIFF',compression='tiff_lzw',dpi=(600,600))
                st.download_button("📥 Download 600 DPI TIFF",bt.getvalue(), "Tensile_Journal_600dpi.tiff","image/tiff")

        with out_tabs[1]:
            section_hdr("Hollomon Strain Hardening & True Stress–Strain","🔩")
            ht1,ht2 = st.tabs(["True vs Engineering","Log–Log Hollomon"])
            with ht1:
                fig_t=go.Figure()
                for name,r in plot_data.items():
                    col=sample_colors.get(name)
                    fig_t.add_trace(go.Scatter(x=r["strain"],y=r["stress"],name=f"{name}–Eng.",mode='lines',line=dict(width=line_lw,color=col)))
                    fig_t.add_trace(go.Scatter(x=r["true_strain"]*100,y=r["true_stress"],name=f"{name}–True",mode='lines',line=dict(width=line_lw,color=col,dash='dash')))
                fig_t.update_layout(plot_bgcolor='#fff',paper_bgcolor='#fff',height=520, xaxis=dict(title="<b>Strain</b>",range=[0,None],**AXIS), yaxis=dict(title="<b>Stress (MPa)</b>",range=[0,None],**AXIS), margin=dict(l=60,r=40,t=25,b=60))
                st.plotly_chart(fig_t,use_container_width=True,config=JCFG)
            with ht2:
                fig_h=go.Figure(); hrows=[]
                for name,r in plot_data.items():
                    col=sample_colors.get(name)
                    if not np.isnan(r["h_n"]):
                        pm=r["strain"]>=(r["y_strain"] if not np.isnan(r["y_strain"]) else 0)
                        te_p=r["true_strain"][pm]; ts_p=r["true_stress"][pm]
                        v=(ts_p>0)&(te_p>0)
                        if v.sum()>2:
                            lx=np.log(te_p[v]); ly=np.log(ts_p[v])
                            fig_h.add_trace(go.Scatter(x=lx,y=ly,mode='markers',name=name,marker=dict(color=col,size=5,opacity=0.7)))
                            lxf=np.linspace(lx.min(),lx.max(),60)
                            fig_h.add_trace(go.Scatter(x=lxf,y=r["h_n"]*lxf+np.log(r["h_K"]),mode='lines',line=dict(color=col,width=1.5,dash='dash'),showlegend=False))
                    hrows.append({"Sample":name,"n":r["h_n"],"K (MPa)":r["h_K"],"R²":r["h_r2"],"Class":r["mat_class"]})
                if fig_h.data:
                    fig_h.update_layout(plot_bgcolor='#fff',paper_bgcolor='#fff',height=430, xaxis=dict(title="<b>ln(True Strain)</b>",**AXIS), yaxis=dict(title="<b>ln(True Stress MPa)</b>",**AXIS), margin=dict(l=65,r=40,t=25,b=60))
                    st.plotly_chart(fig_h,use_container_width=True,config=JCFG)
                st.dataframe(pd.DataFrame(hrows),hide_index=True,use_container_width=True)

        with out_tabs[2]:
            section_hdr("Secant Moduli at Fixed Strain Levels","📐")
            sec_rows=[{"Sample":n,"E (MPa)":r["E_MPa"],**{f"Es@{ts}%":r["secant"].get(ts,"—") for ts in [0.25,0.5,1.0,2.0,5.0,10.0]}} for n,r in plot_data.items()]
            st.dataframe(pd.DataFrame(sec_rows),hide_index=True,use_container_width=True)
            fig_s=go.Figure()
            for name,r in plot_data.items():
                sx=sorted(r["secant"].keys()); sy=[r["secant"][k] for k in sx]
                if sx: fig_s.add_trace(go.Scatter(x=sx,y=sy,mode='lines+markers',name=name, line=dict(color=sample_colors.get(name)),marker=dict(size=9)))
            fig_s.update_layout(plot_bgcolor='#fff',paper_bgcolor='#fff',height=370, xaxis=dict(title="<b>Strain Level (%)</b>",tickvals=[0.25,0.5,1,2,5,10],**AXIS), yaxis=dict(title="<b>Secant Modulus (MPa)</b>",**AXIS),margin=dict(l=65,r=40,t=25,b=60))
            st.plotly_chart(fig_s,use_container_width=True,config=JCFG)

        with out_tabs[3]:
            wt1,wt2=st.tabs(["📉 Weibull","〰 Mean Curve"])
            with wt1:
                section_hdr("Two-Parameter Weibull Analysis","📉")
                wb_data=compute_weibull(res_df["UTS [MPa]"].apply(pd.to_numeric,errors='coerce').dropna().tolist())
                if wb_data:
                    wc=st.columns(4)
                    wc[0].metric("m",f"{wb_data['m']}"); wc[1].metric("σ₀ (MPa)",f"{wb_data['sigma_0']}")
                    wc[2].metric("σ@90% survival",f"{wb_data['sigma_90']}"); wc[3].metric("R²",f"{wb_data['r2']}")
                    fig_wb=go.Figure()
                    fig_wb.add_trace(go.Scatter(x=wb_data["x"],y=wb_data["y"],mode='markers', marker=dict(color='#002244',size=10)))
                    fig_wb.add_trace(go.Scatter(x=wb_data["fx"],y=wb_data["fy"],mode='lines', line=dict(color='#c9a84c',width=2.5),name=f"m={wb_data['m']}"))
                    fig_wb.update_layout(plot_bgcolor='#fff',paper_bgcolor='#fff',height=420, xaxis=dict(title="<b>ln(UTS)</b>",**AXIS), yaxis=dict(title="<b>ln(ln(1/(1−Pf)))</b>",**AXIS),margin=dict(l=70,r=40,t=25,b=60))
                    st.plotly_chart(fig_wb,use_container_width=True,config=JCFG)
                else: st.info("Need ≥ 3 specimens for Weibull.")
            with wt2:
                section_hdr("Mean ± SD Envelope","〰")
                if mean_curve:
                    fig_mc=go.Figure()
                    fig_mc.add_trace(go.Scatter(x=np.concatenate([mean_curve["strain"],mean_curve["strain"][::-1]]), y=np.concatenate([mean_curve["upper"],mean_curve["lower"][::-1]]), fill='toself',fillcolor='rgba(0,34,68,0.11)',line=dict(width=0),name="±1 SD"))
                    for name,r in plot_data.items():
                        fig_mc.add_trace(go.Scatter(x=r["strain"],y=r["stress"],mode='lines', line=dict(color=sample_colors.get(name,'#aaa'),width=1),opacity=0.3,name=name))
                    fig_mc.add_trace(go.Scatter(x=mean_curve["strain"],y=mean_curve["mean"],mode='lines', line=dict(color='#002244',width=2.5),name="Mean"))
                    fig_mc.update_layout(plot_bgcolor='#fff',paper_bgcolor='#fff',height=510, xaxis=dict(title="<b>Strain (%)</b>",range=[0,None],**AXIS), yaxis=dict(title="<b>Stress (MPa)</b>",range=[0,None],**AXIS), margin=dict(l=60,r=40,t=25,b=60))
                    st.plotly_chart(fig_mc,use_container_width=True,config=JCFG)
                else: st.info("Need ≥ 2 specimens.")

        with out_tabs[4]:
            section_hdr("Batch Descriptive Statistics","📊")
            num_df = res_df[num_cols].apply(pd.to_numeric,errors='coerce')
            stats_df = num_df.agg(['mean','std','min','max']).round(3)
            stats_df.loc['CV (%)'] = (stats_df.loc['std']/stats_df.loc['mean'].replace(0,np.nan)*100).round(1)
            st.dataframe(stats_df,use_container_width=True)
            section_hdr("QC Assessment","✅")
            if any([qc_uts>0,qc_E>0,qc_elong>0]):
                qc_rows=[]
                for _,row in res_df.iterrows():
                    fails=[]
                    u, e, el = pd.to_numeric(row.get("UTS [MPa]",np.nan),errors='coerce'), pd.to_numeric(row.get("Modulus [MPa]",np.nan),errors='coerce'), pd.to_numeric(row.get("Elongation at Break [%]",np.nan),errors='coerce')
                    if qc_uts>0 and (np.isnan(u) or u<qc_uts): fails.append(f"UTS {u:.1f}<{qc_uts}")
                    if qc_E>0 and (np.isnan(e) or e<qc_E): fails.append(f"E {e:.0f}<{qc_E}")
                    if qc_elong>0 and (np.isnan(el) or el<qc_elong): fails.append(f"ε {el:.2f}<{qc_elong}")
                    qc_rows.append({"Sample":row["Sample"],"UTS":round(u,2) if not np.isnan(u) else "—", "E":round(e,1) if not np.isnan(e) else "—", "Result":"✅ PASS" if not fails else "❌ FAIL","Fails":"; ".join(fails) or "—"})
                qc_df=pd.DataFrame(qc_rows)
                np_=( qc_df["Result"]=="✅ PASS").sum()
                qcm=st.columns(3)
                qcm[0].metric("Total",len(qc_df)); qcm[1].metric("✅ Pass",int(np_)); qcm[2].metric("❌ Fail",int(len(qc_df)-np_))
                st.dataframe(qc_df,hide_index=True,use_container_width=True)

        with out_tabs[5]:
            section_hdr("Complete Individual Test Records","📋")
            st.dataframe(res_df,hide_index=True,use_container_width=True)

        with out_tabs[6]:
            section_hdr("Export Full Analytics & Plots","💾")
            ec1,ec2=st.columns(2)
            with ec1:
                st.markdown("**📊 Generate Full Excel Report**")
                st.caption("Exports all raw data arrays, analytical results, and high-res chart images into one comprehensive workbook.")
                xl_buf=io.BytesIO()
                try:
                    with pd.ExcelWriter(xl_buf,engine='xlsxwriter') as w:
                        res_df.to_excel(w,sheet_name='Results',index=False)
                        stats_df.to_excel(w,sheet_name='Batch_Statistics')
                        
                        raw_fs=[]
                        for name,r in plot_data.items():
                            raw_fs.append(pd.DataFrame({f"{name}_Strain(%)":r["strain"],f"{name}_Stress(MPa)":r["stress"], f"{name}_TrueStrain(abs)":r["true_strain"],f"{name}_TrueStress(MPa)":r["true_stress"]}))
                        if raw_fs: pd.concat(raw_fs,axis=1).to_excel(w,sheet_name='Raw_Curves',index=False)
                        
                        pd.DataFrame([{"Sample":rr["Sample"],"n":rr["Hollomon n"],"K(MPa)":rr["Hollomon K [MPa]"],"R²":rr["Hollomon R²"]} for rr in all_results]).to_excel(w,sheet_name='Hollomon_Summary',index=False)
                        hol_raw_dfs = []
                        for name, r in plot_data.items():
                            if not np.isnan(r["h_n"]):
                                pm = r["strain"] >= (r["y_strain"] if not np.isnan(r["y_strain"]) else 0)
                                te_p = r["true_strain"][pm]; ts_p = r["true_stress"][pm]; v = (ts_p > 0) & (te_p > 0)
                                if v.sum() > 2:
                                    hol_raw_dfs.append(pd.DataFrame({f"{name}_ln(TrueStrain)": np.log(te_p[v]), f"{name}_ln(TrueStress)": np.log(ts_p[v])}))
                        if hol_raw_dfs: pd.concat(hol_raw_dfs, axis=1).to_excel(w, sheet_name='Hollomon_RawData', index=False)

                        if 'sec_rows' in locals(): pd.DataFrame(sec_rows).to_excel(w, sheet_name='Secant_Data', index=False)
                        if 'wb_data' in locals() and wb_data: pd.DataFrame({"ln(UTS)": wb_data["x"], "ln(ln(1/(1-Pf)))": wb_data["y"]}).to_excel(w, sheet_name='Weibull_Data', index=False)
                        if 'mean_curve' in locals() and mean_curve: pd.DataFrame({"Strain(%)": mean_curve["strain"], "Mean_Stress(MPa)": mean_curve["mean"], "Upper_SD": mean_curve["upper"], "Lower_SD": mean_curve["lower"]}).to_excel(w, sheet_name='Mean_Curve_Data', index=False)
                        
                        plt.rcParams.update({"font.family":"serif","font.size":10})
                        
                        ps=w.book.add_worksheet('Plot_Journal')
                        ps.write('A1','Engineering Stress-Strain Curve')
                        ie=io.BytesIO(); journal_fig.savefig(ie,format='png',dpi=200,bbox_inches='tight'); ie.seek(0)
                        ps.insert_image('A3','p1.png',{'image_data':ie})
                        
                        fig_t_exp, ax_t = plt.subplots(figsize=(7,5))
                        for name, r in plot_data.items(): ax_t.plot(r["true_strain"]*100, r["true_stress"], label=name, color=sample_colors.get(name,"#000"))
                        ax_t.set_xlabel("True Strain (%)"); ax_t.set_ylabel("True Stress (MPa)"); ax_t.legend(); fig_t_exp.tight_layout()
                        buf_t = io.BytesIO(); fig_t_exp.savefig(buf_t, format='png', dpi=200); buf_t.seek(0)
                        w.book.add_worksheet('Plot_TrueSS').insert_image('A1', 'p2.png', {'image_data': buf_t})
                        plt.close(fig_t_exp)
                        
                        fig_h_exp, ax_h = plt.subplots(figsize=(7,5))
                        for name, r in plot_data.items():
                            if not np.isnan(r["h_n"]):
                                pm = r["strain"] >= (r["y_strain"] if not np.isnan(r["y_strain"]) else 0)
                                te_p = r["true_strain"][pm]; ts_p = r["true_stress"][pm]; v = (ts_p > 0) & (te_p > 0)
                                if v.sum() > 2:
                                    lx = np.log(te_p[v]); ly = np.log(ts_p[v])
                                    ax_h.plot(lx, ly, 'o', color=sample_colors.get(name,"#000"), alpha=0.5, ms=4)
                                    lxf = np.linspace(lx.min(), lx.max(), 60)
                                    ax_h.plot(lxf, r["h_n"]*lxf + np.log(r["h_K"]), '--', color=sample_colors.get(name,"#000"), label=f"{name} (n={r['h_n']:.3f})")
                        ax_h.set_xlabel("ln(True Strain)"); ax_h.set_ylabel("ln(True Stress MPa)"); ax_h.legend(); fig_h_exp.tight_layout()
                        buf_h = io.BytesIO(); fig_h_exp.savefig(buf_h, format='png', dpi=200); buf_h.seek(0)
                        w.book.add_worksheet('Plot_Hollomon').insert_image('A1', 'p3.png', {'image_data': buf_h})
                        plt.close(fig_h_exp)
                        
                        fig_s_exp, ax_s = plt.subplots(figsize=(7,5))
                        for name, r in plot_data.items():
                            sx = sorted(r["secant"].keys()); sy = [r["secant"][k] for k in sx]
                            if sx: ax_s.plot(sx, sy, '-o', label=name, color=sample_colors.get(name,"#000"))
                        ax_s.set_xlabel("Strain Level (%)"); ax_s.set_ylabel("Secant Modulus (MPa)"); ax_s.legend(); fig_s_exp.tight_layout()
                        buf_s = io.BytesIO(); fig_s_exp.savefig(buf_s, format='png', dpi=200); buf_s.seek(0)
                        w.book.add_worksheet('Plot_Secant').insert_image('A1', 'p4.png', {'image_data': buf_s})
                        plt.close(fig_s_exp)

                        if 'wb_data' in locals() and wb_data:
                            fig_w_exp, ax_w = plt.subplots(figsize=(7,5))
                            ax_w.plot(wb_data["x"], wb_data["y"], 'o', color='#002244', ms=8)
                            ax_w.plot(wb_data["fx"], wb_data["fy"], '-', color='#c9a84c', lw=2, label=f"m={wb_data['m']}")
                            ax_w.set_xlabel("ln(UTS)"); ax_w.set_ylabel("ln(ln(1/(1-Pf)))"); ax_w.legend(); fig_w_exp.tight_layout()
                            buf_w = io.BytesIO(); fig_w_exp.savefig(buf_w, format='png', dpi=200); buf_w.seek(0)
                            w.book.add_worksheet('Plot_Weibull').insert_image('A1', 'p5.png', {'image_data': buf_w})
                            plt.close(fig_w_exp)

                        if 'mean_curve' in locals() and mean_curve:
                            fig_m_exp, ax_m = plt.subplots(figsize=(7,5))
                            ax_m.fill_between(mean_curve["strain"], mean_curve["lower"], mean_curve["upper"], alpha=0.2, color='#555')
                            for name, r in plot_data.items(): ax_m.plot(r["strain"], r["stress"], lw=1, alpha=0.4, color=sample_colors.get(name,"#aaa"))
                            ax_m.plot(mean_curve["strain"], mean_curve["mean"], 'k--', lw=2, label="Mean")
                            ax_m.set_xlabel("Strain (%)"); ax_m.set_ylabel("Stress (MPa)"); ax_m.legend(); fig_m_exp.tight_layout()
                            buf_m = io.BytesIO(); fig_m_exp.savefig(buf_m, format='png', dpi=200); buf_m.seek(0)
                            w.book.add_worksheet('Plot_MeanCurve').insert_image('A1', 'p6.png', {'image_data': buf_m})
                            plt.close(fig_m_exp)

                    st.download_button("📥 Download Excel Report",xl_buf.getvalue(), "Tensile_Report_v4-7.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                except Exception as e: st.error(f"Export error: {e}")
            with ec2:
                st.markdown("**🖼️ 600 DPI Journal TIFF**")
                try:
                    bp2=io.BytesIO(); journal_fig.savefig(bp2,format='png',dpi=600,bbox_inches='tight'); bp2.seek(0)
                    pj=Image.open(bp2); bt2=io.BytesIO(); pj.save(bt2,format='TIFF',compression='tiff_lzw',dpi=(600,600))
                    st.download_button("📥 Download TIFF",bt2.getvalue(), "Journal_600dpi.tiff","image/tiff",use_container_width=True)
                except Exception as e: st.error(f"TIFF error: {e}")
    else:
        st.markdown("""<div style="margin-top:3rem;padding:3rem 2rem;background:#fff;border:1px solid #dde3ec;border-radius:4px;text-align:center;"><div style="font-size:2.5rem;margin-bottom:1rem;">📉</div><div style="font-family:'Playfair Display',Georgia,serif;font-size:1.4rem;color:#002244;margin-bottom:0.5rem;font-weight:700;">Upload tensile data files to begin</div></div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# PAGE 2 — AGEING TREND ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════
else:
    render_header("Ageing Trend Analysis")
    section_hdr("Ageing Data Source","📥")
    ag_src = st.radio("Load ageing data from:", ["Upload summary file (Excel/CSV)", "Use data accumulated in Tensile Analysis"], horizontal=True)

    ag_df = pd.DataFrame()
    if ag_src == "Upload summary file (Excel/CSV)":
        col_up, col_tmpl = st.columns([3,1])
        ag_file = col_up.file_uploader("Upload Ageing Summary File", type=["csv","xlsx"], key="ag_upload")
        col_tmpl.markdown("&nbsp;")
        col_tmpl.download_button("📋 Download Template", template_to_excel(), "Ageing_Template.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        if ag_file: ag_df = load_ageing_data(ag_file)
    else:
        ag_df = st.session_state["ageing_db"].copy()
        if ag_df.empty: st.info("No data accumulated yet. Process files in Tensile Analysis and click **Add to Ageing Database**.")
        else: st.success(f"Loaded {len(ag_df)} rows from Tensile Analysis session.")

    if ag_df is None or (isinstance(ag_df, pd.DataFrame) and ag_df.empty): st.stop()

    for a_col in TENSILE_TO_AGEING.values():
        raw = a_col+"_SD"
        if raw in ag_df.columns:
            nice = {"E_MPa":"E_SD","UTS_MPa":"UTS_SD","Yield_MPa":"Yield_SD","Elongation_pct":"Elongation_SD","Toughness_MJm3":"Toughness_SD","Resilience_MJm3":"Resilience_SD"}.get(a_col, raw)
            ag_df.rename(columns={raw: nice}, inplace=True)

    SD_COLS = {"E_MPa":"E_SD","UTS_MPa":"UTS_SD","Yield_MPa":"Yield_SD","Elongation_pct":"Elongation_SD","Toughness_MJm3":"Toughness_SD","Resilience_MJm3":"Resilience_SD"}
    formulations = sorted(ag_df["Formulation"].dropna().unique().tolist())
    conditions   = sorted(ag_df["Condition"].dropna().unique().tolist())
    avail_props  = [k for k in AGEING_PROPS if k in ag_df.columns]
    avail_days   = sorted(ag_df["Days"].dropna().unique().astype(int).tolist())

    cond_colors = {}
    ov_cnt = uv_cnt = 0
    for c in conditions:
        if "oven" in c.lower(): cond_colors[c] = OVEN_SHADES[ov_cnt % len(OVEN_SHADES)]; ov_cnt+=1
        elif "uv" in c.lower() or "xen" in c.lower(): cond_colors[c] = UV_SHADES[uv_cnt  % len(UV_SHADES)];   uv_cnt+=1
        else: cond_colors[c] = PALETTE[(ov_cnt+uv_cnt) % len(PALETTE)]

    form_markers = {f: ['circle','square','diamond','triangle-up','cross','star','pentagon'][i%7] for i,f in enumerate(formulations)}

    st.markdown("---")
    k1,k2,k3,k4,k5 = st.columns(5)
    k1.metric("Formulations", len(formulations)); k2.metric("Conditions", len(conditions))
    k3.metric("Time Points", len(avail_days)); k4.metric("Properties", len(avail_props))
    k5.metric("Data Rows", len(ag_df))
    st.markdown("---")

    ag_tabs = st.tabs(["📈 Property Trends", "🔄 Retention Analysis", "⚗️ Degradation Kinetics", "🔆 Oven vs UV Head-to-Head", "🕸️ Multi-Property Radar", "⏱️ Service Life Prediction", "📊 Statistics & ANOVA", "🌡️ Arrhenius Analysis", "💾 Export"])

    with ag_tabs[0]:
        section_hdr("Mechanical Property vs Ageing Time","📈","#002244")
        pt_prop = st.selectbox("Property", avail_props, format_func=lambda k: f"{AGEING_PROP_LABELS[k]} ({AGEING_PROP_UNITS[k]})")
        pt_forms = st.multiselect("Formulations", formulations, default=formulations)
        pt_conds = st.multiselect("Conditions", conditions, default=conditions)

        fig_pt = go.Figure()
        for form in pt_forms:
            for cond in pt_conds:
                sub = ag_df[(ag_df["Formulation"]==form)&(ag_df["Condition"]==cond)].sort_values("Days")
                if sub.empty or pt_prop not in sub.columns: continue
                vals, days_ = sub[pt_prop].values, sub["Days"].values.astype(float)
                ns = sub.get("n", pd.Series([5]*len(sub))).fillna(5).values
                ci = [compute_ci(m, sub[SD_COLS.get(pt_prop,"")].iloc[i] if SD_COLS.get(pt_prop,"") in sub.columns else 0, ns[i]) for i,m in enumerate(vals)]
                col, mark, lbl = cond_colors.get(cond, "#002244"), form_markers.get(form, "circle"), f"{form} — {cond}"
                dash = "dash" if ("uv" in cond.lower() or "xen" in cond.lower()) else "solid"

                if ag_show_ci: fig_pt.add_trace(go.Scatter(x=np.concatenate([days_, days_[::-1]]), y=np.concatenate([vals+ci, (vals-ci)[::-1]]), fill='toself', fillcolor=f"rgba({','.join(str(int(int(col.lstrip('#')[i:i+2],16))) for i in (0,2,4))},0.12)", line=dict(width=0), showlegend=False, hoverinfo='skip'))
                fig_pt.add_trace(go.Scatter(x=days_, y=vals, name=lbl, mode='lines+markers', line=dict(color=col, width=2.5, dash=dash), marker=dict(symbol=mark, size=10, color=col, line=dict(width=2, color='#fff')), error_y=dict(type='data', array=ci, visible=ag_show_ci, color=col, thickness=1.5, width=5)))

        fig_pt.update_layout(plot_bgcolor='#fff', paper_bgcolor='#fff', height=600, xaxis=dict(title="<b>Ageing Time (days)</b>", tickvals=avail_days, range=[-1, max(avail_days)*1.08], **AXIS), yaxis=dict(title=f"<b>{AGEING_PROP_LABELS[pt_prop]} ({AGEING_PROP_UNITS[pt_prop]})</b>", rangemode='tozero', **AXIS), margin=dict(l=65,r=40,t=25,b=60))
        st.plotly_chart(fig_pt, use_container_width=True, config=JCFG)

    with ag_tabs[1]:
        section_hdr("Property Retention Analysis (% of Day-0 Value)","🔄","#002244")
        ret_prop = st.selectbox("Property", avail_props, format_func=lambda k: f"{AGEING_PROP_LABELS[k]} ({AGEING_PROP_UNITS[k]})", key="ret_prop")
        ret_forms = st.multiselect("Formulations", formulations, default=formulations, key="ret_f")
        ret_conds = st.multiselect("Conditions", conditions, default=conditions, key="ret_c")

        fig_ret = go.Figure()
        fig_ret.add_hline(y=ag_failure_thresh, line=dict(color='#c0392b', width=1.5, dash='dot'), annotation_text=f"Failure threshold {ag_failure_thresh}%")

        retention_table = []
        for form in ret_forms:
            for cond in ret_conds:
                days_, ret_ = get_retention(ag_df, form, cond, ret_prop)
                if all(np.isnan(r) for r in ret_): continue
                col, mark, lbl = cond_colors.get(cond,"#002244"), form_markers.get(form,"circle"), f"{form} — {cond}"
                fig_ret.add_trace(go.Scatter(x=days_, y=ret_, name=lbl, mode='lines+markers', line=dict(color=col, width=2.5, dash="dash" if ("uv" in cond.lower() or "xen" in cond.lower()) else "solid"), marker=dict(symbol=mark, size=10, color=col, line=dict(width=2, color='#fff'))))
                row = {"Formulation":form,"Condition":cond}
                for d,r in zip(days_,ret_): row[f"Day {int(d)}"] = f"{r:.1f}%" if not np.isnan(r) else "—"
                row["AUC Retention Score"] = f"{compute_auc_retention([d for d,r in zip(days_,ret_) if not np.isnan(r)], [r for r in ret_ if not np.isnan(r)]):.1f}%"
                retention_table.append(row)

        fig_ret.update_layout(plot_bgcolor='#fff', paper_bgcolor='#fff', height=560, xaxis=dict(title="<b>Ageing Time (days)</b>", tickvals=avail_days, range=[-1, max(avail_days)*1.08], **AXIS), yaxis=dict(title=f"<b>Retention of {AGEING_PROP_LABELS[ret_prop]} (%)</b>", range=[0, 110], **AXIS), margin=dict(l=65,r=40,t=25,b=60))
        st.plotly_chart(fig_ret, use_container_width=True, config=JCFG)

        section_hdr("Retention Heatmap (All Properties × Formulation × Condition)","🗺️","#002244")
        heat_day = st.selectbox("Ageing Day for Heatmap", avail_days, index=len(avail_days)-1, key="hday")
        heat_rows=[]; heat_labels=[]
        for prop_k in avail_props:
            row_vals=[]
            for form in formulations:
                for cond in conditions:
                    sub=ag_df[(ag_df["Formulation"]==form)&(ag_df["Condition"]==cond)&(ag_df["Days"]==heat_day)]
                    sub0=ag_df[(ag_df["Formulation"]==form)&(ag_df["Condition"]==cond)&(ag_df["Days"]==0)]
                    if sub.empty or sub0.empty or prop_k not in ag_df.columns: row_vals.append(np.nan); continue
                    v=sub[prop_k].values[0]; v0=sub0[prop_k].values[0]
                    row_vals.append(round(v/v0*100,1) if v0 and v0!=0 else np.nan)
            heat_rows.append(row_vals); heat_labels.append(AGEING_PROP_LABELS[prop_k])
        x_labels=[f"{f}\n{c}" for f in formulations for c in conditions]
        fig_hm = go.Figure(go.Heatmap(z=heat_rows, x=x_labels, y=heat_labels, colorscale=[[0,'#c0392b'],[0.5,'#f39c12'],[1,'#1e8449']], zmid=100, zmin=50, zmax=110, text=[[f"{v:.1f}%" if not np.isnan(v) else "—" for v in row] for row in heat_rows], texttemplate="%{text}", textfont=dict(size=11, family="IBM Plex Mono"), hovertemplate="<b>%{y}</b><br>%{x}<br>Retention = %{text}<extra></extra>", colorbar=dict(title="Retention (%)", ticksuffix="%")))
        fig_hm.update_layout(plot_bgcolor='#fff', paper_bgcolor='#fff', height=max(300, len(avail_props)*55+80), xaxis=dict(tickfont=dict(size=11), side='bottom'), yaxis=dict(tickfont=dict(size=11)), margin=dict(l=140,r=60,t=30,b=60))
        st.plotly_chart(fig_hm, use_container_width=True, config=JCFG)
        
        if retention_table:
            st.markdown("---")
            st.dataframe(pd.DataFrame(retention_table), hide_index=True, use_container_width=True)

    with ag_tabs[2]:
        section_hdr("Degradation Kinetics Model Fitting","⚗️","#1a3a1a")
        kin_prop = st.selectbox("Property for Kinetics", avail_props, format_func=lambda k: f"{AGEING_PROP_LABELS[k]} ({AGEING_PROP_UNITS[k]})",key="kp")
        kin_forms = st.multiselect("Formulations", formulations, default=formulations[:1], key="kf")
        kin_conds = st.multiselect("Conditions", conditions, default=conditions, key="kc")
        t_ext2, kin_summary = np.linspace(0, max(avail_days)*1.6, 200), []

        for form in kin_forms:
            for cond in kin_conds:
                days_, ret_ = get_retention(ag_df, form, cond, kin_prop)
                valid = [(d,r) for d,r in zip(days_,ret_) if not np.isnan(r)]
                if len(valid) < 3: continue
                vd,vr = zip(*valid)
                fit_results = fit_degradation_models(list(vd), list(vr))
                if not fit_results: continue

                col, mark, lbl = cond_colors.get(cond,"#002244"), form_markers.get(form,"circle"), f"{form} — {cond}"
                fig_k = go.Figure()
                fig_k.add_hline(y=ag_failure_thresh, line=dict(color='#c0392b',width=1,dash='dot'))
                fig_k.add_trace(go.Scatter(x=list(vd), y=list(vr), mode='markers', name="Data", marker=dict(symbol=mark,size=12,color=col,line=dict(width=2,color='#fff'))))
                
                if ag_show_fit:
                    for mname, mres in fit_results.items():
                        pred_ext = None
                        if mname == "Linear": pred_ext = mres['params'].get('R0', 100) - mres['params'].get('k (MPa/day)', 0) * t_ext2
                        elif mname == "First-order": pred_ext = 100.0 * np.exp(-mres['params'].get('k (day⁻¹)', 0) * t_ext2)
                        elif mname == "Power-law": pred_ext = 100.0 * (1 + t_ext2)**(-mres['params'].get('n (exponent)', 0))
                        elif mname == "Two-phase Exp." and HAS_SCIPY: pred_ext = mres['params'].get('A (fast %)', 70) * np.exp(-mres['params'].get('k₁ (fast day⁻¹)', 0.05) * t_ext2) + (100 - mres['params'].get('A (fast %)', 70)) * np.exp(-mres['params'].get('k₂ (slow day⁻¹)', 0.005) * t_ext2)
                        if pred_ext is not None: fig_k.add_trace(go.Scatter(x=t_ext2, y=pred_ext, mode='lines', name=f"{mname} (R²={mres['r2']})", line=dict(color={"Linear":"#002244","First-order":"#c9a84c","Power-law":"#1e8449","Two-phase Exp.":"#7d3c98"}.get(mname,'#555'), width=2, dash='dot' if mname!="First-order" else 'solid')))

                fig_k.update_layout(title=dict(text=f"<b>{lbl}</b>",font=dict(size=14,color='#002244'),x=0.01), plot_bgcolor='#fff', paper_bgcolor='#fff', height=430, xaxis=dict(title="<b>Ageing Time (days)</b>", range=[0, max(avail_days)*1.65], tickvals=avail_days, **AXIS), yaxis=dict(title=f"<b>Retention of {AGEING_PROP_LABELS[kin_prop]} (%)</b>", range=[0,110], **AXIS), margin=dict(l=65,r=40,t=45,b=60))
                st.plotly_chart(fig_k, use_container_width=True, config=JCFG)
                
                for mname,mres in fit_results.items():
                    row = {"Formulation":form,"Condition":cond,"Model":mname,"R²":mres["r2"]}
                    row.update(mres["params"]); kin_summary.append(row)

        if kin_summary: st.dataframe(pd.DataFrame(kin_summary), hide_index=True, use_container_width=True)

    with ag_tabs[3]:
        section_hdr("Oven vs UV-Xenon Direct Comparison","🔆","#4a1a00")
        hh_prop = st.selectbox("Property", avail_props, format_func=lambda k: f"{AGEING_PROP_LABELS[k]} ({AGEING_PROP_UNITS[k]})",key="hh")
        hh_forms = st.multiselect("Formulations",formulations,default=formulations,key="hhf")
        oven_cond = [c for c in conditions if "oven" in c.lower()][0] if [c for c in conditions if "oven" in c.lower()] else None
        uv_cond = [c for c in conditions if "uv" in c.lower() or "xen" in c.lower()][0] if [c for c in conditions if "uv" in c.lower() or "xen" in c.lower()] else None

        if not (oven_cond or uv_cond): st.warning("No 'Oven' or 'UV' conditions detected.")
        else:
            rate_rows = []
            for form in hh_forms:
                fig_hh = make_subplots(rows=1, cols=2, subplot_titles=[f"Retention — {form}", f"Rate Comparison — {form}"])
                for cond, color_c in [(oven_cond, OVEN_COL),(uv_cond, UV_COL)]:
                    if cond is None: continue
                    days_, ret_ = get_retention(ag_df, form, cond, hh_prop)
                    valid = [(d,r) for d,r in zip(days_,ret_) if not np.isnan(r)]
                    if not valid: continue
                    vd,vr=zip(*valid)
                    fig_hh.add_trace(go.Scatter(x=list(vd),y=list(vr),name=cond,mode='lines+markers', line=dict(color=color_c,width=2.5,dash="solid" if "oven" in cond.lower() else "dash"), marker=dict(size=9,color=color_c,line=dict(width=2,color='#fff'))), row=1,col=1)
                    rate_rows.append({"Formulation":form,"Condition":cond, "Deg. Rate (%/day)": round(compute_degradation_rate(list(vd),list(vr)),4)})
                
                ov_rate = next((r["Deg. Rate (%/day)"] for r in rate_rows if r["Formulation"]==form and r.get("Condition")==oven_cond), np.nan)
                uv_rate = next((r["Deg. Rate (%/day)"] for r in rate_rows if r["Formulation"]==form and r.get("Condition")==uv_cond),  np.nan)
                if ov_rate or uv_rate: fig_hh.add_trace(go.Bar(x=[oven_cond, uv_cond],y=[ov_rate, uv_rate], marker_color=[OVEN_COL, UV_COL],showlegend=False),row=1,col=2)
                fig_hh.update_layout(plot_bgcolor='#fff',paper_bgcolor='#fff',height=430)
                st.plotly_chart(fig_hh, use_container_width=True, config=JCFG)

    with ag_tabs[4]:
        section_hdr("Multi-Property Radar Chart (Retention %)","🕸️","#1a003a")
        rad_forms = st.multiselect("Formulations", formulations, default=formulations[:2], key="rdf")
        rad_conds = st.multiselect("Conditions",   conditions,   default=conditions[:1],   key="rdc")
        rad_days  = st.multiselect("Days to compare", avail_days, default=[0, avail_days[-1]], key="rdd")

        prop_names = [AGEING_PROP_LABELS[k] for k in avail_props]
        prop_cols  = avail_props

        fig_rad = go.Figure()
        for form in rad_forms:
            for cond in rad_conds:
                for day in rad_days:
                    sub0 = ag_df[(ag_df["Formulation"]==form)&(ag_df["Condition"]==cond)&(ag_df["Days"]==0)]
                    sub  = ag_df[(ag_df["Formulation"]==form)&(ag_df["Condition"]==cond)&(ag_df["Days"]==day)]
                    if sub0.empty or sub.empty: continue
                    r_vals=[]
                    for pc in prop_cols:
                        if pc not in ag_df.columns: r_vals.append(np.nan); continue
                        v=sub[pc].values[0]; v0=sub0[pc].values[0]
                        r_vals.append(round(v/v0*100,1) if v0 and v0!=0 else np.nan)
                    if all(np.isnan(v) for v in r_vals): continue
                    r_disp = [v if not np.isnan(v) else 0 for v in r_vals]
                    col = cond_colors.get(cond,"#002244")
                    dash_r= "dash" if ("uv" in cond.lower() or "xen" in cond.lower()) else "solid"
                    lbl = f"{form} — {cond} — Day {day}"
                    fig_rad.add_trace(go.Scatterpolar(
                        r=r_disp+[r_disp[0]], theta=prop_names+[prop_names[0]], name=lbl, mode='lines+markers',
                        line=dict(color=col, width=2, dash=dash_r), marker=dict(color=col, size=7), opacity=0.85 if day==0 else 1.0,
                        fill='toself', fillcolor=f"rgba({','.join(str(int(col.lstrip('#')[i:i+2],16)) for i in (0,2,4))},0.08)"))
        fig_rad.add_trace(go.Scatterpolar(r=[100]*len(prop_names)+[100], theta=prop_names+[prop_names[0]], name="100% Reference", mode='lines', line=dict(color='#c0392b', width=1, dash='dot'), opacity=0.6))
        fig_rad.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,120], tickfont=dict(size=10,family="IBM Plex Mono"), ticksuffix="%", gridcolor='#e0e0e0'), angularaxis=dict(tickfont=dict(size=12,family="IBM Plex Sans",color='#002244'))), showlegend=True, legend=dict(font=dict(family="Times New Roman",size=11)), paper_bgcolor='#fff', height=580, margin=dict(l=60,r=60,t=40,b=40))
        st.plotly_chart(fig_rad, use_container_width=True, config=JCFG)

    with ag_tabs[5]:
        section_hdr("Service Life Prediction & Extrapolation","⏱️","#1a1a3a")
        sl_prop  = st.selectbox("Property", avail_props, format_func=lambda k: f"{AGEING_PROP_LABELS[k]} ({AGEING_PROP_UNITS[k]})", key="slp")
        sl_forms = st.multiselect("Formulations", formulations, default=formulations, key="slf")
        sl_conds = st.multiselect("Conditions",   conditions,   default=conditions,   key="slc")
        sl_model = st.selectbox("Kinetic Model for Prediction", ["First-order","Power-law","Linear","Two-phase Exp."])
        sl_extdays= st.slider("Extrapolation Horizon (days)", 28, 365, 90)

        t_sl = np.linspace(0, sl_extdays, 400)
        fig_sl = go.Figure()
        fig_sl.add_vline(x=max(avail_days), line=dict(color='#5a6a7e',width=1.5,dash='dash'))
        fig_sl.add_hline(y=ag_failure_thresh, line=dict(color='#c0392b',width=1.5,dash='dot'), annotation_text=f"Failure threshold {ag_failure_thresh}%")

        sl_table = []
        for form in sl_forms:
            for cond in sl_conds:
                days_, ret_ = get_retention(ag_df, form, cond, sl_prop)
                valid = [(d,r) for d,r in zip(days_,ret_) if not np.isnan(r)]
                if len(valid) < 3: continue
                vd,vr = zip(*valid)
                fits = fit_degradation_models(list(vd),list(vr))
                if not fits or sl_model not in fits: continue
                mres = fits[sl_model]
                col, mark, dash, lbl = cond_colors.get(cond,"#002244"), form_markers.get(form,"circle"), "dash" if ("uv" in cond.lower() or "xen" in cond.lower()) else "solid", f"{form} — {cond}"

                fig_sl.add_trace(go.Scatter(x=list(vd),y=list(vr),mode='markers', name=f"{lbl} (data)",showlegend=True, marker=dict(symbol=mark,size=10,color=col,line=dict(width=2,color='#fff'))))
                
                pred_sl = np.clip(mres["pred"][:len(t_sl)] if len(mres["pred"])>=len(t_sl) else np.interp(t_sl, np.linspace(0,max(avail_days),len(mres["pred"])), mres["pred"]), 0, 110)
                kp = mres["params"]
                if sl_model == "First-order": pred_sl = 100.0*np.exp(-kp.get('k (day⁻¹)',0)*t_sl)
                elif sl_model == "Linear": pred_sl = np.maximum(kp.get('R0',100) - kp.get('k (MPa/day)',0)*t_sl, 0)
                elif sl_model == "Power-law": pred_sl = 100.0*(1+t_sl)**(-kp.get('n (exponent)',0))
                elif sl_model == "Two-phase Exp." and HAS_SCIPY: pred_sl = kp.get('A (fast %)',70)*np.exp(-kp.get('k₁ (fast day⁻¹)',0.05)*t_sl)+(100-kp.get('A (fast %)',70))*np.exp(-kp.get('k₂ (slow day⁻¹)',0.005)*t_sl)

                in_mask = t_sl <= max(avail_days)
                fig_sl.add_trace(go.Scatter(x=t_sl[in_mask],y=pred_sl[in_mask],mode='lines', name=lbl,line=dict(color=col,width=2.5,dash=dash),showlegend=False))
                fig_sl.add_trace(go.Scatter(x=t_sl[~in_mask],y=pred_sl[~in_mask],mode='lines', name=f"{lbl} (extrap.)",line=dict(color=col,width=2,dash='dot'), opacity=0.75,showlegend=False))

                sl_fn = mres.get("service_life_fn")
                t_fail = sl_fn(ag_failure_thresh) if sl_fn else np.inf
                if np.isfinite(t_fail) and t_fail <= sl_extdays:
                    fig_sl.add_trace(go.Scatter(x=[t_fail],y=[ag_failure_thresh],mode='markers', name=f"t_f {lbl}={t_fail:.0f}d", marker=dict(symbol='x',size=16,color=col, line=dict(width=3,color='#c0392b')),showlegend=True))
                sl_table.append({"Formulation":form,"Condition":cond,"Model":sl_model,"R²":mres["r2"], f"Service Life @ {ag_failure_thresh}% retention (days)": f"{t_fail:.0f}" if np.isfinite(t_fail) else ">365", "Degradation Rate (%/day)":compute_degradation_rate(list(vd),list(vr)), "Equation":mres["eq"]})

        fig_sl.update_layout(plot_bgcolor='#fff', paper_bgcolor='#fff', height=600, xaxis=dict(title="<b>Ageing Time (days)</b>",range=[0,sl_extdays], **AXIS), yaxis=dict(title=f"<b>Retention of {AGEING_PROP_LABELS[sl_prop]} (%)</b>", range=[0,110], **AXIS), margin=dict(l=65,r=40,t=25,b=60))
        st.plotly_chart(fig_sl, use_container_width=True, config=JCFG)
        if sl_table: st.dataframe(pd.DataFrame(sl_table), hide_index=True, use_container_width=True)

    with ag_tabs[6]:
        section_hdr("Batch Statistics & One-Way ANOVA","📊","#1a1a00")
        stat_prop = st.selectbox("Property", avail_props, format_func=lambda k: f"{AGEING_PROP_LABELS[k]} ({AGEING_PROP_UNITS[k]})", key="sp")
        stat_cond = st.selectbox("Condition", conditions, key="sc")

        stat_rows = []
        for form in formulations:
            sub = ag_df[(ag_df["Formulation"]==form)&(ag_df["Condition"]==stat_cond)].sort_values("Days")
            if sub.empty or stat_prop not in sub.columns: continue
            for _, row in sub.iterrows():
                m, sd_, n_ = row.get(stat_prop, np.nan), row.get(SD_COLS.get(stat_prop,""), np.nan), row.get("n",5)
                ret_=(m/sub[sub["Days"]==0][stat_prop].values[0]*100 if len(sub[sub["Days"]==0])>0 and sub[sub["Days"]==0][stat_prop].values[0]!=0 else np.nan)
                stat_rows.append({"Formulation":form, "Days":int(row["Days"]), "Mean":round(m,3) if not np.isnan(m) else "—", "SD":round(sd_,3) if not np.isnan(sd_) else "—", "n":int(n_), "95% CI ±":round(compute_ci(m, sd_, n_),3), f"Retention (%)":round(ret_,1) if not np.isnan(ret_) else "—", "CV (%)":round(sd_/m*100,1) if (not np.isnan(sd_) and m and m!=0) else "—"})
        if stat_rows: st.dataframe(pd.DataFrame(stat_rows), hide_index=True, use_container_width=True)

        if HAS_SCIPY:
            anova_rows=[]
            for form in formulations:
                sub = ag_df[(ag_df["Formulation"]==form)&(ag_df["Condition"]==stat_cond)]
                groups=[]
                for day in avail_days:
                    sd_sub = sub[sub["Days"]==day]
                    if sd_sub.empty or stat_prop not in sd_sub.columns: continue
                    m_, s_, n_ = sd_sub[stat_prop].values[0], sd_sub.get(SD_COLS.get(stat_prop,""), pd.Series([0])).values[0], int(sd_sub.get("n",pd.Series([5])).values[0])
                    if pd.isna(m_) or pd.isna(s_) or n_<2: continue
                    np.random.seed(42); groups.append(np.random.normal(m_, max(s_,1e-6), n_))
                if len(groups) >= 3:
                    try:
                        f_stat, p_val = f_oneway(*groups)
                        anova_rows.append({"Formulation":form,"F-statistic":round(f_stat,3), "p-value":round(p_val,4),"Significant?": "✅ Yes (p<0.05)" if p_val<0.05 else "❌ No (p≥0.05)"})
                    except Exception: pass
            if anova_rows: st.dataframe(pd.DataFrame(anova_rows),hide_index=True,use_container_width=True)
            else: st.info("Insufficient groups for ANOVA (need ≥ 3 time points with n ≥ 2).")

        dsi_rows=[]
        for form in formulations:
            for cond in conditions:
                dsi = compute_dsi(ag_df, form, cond)
                dsi_rows.append({"Formulation":form,"Condition":cond, "DSI (%)":f"{dsi:.1f}" if not np.isnan(dsi) else "—", "Assessment":("🟢 Excellent" if dsi>=95 else "🟡 Moderate" if dsi>=85 else "🟠 Significant" if dsi>=75 else "🔴 Severe")})
        if dsi_rows: st.dataframe(pd.DataFrame(dsi_rows),hide_index=True,use_container_width=True)

    with ag_tabs[7]:
        section_hdr("Arrhenius Activation Energy Estimation","🌡️","#3a0000")
        if not use_arrhenius:
            st.info("Enable **Arrhenius Analysis** in the sidebar to use this tab.")
        else:
            try: arr_temps = [float(t.strip()) for t in arr_temps_str.split(",") if t.strip()]
            except ValueError: st.error("Invalid temperature input."); arr_temps=[]

            ov_cs = [c for c in conditions if "oven" in c.lower()]
            if len(arr_temps) < 2: st.warning("Enter at least 2 oven temperatures separated by commas.")
            elif len(ov_cs) < len(arr_temps): st.warning(f"You specified {len(arr_temps)} temperatures but found only {len(ov_cs)} oven conditions.")
            else:
                arr_prop = st.selectbox("Property for Arrhenius", avail_props, format_func=lambda k: f"{AGEING_PROP_LABELS[k]} ({AGEING_PROP_UNITS[k]})", key="ap")
                arr_model= st.selectbox("Kinetic Model", ["First-order","Power-law","Linear"], key="am")
                arr_form = st.selectbox("Formulation",formulations,key="af")
                R_gas = 8.314e-3
                arr_rows = []
                for temp_C, cond in zip(arr_temps, ov_cs[:len(arr_temps)]):
                    days_,ret_ = get_retention(ag_df, arr_form, cond, arr_prop)
                    valid=[(d,r) for d,r in zip(days_,ret_) if not np.isnan(r)]
                    if len(valid)<3: continue
                    vd,vr=zip(*valid)
                    fits=fit_degradation_models(list(vd),list(vr))
                    if not fits or arr_model not in fits: continue
                    mres=fits[arr_model]
                    k_val = list(mres["params"].values())[0]
                    if isinstance(k_val,float) and k_val>0:
                        T_K = temp_C + 273.15
                        arr_rows.append({"Temp (°C)":temp_C,"T (K)":T_K, "1/T (K⁻¹)":1/T_K,"k":k_val,"ln(k)":np.log(k_val), "Condition":cond})

                if len(arr_rows) >= 2:
                    arr_df = pd.DataFrame(arr_rows); x_arr = arr_df["1/T (K⁻¹)"].values; y_arr = arr_df["ln(k)"].values
                    try:
                        c_arr = np.polyfit(x_arr, y_arr, 1)
                        Ea = -c_arr[0] * R_gas
                        ac1,ac2,ac3 = st.columns(3)
                        ac1.metric("Activation Energy Eₐ (kJ/mol)", f"{Ea:.1f}"); ac2.metric("Pre-exponential A", f"{np.exp(c_arr[1]):.2e}"); ac3.metric("Arrhenius R²", f"{_r2(y_arr, np.polyval(c_arr,x_arr)):.4f}")

                        fig_arr=go.Figure()
                        fig_arr.add_trace(go.Scatter(x=x_arr,y=y_arr,mode='markers', marker=dict(color='#002244',size=12,symbol='circle'),name="Data"))
                        x_fit = np.linspace(x_arr.min()*0.995, x_arr.max()*1.005, 60)
                        fig_arr.add_trace(go.Scatter(x=x_fit,y=np.polyval(c_arr, x_fit),mode='lines', line=dict(color='#c9a84c',width=2.5), name=f"Eₐ={Ea:.1f} kJ/mol"))
                        fig_arr.update_layout(plot_bgcolor='#fff',paper_bgcolor='#fff',height=440, xaxis=dict(title="<b>1/T (K⁻¹)</b>",**AXIS), yaxis=dict(title="<b>ln(k)</b>",**AXIS))
                        st.plotly_chart(fig_arr,use_container_width=True,config=JCFG)
                    except Exception as e: st.error(f"Arrhenius fit failed: {e}")

    with ag_tabs[8]:
        section_hdr("Ageing Report Export","💾","#002244")
        st.markdown("**📊 Full Ageing Excel Report**")
        ag_xl = io.BytesIO()
        try:
            with pd.ExcelWriter(ag_xl, engine='xlsxwriter') as w:
                wb_xl = w.book
                hdr_fmt = wb_xl.add_format({'bold':True,'bg_color':'#002244','font_color':'#f0f4fb','border':1,'align':'center'})
                
                ag_df.to_excel(w, sheet_name='Raw_Ageing_Data', index=False)
                ws0=w.sheets['Raw_Ageing_Data']
                for i,col in enumerate(ag_df.columns): ws0.write(0,i,str(col),hdr_fmt)

                for prop_k in avail_props:
                    ret_mat = []
                    for form in formulations:
                        for cond in conditions:
                            days_,ret_=get_retention(ag_df,form,cond,prop_k)
                            row_r={"Formulation":form,"Condition":cond}
                            for d,r in zip(days_,ret_): row_r[f"Day {int(d)}"]=round(r,1) if not np.isnan(r) else ""
                            row_r["AUC_Score"]=compute_auc_retention([d for d,r in zip(days_,ret_) if not np.isnan(r)], [r for r in ret_ if not np.isnan(r)])
                            ret_mat.append(row_r)
                    if ret_mat: pd.DataFrame(ret_mat).to_excel(w,sheet_name=f"Ret_{AGEING_PROP_LABELS[prop_k][:12].replace(' ','_')}",index=False)

                kin_all=[]
                for prop_k in avail_props:
                    for form in formulations:
                        for cond in conditions:
                            days_,ret_=get_retention(ag_df,form,cond,prop_k)
                            valid=[(d,r) for d,r in zip(days_,ret_) if not np.isnan(r)]
                            if len(valid)<3: continue
                            fits=fit_degradation_models([v[0] for v in valid],[v[1] for v in valid])
                            if not fits: continue
                            for mname,mres in fits.items():
                                r={"Property":AGEING_PROP_LABELS[prop_k],"Formulation":form, "Condition":cond,"Model":mname,"R²":mres["r2"], "Equation":mres["eq"]}
                                r.update(mres["params"])
                                sl_fn=mres.get("service_life_fn")
                                r[f"Service_Life@{ag_failure_thresh}%"]=round(sl_fn(ag_failure_thresh),1) if sl_fn and np.isfinite(sl_fn(ag_failure_thresh)) else ">365"
                                kin_all.append(r)
                if kin_all: pd.DataFrame(kin_all).to_excel(w,sheet_name='Kinetics',index=False)

                dsi_all=[{"Formulation":f,"Condition":c,"DSI (%)":compute_dsi(ag_df,f,c)} for f in formulations for c in conditions]
                pd.DataFrame(dsi_all).to_excel(w,sheet_name='DSI',index=False)

            st.download_button("📥 Download Comprehensive Ageing Report",ag_xl.getvalue(), f"Ageing_Report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        except Exception as e:
            st.error(f"Export error: {e}")
