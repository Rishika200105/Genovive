# -*- coding: utf-8 -*-
# =========================================================
# 🧬 Genovive — Infertility Diagnostic Support (Advanced)
# =========================================================
# Streamlit app for multi-factor screening with hormones,
# genetics, and clinical notes — plus decision support
# for tests, medicines, and next steps.
#
# ⚠️ Educational demo only. Not medical advice.
# =========================================================

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Circle
from datetime import datetime, timedelta

# ============================
# 🎯 Page Config & Theming
# ============================
st.set_page_config(
    page_title="Genovive",
    layout="wide",
    page_icon="🧬",
    initial_sidebar_state="expanded",
)

# ---- Minimal custom CSS for a modern look ----
CUSTOM_CSS = """
<style>
/***** Layout tweaks *****/
:root { --card-bg: #ffffff; --card-br: 18px; --soft-shadow: 0 8px 24px rgba(0,0,0,.08); }

.block-container {padding-top: 1.3rem;}

/***** Fancy title *****/
.huge-title { 
    font-size: 2.2rem; 
    font-weight: 800; 
    letter-spacing: -0.02em; 
    color: #111827 !important;
}
.subtitle { 
    color: #374151 !important;
    font-size: 1.05rem;
}

/***** Card *****/
.card { 
    background: var(--card-bg);
    border-radius: var(--card-br);
    padding: 1.1rem 1.2rem; 
    box-shadow: var(--soft-shadow); 
    border: 1px solid #eef2f7; 
}
.card h3 { margin: 0 .2rem .6rem 0; }

/***** Pills *****/
.pill { 
    display:inline-block; 
    padding:.25rem .6rem; 
    border-radius:999px; 
    background:#f1f5f9; 
    border:1px solid #e5e7eb; 
    margin:.1rem .25rem; 
    font-size:.85rem 
}

/***** Progress tag *****/
.badge {
    font-weight:600; 
    padding:.2rem .5rem; 
    border-radius:8px; 
    background:#eef2ff; 
    color:#3730a3; 
    border:1px solid #e0e7ff;
}

.footer-note { color:#6b7280; font-size:.85rem; }

/***** KPI *****/
.kpi {
    display:flex; align-items:center; justify-content:space-between;
    padding:.6rem .8rem; border:1px dashed #e5e7eb; border-radius:12px;
}
.kpi .value { font-weight:800; font-size:1.1rem; }

/***** Hide Deploy button watermark spacing tweaks *****/
.css-18ni7ap { padding-top: 0px; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown(
    """
    <div class="card" style="margin-bottom: .75rem;">
    <div class="huge-title">🧬 Genovive — Infertility Diagnostic Support</div>
    <div class="subtitle">Multi-factor screening with hormones, genetics, and clinical notes — plus decision support for tests, medicines, and steps recommended.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================
# 🧠 Session State helpers
# ============================
if "history" not in st.session_state:
    st.session_state.history = []  # store tuples of (timestamp, score)

def push_history(score):
    st.session_state.history.append((datetime.now(), float(score)))
    # limit
    st.session_state.history = st.session_state.history[-20:]

# ============================
# 🔧 Sidebar — Inputs
# ============================
st.sidebar.header("📋 Patient Information")

# 🔤 Patient name field (NEW)
patient_name = st.sidebar.text_input("Patient Name (optional)", placeholder="e.g., Riya Sharma")

# Demographics & Hormones
colA, colB = st.sidebar.columns(2)
with colA:
    age = st.sidebar.slider("Age (years)", 18, 50, 30)
    lh = st.sidebar.number_input("LH (IU/L)", min_value=0.0, max_value=50.0, value=5.0, step=0.1)
    estradiol = st.sidebar.number_input("Estradiol (pg/mL)", min_value=0, max_value=1000, value=50, step=1)
with colB:
    bmi = st.sidebar.slider("BMI", 15.0, 40.0, 22.0)
    amh = st.sidebar.number_input("AMH (ng/mL)", min_value=0.0, max_value=15.0, value=2.5, step=0.1)
    fsh = st.sidebar.number_input("FSH (IU/L)", min_value=0.0, max_value=50.0, value=6.0, step=0.1)

