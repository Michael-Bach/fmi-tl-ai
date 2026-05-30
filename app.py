from dotenv import load_dotenv
load_dotenv()

import streamlit as st

st.set_page_config(
    page_title="EW M&S Foundation",
    layout="wide",
    page_icon="🛡️",
)

st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    .stApp { background-color: #0d1117; }
    .stMetric label, .stMetric div[data-testid="stMetricValue"] {
        font-family: 'Courier New', monospace !important;
    }
    .stDataFrame, .stDataFrame td, .stDataFrame th {
        font-family: 'Courier New', monospace !important;
    }
    .stSelectbox label, .stSlider label, .stExpander summary p {
        font-family: 'Courier New', monospace !important;
    }
    [data-testid="metric-container"] {
        font-family: 'Courier New', monospace !important;
    }
    .stSidebar [data-testid="stMarkdownContainer"] p {
        font-family: 'Courier New', monospace !important;
        color: #c9d1d9;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        """
        ```
        Role:         Team Lead, AI Modellering
                      og Simulering
        Organisation: FMI — TEW
        ```
        """
    )
    st.divider()
    briefing_mode = st.toggle(
        "Briefing mode",
        value=st.session_state.get("briefing_mode", False),
        help="Hide technical controls. Show operational conclusions only.",
    )
    st.session_state["briefing_mode"] = briefing_mode
    if briefing_mode:
        st.markdown(
            "<small style='color:#e3b341'>⬛ Briefing mode active</small>",
            unsafe_allow_html=True,
        )

st.title("EW M&S Foundation — FMI TEW")

from modules import (
    vision, simulation, landscape, intelligence, function, strategy,
    sead, bayesian, rl_jammer,
    killchain, threat_evolution, eob,
    vendor, anomaly, arms_race,
    fusion, sensor_perf, trl, teknisk_vurdering,
    # New modules
    drfm, deep_rl, network_ew, cognitive_radar,
    risk, intel_kb, gap_map, scenarios, elint, emcon,
)

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "🗺️ Vision",
    "📡 Simulation",
    "⚔️ Scenarios",
    "📋 Acquisition",
    "🌐 Landscape",
    "🔍 Intelligence",
    "🏛️ Function",
    "🎯 Strategy",
    "📂 Library",
])

with tab1:
    vision.render()

with tab2:
    st1, st2, st3, st4, st5, st6, st7, st8, st9, st10, st11, st12 = st.tabs([
        "J/S Simulator",
        "SEAD Scenario",
        "Bayesian Estimator",
        "RL Adaptive Jammer",
        "Deep RL Jammer",
        "Multi-Jammer",
        "Arms Race",
        "Sensor Fusion",
        "Sensor Performance",
        "DRFM Deception",
        "Networked EW",
        "Cognitive Radar",
    ])
    with st1:  simulation.render()
    with st2:  sead.render()
    with st3:  bayesian.render()
    with st4:  rl_jammer.render()
    with st5:  deep_rl.render()
    with st6:  arms_race._render_multijammer()
    with st7:  arms_race._render_arms_race()
    with st8:  fusion.render()
    with st9:  sensor_perf.render()
    with st10: drfm.render()
    with st11: network_ew.render()
    with st12: cognitive_radar.render()

with tab3:
    sc1, sc2, sc3, sc4 = st.tabs([
        "🎯 Kill Chain",
        "📈 Threat Evolution",
        "🗺️ EOB / EMCON",
        "📡 EMCON Planner",
    ])
    with sc1: killchain.render()
    with sc2: threat_evolution.render()
    with sc3: eob.render()
    with sc4: emcon.render()

with tab4:
    ac1, ac2, ac3, ac4, ac5, ac6, ac7, ac8 = st.tabs([
        "🔬 Vendor Stress-Test",
        "📄 Kravspec",
        "📝 Teknisk Vurdering",
        "🎓 TRL Assessment",
        "🚨 Anomaly Detection",
        "📻 Waveform Classifier",
        "⚠️ Procurement Risk",
        "🔎 ELINT Fingerprint",
    ])
    with ac1: vendor._render_stress_tester()
    with ac2: vendor._render_kravspec_generator()
    with ac3: teknisk_vurdering.render()
    with ac4: trl.render()
    with ac5: anomaly._render_anomaly_detection()
    with ac6: anomaly._render_waveform_classifier()
    with ac7: risk.render()
    with ac8: elint.render()

with tab5:
    lc1, lc2 = st.tabs(["🌐 Nordic/NATO Landscape", "🗺️ Allied Gap Map"])
    with lc1: landscape.render()
    with lc2: gap_map.render()

with tab6:
    it1, it2 = st.tabs(["🔍 Intelligence Analysis", "🗃️ Knowledge Base"])
    with it1: intelligence.render()
    with it2: intel_kb.render()

with tab7:
    function.render()

with tab8:
    strategy.render()

with tab9:
    scenarios.render()