# ---- Clinical Notes Builder (NEW)
st.sidebar.markdown("### 🧠 Clinical Notes")
NOTE_TEMPLATES = {
    "Regular cycles, no pain": "Regular cycles, no pain",
    "Irregular cycles / oligomenorrhea": "Irregular cycles present with oligomenorrhea over last 6 months",
    "Pelvic pain & dysmenorrhea (Endometriosis-like)": "Chronic pelvic pain, dysmenorrhea, dyspareunia suspected",
    "PCOS profile": "Features suggestive of PCOS: acne, hirsutism, weight gain",
    "Thyroid symptoms": "History of thyroid issues; fatigue, weight changes",
    "Male factor suspected": "Semen analysis pending; possible motility concerns",
    "Infection/inflammation": "Recurrent UTIs; discharge; pelvic inflammatory signs",
    "Hyperprolactinemia suspicion": "Galactorrhea episodes; menstrual irregularity; prolactin suspected high",
}
note_choice = st.sidebar.selectbox(
    "Choose a note template",
    options=list(NOTE_TEMPLATES.keys()),
    index=0
)
extra_notes = st.sidebar.text_area("Add/Modify Notes", value=NOTE_TEMPLATES[note_choice], height=90)

# ---- Multi-select genes (expanded)
GENE_OPTIONS = [
    "FOXP3", "STAT3", "COL1A1", "COL3A1", "RPL13A", "RPL3", "GATA4", "LHX1-AS1",
    "KLF5-AS1", "TDRD7", "PDGFRB", "ZEB2", "BCL2", "ESR1", "FSHR", "LHCGR",
    "VEGFA", "HIF1A", "MUC1", "ITGB3", "HOXA10", "PGR", "IL6", "TNF"
]
genes = st.sidebar.multiselect(
    "Select Genes of Interest",
    options=GENE_OPTIONS,
    default=["FOXP3", "STAT3", "GATA4", "PGR"],
    help="Choose one or more genes detected/flagged in the patient."
)

# Cycle info (for timeline)
st.sidebar.markdown("### 🗓️ Cycle Information")
cycle_length = st.sidebar.slider("Cycle Length (days)", 21, 35, 28)
last_menses_date = st.sidebar.date_input("Last Menstrual Period (LMP)")

# Action button
run_btn = st.sidebar.button("🔮 Predict & Generate Plan", use_container_width=True)

# ============================
# 📚 Knowledge blocks
# ============================
GENE_INFO = {
    "FOXP3": "Immune tolerance; Treg function; implantation immune balance.",
    "STAT3": "Cytokine signaling; endometrial receptivity; inflammation control.",
    "COL1A1": "Structural ECM; endometrium integrity.",
    "COL3A1": "Tissue remodeling; ECM dynamics.",
    "RPL13A": "Ribosomal stress & protein synthesis (housekeeping).",
    "RPL3": "Ribosomal machinery (housekeeping).",
    "GATA4": "Ovarian development & steroidogenesis.",
    "LHX1-AS1": "Regulates LHX1; uterine development context.",
    "KLF5-AS1": "May impact endometrial receptivity pathways.",
    "TDRD7": "Germ cell development & RNA granules.",
    "PDGFRB": "Growth signaling; stromal cell function; endometrium vascular cues.",
    "ZEB2": "EMT regulator; implantation and remodeling.",
    "BCL2": "Apoptosis regulation; cell survival.",
    "ESR1": "Estrogen receptor alpha; endometrium responsiveness.",
    "FSHR": "FSH receptor; folliculogenesis & ovarian response.",
    "LHCGR": "LH/hCG receptor; ovulation signaling.",
    "VEGFA": "Angiogenesis; endometrial vascularization.",
    "HIF1A": "Hypoxia response; implantation microenvironment.",
    "MUC1": "Endometrial surface; embryo adhesion context.",
    "ITGB3": "Integrin beta-3; implantation adhesion.",
    "HOXA10": "Uterine receptivity and patterning.",
    "PGR": "Progesterone receptor; secretory transformation.",
    "IL6": "Inflammation and cytokine signaling.",
    "TNF": "Inflammation, implantation stress signaling."
}

THERAPY_INSIGHTS = {
    "FOXP3": "Immunotherapy research explores Treg modulation; experimental in reproductive failure.",
    "STAT3": "Targeted anti-inflammatory or JAK/STAT-pathway modulation is under study.",
    "ZEB2": "EMT pathway modulation is a research frontier; not standard of care.",
    "PDGFRB": "Angiogenesis and stromal signaling modulation investigated preclinically.",
    "PGR": "Progesterone support can be considered in luteal phase defects (clinician-guided).",
    "ESR1": "Estrogen priming/replacement may support thin endometrium under supervision."
}

# ============================
# 🧠 Helper Functions
# ============================
def parse_notes(text: str):
    """Tiny NLP: extract flags from free text using simple keyword rules."""
    text_low = text.lower()
    flags = {
        'pcos': any(k in text_low for k in ["pcos", "polycystic", "cysts", "androgen", "hirsutism"]),
        'endometriosis': any(k in text_low for k in ["endometriosis", "pelvic pain", "dyspareunia", "dysmenorrhea"]),
        'irregular_cycles': any(k in text_low for k in ["irregular", "oligomenorrhea", "amenorrhea"]),
        'thyroid': any(k in text_low for k in ["tsh", "thyroid", "hypothyroid", "hyperthyroid"]),
        'male_factor': any(k in text_low for k in ["semen", "sperm", "motility", "count", "morphology"]),
        'infection': any(k in text_low for k in ["infection", "uti", "pid", "inflammation", "discharge"]),
        'hyperprolactinemia': any(k in text_low for k in ["prolactin", "galactorrhea"]),
    }
    return flags

def mock_predict(features, genes_sel, flags):
    """Simple rule-based model, returns (label, confidence [0-1], score [0-100])."""
    age, bmi, amh, fsh, lh, estradiol = features
    # Weighted scoring (0-100)
    score = 0
    # Age contributions
    score += np.interp(age, [18, 50], [5, 25])
    # BMI risk (U-shape, modeled as higher BMI risk)
    score += np.interp(bmi, [18.5, 35], [5, 20])
    # AMH: lower AMH -> higher risk; map reversed
    score += np.interp(amh, [0.1, 6.0], [25, 2])
    # FSH high increases risk
    score += np.interp(fsh, [1.0, 20.0], [2, 18])
    # LH moderately contributes (PCOS-like when high)
    score += np.interp(lh, [1.0, 20.0], [2, 15])
    # Estradiol very low or very high contributes
    if estradiol < 30 or estradiol > 300:
        score += 8
    else:
        score += 3
    # Genetic bumps
    gene_risk = 0
    for g in ["FOXP3","STAT3","GATA4","ZEB2","PDGFRB","ESR1","PGR","FSHR","HOXA10","ITGB3"]:
        if g in genes_sel:
            gene_risk += 2.5
    score += gene_risk
    # Flags
    if flags.get('pcos'): score += 6
    if flags.get('endometriosis'): score += 5
    if flags.get('thyroid'): score += 4
    if flags.get('hyperprolactinemia'): score += 4
    if flags.get('infection'): score += 3
    if flags.get('male_factor'): score += 2

    score = float(np.clip(score, 0, 100))
    label = "Likely Infertile" if score >= 55 else "Likely Fertile"
    confidence = 0.55 + (abs(score-55) / 100)  # mock confidence around decision boundary
    confidence = float(np.clip(confidence, 0.55, 0.95))
    return label, confidence, score

def gauge_chart(score: float):
    """Matplotlib gauge (0-100) returning a fig."""
    fig, ax = plt.subplots(figsize=(5.8, 3.5))
    ax.axis('off')
    # Gauge background
    wedge_bg = Wedge((0.5, 0), 0.45, 0, 180, fc='#f4f5f7', ec='#e5e7eb')
    ax.add_patch(wedge_bg)
    # Zones
    zones = [
        (0, 35, '#d1fae5'),   # low risk
        (35, 55, '#fef3c7'),  # moderate
        (55, 100, '#fee2e2')  # high
    ]
    for start, end, color in zones:
        ax.add_patch(Wedge((0.5, 0), 0.45,
                    np.interp(start,[0,100],[0,180]),
                    np.interp(end,[0,100],[0,180]),
                    fc=color, ec='white'))
    # Needle
    angle = np.interp(score, [0, 100], [0, 180])
    theta = np.deg2rad(angle)
    x, y = 0.5 + 0.40*np.cos(theta), 0.0 + 0.40*np.sin(theta)
    ax.plot([0.5, x], [0.0, y])
    ax.add_patch(Circle((0.5, 0), 0.015, color='black'))
    # Label
    band = "Low" if score < 35 else ("Moderate" if score < 55 else "High")
    ax.text(0.5, -0.1, f"Risk Index: {score:.0f}/100 ({band})",
            ha='center', va='center', fontsize=12, fontweight='bold')
    return fig

def gene_importance_chart(genes_list):
    rng = np.random.default_rng(42)
    imp = rng.random(len(genes_list))
    fig, ax = plt.subplots()
    ax.barh(genes_list, imp)
    ax.set_xlabel("Importance")
    ax.set_title("Gene Contribution to Infertility")
    return fig

def clinical_factors_chart(values_dict):
    fig, ax = plt.subplots()
    ax.bar(list(values_dict.keys()), list(values_dict.values()))
    ax.set_ylabel("Value")
    ax.set_title("Clinical Factors")
    return fig

def radar_chart(genes_list):
    if len(genes_list) < 3:
        return None
    rng = np.random.default_rng(7)
    values = rng.random(len(genes_list))
    angles = np.linspace(0, 2*np.pi, len(genes_list), endpoint=False)
    values = np.concatenate((values, [values[0]]))
    angles = np.concatenate((angles, [angles[0]]))
    fig = plt.figure(figsize=(5,5))
    ax = fig.add_subplot(111, polar=True)
    ax.plot(angles, values, 'o-', linewidth=2)
    ax.fill(angles, values, alpha=0.25)
    ax.set_thetagrids(np.degrees(angles[:-1]), genes_list)
    ax.set_title("Gene Pattern Radar")
    return fig

def fertile_window_heatmap(lmp: datetime, cycle_len: int):
    """Create a simple 28-35 day cycle probability curve."""
    days = np.arange(cycle_len)
    ov_day = int(cycle_len * 0.5)
    probs = np.exp(-0.5*((days-ov_day)/2.0)**2)  # Gaussian around ov_day
    probs = probs / probs.max()
    fig, ax = plt.subplots()
    ax.plot(days, probs)
    ax.set_xlabel("Day of Cycle")
    ax.set_ylabel("Conception Probability")
    ax.set_title("Fertile Window Predictor")
    return fig

def uterine_3d_plot(estradiol_val, fsh_val):
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    fig = plt.figure(figsize=(5.5, 4.2))
    ax = fig.add_subplot(111, projection='3d')
    x = np.linspace(-2,2,50)
    y = np.linspace(-2,2,50)
    X, Y = np.meshgrid(x, y)
    base = np.exp(-(X**2+Y**2))
    thickness = np.interp(estradiol_val, [10, 300], [5.5, 10.5]) - np.interp(fsh_val, [1, 20], [0, 2.0])
    Z = base * (thickness/10.0)
    ax.plot_surface(X, Y, Z, linewidth=0, antialiased=True)
    ax.set_title("Endometrium Thickness Landscape")
    return fig

# --- Decision Support: Tests & Medicines (EXPANDED) ---
def suggest_tests(hormones, genes_sel, flags):
    age, bmi, amh, fsh, lh, estradiol = hormones
    tests = []

    # Hormone-related
    if estradiol < 30: tests.append("Estradiol Day-3 repeat")
    if amh < 1.0: tests.append("Antral Follicle Count (AFC) via ultrasound")
    if fsh > 10: tests.append("Repeat Day-3 FSH + Estradiol")
    if bmi > 30: tests.append("Oral Glucose Tolerance Test (OGTT)")

    # PCOS pathway
    if flags.get('pcos') or lh > 12 or bmi >= 27:
        tests += ["Free testosterone", "DHEA-S", "Fasting insulin + HOMA-IR"]

    # Endometriosis pathway
    if flags.get('endometriosis'):
        tests += ["Transvaginal USG / MRI pelvis", "CA-125 (supportive, not diagnostic)"]

    # Thyroid pathway
    if flags.get('thyroid'):
        tests += ["TSH", "Free T4", "Anti-TPO antibodies"]

    # Male factor
    if flags.get('male_factor'):
        tests += ["Semen analysis (WHO 2021)", "DNA fragmentation index (if indicated)"]

    # Infection/inflammation
    if flags.get('infection'):
        tests += ["Cervical/vaginal swab culture", "CRP/ESR (inflammation markers)"]

    # Hyperprolactinemia
    if flags.get('hyperprolactinemia'):
        tests += ["Serum Prolactin (fasting, repeat if elevated)"]

    # Imaging/structure
    tests += ["HSG (Fallopian tube patency)"]
    # Gene-specific add-ons
    if "FOXP3" in genes_sel: tests.append("Immune profiling (Tregs, autoantibodies)")
    if "ZEB2" in genes_sel: tests.append("Endometrial biopsy – EMT markers")
    if "PDGFRB" in genes_sel: tests.append("Endometrial receptivity assay / Doppler blood flow")
    if "ESR1" in genes_sel or "PGR" in genes_sel: tests.append("Endometrial thickness tracking across cycle")
    # De-duplicate
    tests = list(dict.fromkeys(tests))
    return tests

def suggest_medicines(hormones, genes_sel, flags):
    age, bmi, amh, fsh, lh, estradiol = hormones
    recs = []

    # Ovulation induction / ovarian support
    if fsh > 12 or lh > 12:
        recs += ["Letrozole – ovulation induction", "Clomiphene Citrate – ovulation induction"]
    if amh < 1.5:
        recs += ["DHEA (discuss dosing) – may support ovarian reserve", "CoQ10 – mitochondrial support"]

    # PCOS/Metabolic
    if flags.get('pcos') or (bmi >= 27):
        recs += ["Metformin – if insulin resistance suspected", "Myo-inositol + D-chiro-inositol"]

    # Luteal / endometrium support
    if "PGR" in genes_sel or estradiol < 50:
        recs += ["Progesterone support (luteal phase, clinician-guided)"]
    if "ESR1" in genes_sel:
        recs += ["Estrogen priming protocol for thin endometrium (specialist care)"]

    # Inflammation/immune
    if "STAT3" in genes_sel or flags.get('endometriosis') or flags.get('infection'):
        recs += ["Anti-inflammatory plan (e.g., omega-3, short NSAID course if appropriate)"]
    if "FOXP3" in genes_sel:
        recs += ["Immunomodulatory strategy – consider Treg support (specialist)"]

    # Thyroid / Prolactin / General
    if flags.get('thyroid'):
        recs += ["Levothyroxine – if hypothyroid (target TSH per guidelines)"]
    if flags.get('hyperprolactinemia'):
        recs += ["Cabergoline – if prolactin confirmed high (endocrinology)"]
    recs += ["Folic acid 400–800 µg/day", "Vitamin D repletion if low"]

    # De-duplicate
    recs = list(dict.fromkeys(recs))
    return recs

def agentic_next_steps(score, flags, tests, meds):
    steps = []
    if score >= 55:
        steps.append("Re-test key hormones in next cycle window (Day 2–4)")
        steps.append("Schedule transvaginal ultrasound for AFC and endometrium assessment")
        if flags.get('pcos'): steps.append("Initiate PCOS pathway: nutrition + insulin resistance workup")
        if flags.get('endometriosis'): steps.append("Refer for laparoscopy consult if pain severe")
        steps.append("Begin 12-week lifestyle protocol alongside medication trial")
        steps.append("Set follow-up at 6–8 weeks to evaluate response")
    else:
        steps.append("Maintain lifestyle optimization; track cycles for 3 months")
        steps.append("Time intercourse/IUI during predicted fertile window")
        if flags.get('thyroid'): steps.append("TSH optimization with endocrinology consult")
    if len(tests) > 0: steps.append("Order tests: " + ", ".join(tests[:5]) + ("…" if len(tests)>5 else ""))
    if len(meds) > 0: steps.append("Start/consider meds: " + ", ".join(meds[:5]) + ("…" if len(meds)>5 else ""))
    return steps

# ============================
# ▶️ Main Run
# ============================
if run_btn:
    notes = extra_notes
    flags = parse_notes(notes)
    features = [age, bmi, amh, fsh, lh, estradiol]
    label, confidence, score = mock_predict(features, genes, flags)
    push_history(score)

    # --- Top summary cards ---
    c1, c2, c3, c4 = st.columns([1,1,1,1])
    with c1:
        st.markdown(f"""
        <div class='card'>
        <h3>🔮 Prediction</h3>
    <div><span class='badge'>{label}</span></div>
<div class='footer-note'>Confidence: {confidence:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        fig_g = gauge_chart(score)
        st.pyplot(fig_g, use_container_width=True)
    with c3:
        # Inputs Snapshot
        st.markdown("<div class='card'><h3>🧪 Inputs Snapshot</h3>", unsafe_allow_html=True)
        if patient_name:
            st.markdown(f"**Patient:** {patient_name}")
        st.markdown(
            f"""
            - **Age:** {age} &nbsp; | &nbsp; **BMI:** {bmi}
            - **AMH:** {amh} ng/mL &nbsp; | &nbsp; **FSH:** {fsh} IU/L
            - **LH:** {lh} IU/L &nbsp; | &nbsp; **Estradiol:** {estradiol} pg/mL
            """
        )
        if genes:
            st.markdown("**Genes Selected:** " + "".join([f"<span class='pill'>{g}</span>" for g in genes]), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with c4:
        # Quick risk band KPI
        band = "Low" if score < 35 else ("Moderate" if score < 55 else "High")
        st.markdown(f"""
        <div class="card">
        <div class="kpi">
            <div>📈 Risk Band</div>
            <div class="value">{band}</div>
        </div>
        <div style="height:.4rem;"></div>
        <div class="kpi">
            <div>🧬 Genes Selected</div>
            <div class="value">{len(genes)}</div>
        </div>
        <div style="height:.4rem;"></div>
        <div class="kpi">
            <div>📝 Flags Detected</div>
            <div class="value">{sum(1 for v in flags.values() if v)}</div>
        </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # --- Tabs ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Analytics", "🧬 Gene Insights", "🗓️ Timeline", "🧠 Notes & AI", "🧾 Plan & Download"
    ])

    # ========== TAB 1: Analytics ==========
    with tab1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Feature Visualizations")
        c11, c12 = st.columns(2)
        with c11:
            if genes:
                st.pyplot(gene_importance_chart(genes), use_container_width=True)
        with c12:
            st.pyplot(clinical_factors_chart({"Age": age, "BMI": bmi, "FSH": fsh, "AMH": amh, "LH": lh}), use_container_width=True)
        if len(genes) >= 3:
            radar = radar_chart(genes)
            if radar is not None:
                st.pyplot(radar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("3D Endometrium Visualization")
        st.pyplot(uterine_3d_plot(estradiol, fsh), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ========== TAB 2: Gene Insights ==========
    with tab2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Gene-Specific Insights")
        if not genes:
            st.info("Select genes in the sidebar to view insights.")
        else:
            for g in genes:
                st.markdown(f"**{g}** — {GENE_INFO.get(g, 'No curated insight yet.')}" )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Genetic Therapy Insights (Research – not medical advice)")
        found = False
        for g in genes:
            if g in THERAPY_INSIGHTS:
                found = True
                st.markdown(f"- **{g}** → {THERAPY_INSIGHTS[g]}")
        if not found:
            st.write("No targeted research notes for the selected genes.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ========== TAB 3: Timeline ==========
    with tab3:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Fertility Timeline Predictor")
        if last_menses_date:
            st.pyplot(fertile_window_heatmap(pd.to_datetime(last_menses_date), cycle_length), use_container_width=True)
            ovulation_est = pd.to_datetime(last_menses_date) + pd.Timedelta(days=int(cycle_length*0.5))
            fw_start = ovulation_est - pd.Timedelta(days=3)
            fw_end = ovulation_est + pd.Timedelta(days=1)
            st.success(f"Estimated fertile window: **{fw_start.date()} → {fw_end.date()}** (ovulation around **{ovulation_est.date()}**) —estimate")
        else:
            st.info("Provide LMP in sidebar to calculate timeline.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ========== TAB 4: Notes & AI ==========
    with tab4:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Clinical Notes Understanding")
        colA, colB = st.columns(2)
        with colA:
            st.write("**Detected from notes:**")
            any_detected = False
            for k, v in flags.items():
                if v:
                    any_detected = True
                    st.markdown(f"- ✅ {k.replace('_',' ').title()}")
            if not any_detected:
                st.markdown("- ✅ None detected")
        with colB:
            st.write("**Potential blindspots:**")
            for k, v in flags.items():
                if not v:
                    st.markdown(f"- ◻️ {k.replace('_',' ').title()}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Decision Support: Tests & Medicines (Expanded)")
        meds = suggest_medicines(features, genes, flags)
        tests = suggest_tests(features, genes, flags)
        c21, c22 = st.columns(2)
        with c21:
            st.markdown("**🧪 Suggested Tests**")
            if tests:
                for t in tests: st.markdown(f"- {t}")
            else:
                st.write("No immediate tests suggested based on current inputs.")
        with c22:
            st.markdown("**💊 Suggested Medications**")
            if meds:
                for m in meds: st.markdown(f"- {m}")
            else:
                st.write("No medication suggestions at this time.")
        st.caption("These are educational suggestions for discussion with a licensed clinician.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader(" Workflow to be followed :")
        steps = agentic_next_steps(score, flags, tests, meds)
        for i, stext in enumerate(steps, start=1):
            st.markdown(f"{i}. {stext}")
        st.markdown("</div>", unsafe_allow_html=True)

    # ========== TAB 5: Plan & Download ==========
    with tab5:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Personalized Plan Summary")

        # Build a simple text report
        lines = []
        lines.append("🧬Genovive\n")
        lines.append(f"Date: {datetime.now().date()}\n")
        if patient_name: lines.append(f"Patient: {patient_name}\n")
        lines.append("--- Inputs ---\n")
        lines.append(f"Age: {age}, BMI: {bmi}\n")
        lines.append(f"AMH: {amh} ng/mL, FSH: {fsh} IU/L, LH: {lh} IU/L, Estradiol: {estradiol} pg/mL\n")
        lines.append("Genes: " + (", ".join(genes) if genes else "None") + "\n")
        lines.append("Notes: " + (notes if notes else "None") + "\n")
        lines.append("\n--- Prediction ---\n")
        band = "Low" if score < 35 else ("Moderate" if score < 55 else "High")
        lines.append(f"Label: {label}, Confidence: {confidence:.2f}, Risk Index: {score:.0f}/100 ({band})\n")
        lines.append("\n--- Suggested Tests ---\n")
        for t in tests: lines.append(f"- {t}\n")
        lines.append("\n--- Suggested Medicines (for clinician discussion) ---\n")
        for m in meds: lines.append(f"- {m}\n")
        lines.append("\n--- Next Steps ---\n")
        for stext in steps: lines.append(f"- {stext}\n")
        lines.append("\nDisclaimer: This app is a demo decision-support tool and not a substitute for professional medical advice.\n")

        report_txt = "".join(lines)
        st.text_area("Preview Report", value=report_txt, height=280)

        # Tabular CSV exports (suggestions)
        df_tests = pd.DataFrame({"Suggested Tests": tests})
        df_meds  = pd.DataFrame({"Suggested Medicines": meds})
        df_steps = pd.DataFrame({"Next Steps": steps})

        cdl1, cdl2, cdl3, cdl4 = st.columns([1,1,1,1])
        with cdl1:
            st.download_button("⬇️ Download Plan (TXT)", data=report_txt, file_name="infertility_plan.txt")
        with cdl2:
            st.download_button("⬇️ Tests (CSV)", data=df_tests.to_csv(index=False), file_name="suggested_tests.csv")
        with cdl3:
            st.download_button("⬇️ Medicines (CSV)", data=df_meds.to_csv(index=False), file_name="suggested_medicines.csv")
        with cdl4:
            st.download_button("⬇️ Next Steps (CSV)", data=df_steps.to_csv(index=False), file_name="next_steps.csv")

        st.caption("This app is an educational prototype. Always consult a qualified clinician.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Subtle celebratory animation for UX delight
    st.balloons()

else:
    st.info("Use the sidebar to enter patient data, then click **Predict & Generate Plan**.")
    st.caption("Tip: Add a patient name, pick a notes template, choose genes, and set LMP to unlock all features.")

# ============================
# End of App
# ============================
