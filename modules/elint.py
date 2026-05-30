"""
Waveform ELINT Fingerprinting — emitter identification from signal parameters.

Given observed waveform measurements (frequency, PRF, pulse width, scan type,
platform), score against an open-source emitter library and return ranked
candidates with per-parameter match breakdown.
"""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

_L = dict(
    plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
    font=dict(color="#c9d1d9", family="Courier New"),
    legend=dict(bgcolor="#0d1117", bordercolor="#21262d"),
    margin=dict(l=60, r=20, t=60, b=50),
)

# Open-source emitter library.
# freq/prf/pw given as (low, high) ranges; scan and platform are categorical.
# Sources: Jane's All the World's Aircraft, IHS Jane's Radar, public OSINT.
_EMITTERS = [
    # --- SAM fire control ---
    {"name": "SA-15 GAUNTLET / 9S35M",    "role": "SAM FC",   "band": "H/I",
     "freq": (8.5, 10.0),  "prf": (1000, 6000), "pw": (0.5,  2.0), "scan": "sector",   "platform": "ground"},
    {"name": "SA-21 / 91N6E Big Bird",     "role": "SAM acq",  "band": "S",
     "freq": (2.7,  3.1),  "prf": (250,  500),  "pw": (10.0, 25.0),"scan": "circular", "platform": "ground"},
    {"name": "SA-10 / 30N6 Flap Lid",     "role": "SAM FC",   "band": "C/X",
     "freq": (5.4,  10.0), "prf": (300,  1200), "pw": (2.0,  8.0), "scan": "sector",   "platform": "ground"},
    {"name": "SA-11 / 9S35 Fire Dome",    "role": "SAM FC",   "band": "H",
     "freq": (8.0,  10.0), "prf": (1200, 4000), "pw": (0.8,  2.5), "scan": "sector",   "platform": "ground"},
    {"name": "SA-6 / 1S91 Straight Flush","role": "SAM FC",   "band": "G/H",
     "freq": (4.0,  8.0),  "prf": (2000, 5000), "pw": (0.4,  1.5), "scan": "sector",   "platform": "ground"},
    # --- Airborne intercept / fighter ---
    {"name": "Su-35 Irbis-E",             "role": "AI radar", "band": "X",
     "freq": (9.0,  10.0), "prf": (2000, 8000), "pw": (0.3,  1.5), "scan": "sector",   "platform": "airborne"},
    {"name": "MiG-29 N019 Slot Back",     "role": "AI radar", "band": "X",
     "freq": (9.5,  9.8),  "prf": (2000, 5000), "pw": (0.5,  2.0), "scan": "sector",   "platform": "airborne"},
    {"name": "Su-24 Orion-A",             "role": "Ground attack", "band": "X",
     "freq": (9.3,  9.6),  "prf": (1500, 4000), "pw": (0.5,  3.0), "scan": "fixed",    "platform": "airborne"},
    {"name": "F/A-18 APG-73",             "role": "AI radar", "band": "X",
     "freq": (8.0,  12.0), "prf": (2000, 10000),"pw": (0.2,  1.0), "scan": "sector",   "platform": "airborne"},
    # --- Maritime / ship ---
    {"name": "Kilo class MF-244 Snoop Tray","role":"Surface search","band":"I",
     "freq": (9.0,  10.0), "prf": (700,  1200), "pw": (0.1,  0.5), "scan": "circular", "platform": "naval"},
    {"name": "Udaloy Fregat-M Top Plate", "role": "Air search","band": "E/F",
     "freq": (2.9,  3.1),  "prf": (300,  600),  "pw": (4.0,  12.0),"scan": "circular", "platform": "naval"},
    {"name": "Slava Fregat-MA Top Pair",  "role": "3D search", "band": "E/F",
     "freq": (2.8,  3.0),  "prf": (250,  450),  "pw": (8.0,  18.0),"scan": "circular", "platform": "naval"},
    {"name": "Sovremenny MR-710 Fregat",  "role": "Air search","band": "E/F",
     "freq": (2.9,  3.2),  "prf": (290,  540),  "pw": (4.0,  12.0),"scan": "circular", "platform": "naval"},
    # --- AEW ---
    {"name": "A-50 Mainstay Shmel AEW",   "role": "AEW",      "band": "L",
     "freq": (1.2,  1.4),  "prf": (250,  500),  "pw": (40.0, 80.0),"scan": "circular", "platform": "airborne"},
    {"name": "IL-20 Coot ELINT",          "role": "ELINT/SIGINT","band": "multiple",
     "freq": (0.5,  18.0), "prf": (0,    0),    "pw": (0.0,  0.0), "scan": "fixed",    "platform": "airborne"},
    # --- EW / jammer ---
    {"name": "Su-24MP Fencer-F EW",       "role": "Escort jammer","band": "C–J",
     "freq": (4.0,  18.0), "prf": (0,    0),    "pw": (0.0,  0.0), "scan": "fixed",    "platform": "airborne"},
    {"name": "Il-22PP Porubshchik EW",    "role": "SEAD jammer","band": "multiple",
     "freq": (1.0,  18.0), "prf": (0,    0),    "pw": (0.0,  0.0), "scan": "fixed",    "platform": "airborne"},
    # --- Short-range AAA ---
    {"name": "ZSU-23-4 Shilka Gun Dish",  "role": "AAA FC",   "band": "J",
     "freq": (15.0, 17.0), "prf": (1600, 3000), "pw": (0.2,  0.8), "scan": "sector",   "platform": "ground"},
    {"name": "SA-13 Gopher / 9S16 Flat Face","role":"Short SAM","band":"H/I",
     "freq": (7.5,  9.5),  "prf": (700,  2500), "pw": (0.4,  1.8), "scan": "circular", "platform": "ground"},
    # --- Early warning ---
    {"name": "55Zh6M Nebo-M VHF EWR",    "role": "EW radar",  "band": "VHF/A",
     "freq": (0.15, 0.45), "prf": (100,  300),  "pw": (50.0,150.0),"scan": "circular", "platform": "ground"},
    {"name": "1L119 Nebo SVU meter EWR",  "role": "EW radar",  "band": "A/B",
     "freq": (0.1,  0.3),  "prf": (80,   250),  "pw": (40.0,120.0),"scan": "circular", "platform": "ground"},
]

_SCAN_TYPES = sorted({e["scan"] for e in _EMITTERS})
_PLATFORMS  = sorted({e["platform"] for e in _EMITTERS})

# Feature weights: how strongly each parameter narrows the match
_WEIGHTS = {
    "freq":  0.40,
    "prf":   0.25,
    "pw":    0.20,
    "scan":  0.10,
    "plat":  0.05,
}


def _score_emitter(em: dict, obs_freq: float, obs_prf: float, obs_pw: float,
                   obs_scan: str, obs_plat: str) -> dict:
    def range_match(val, lo, hi):
        if lo == hi == 0:
            return 0.5   # unknown (EW/ELINT aircraft — no discrete pulses)
        centre = (lo + hi) / 2
        half   = max((hi - lo) / 2, 0.01)
        if lo <= val <= hi:
            return 1.0
        dist = min(abs(val - lo), abs(val - hi))
        return float(np.exp(-0.5 * (dist / half) ** 2))

    s_freq = range_match(obs_freq,  *em["freq"])
    s_prf  = range_match(obs_prf,   *em["prf"])
    s_pw   = range_match(obs_pw,    *em["pw"])
    s_scan = 1.0 if obs_scan == em["scan"]     else 0.2
    s_plat = 1.0 if obs_plat == em["platform"] else 0.3

    total = (s_freq * _WEIGHTS["freq"] + s_prf  * _WEIGHTS["prf"] +
             s_pw   * _WEIGHTS["pw"]   + s_scan * _WEIGHTS["scan"] +
             s_plat * _WEIGHTS["plat"])

    return {
        "name":     em["name"],
        "role":     em["role"],
        "band":     em["band"],
        "platform": em["platform"],
        "score":    float(total),
        "breakdown": {
            "Frequency": s_freq,
            "PRF":       s_prf,
            "Pulse width": s_pw,
            "Scan type": s_scan,
            "Platform":  s_plat,
        },
        "freq_range": em["freq"],
        "prf_range":  em["prf"],
        "pw_range":   em["pw"],
    }


@st.cache_data
def fingerprint(
    obs_freq: float, obs_prf: float, obs_pw: float,
    obs_scan: str,   obs_plat: str,  top_n: int = 5,
) -> list:
    scores = [_score_emitter(e, obs_freq, obs_prf, obs_pw, obs_scan, obs_plat)
              for e in _EMITTERS]
    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[:top_n]


def render():
    st.header("ELINT Waveform Fingerprinting")
    st.caption(
        "Enter observed waveform parameters — frequency, PRF, pulse width, scan type, platform. "
        "Score is computed against a library of 20 emitters using weighted parameter matching. "
        "Returns ranked candidates with per-parameter match breakdown."
    )

    col_a, col_b = st.columns([1, 2])

    with col_a:
        st.markdown("**Observed waveform**")
        obs_freq = st.slider("Frequency (GHz)",       0.1, 18.0, 9.5, 0.1)
        obs_prf  = st.slider("PRF (Hz) — 0 if CW/ELINT", 0, 10000, 2500, 100)
        obs_pw   = st.slider("Pulse width (µs) — 0 if CW", 0.0, 200.0, 1.0, 0.1)
        obs_scan = st.selectbox("Scan type", _SCAN_TYPES)
        obs_plat = st.selectbox("Platform", _PLATFORMS)
        top_n    = st.slider("Candidates to show", 3, 8, 5, 1)
        st.divider()
        st.markdown("**Parameter weights**")
        for feat, w in _WEIGHTS.items():
            st.progress(w, text=f"{feat}: {w:.0%}")

    results = fingerprint(obs_freq, obs_prf, obs_pw, obs_scan, obs_plat, top_n)

    with col_b:
        # Confidence bar chart
        fig = go.Figure()
        names   = [r["name"].split("/")[0].strip()[:28] for r in results]
        scores  = [r["score"] * 100 for r in results]
        colors  = ["#39d353" if s >= 70 else "#e3b341" if s >= 40 else "#f85149"
                   for s in scores]
        fig.add_trace(go.Bar(
            x=scores, y=names, orientation="h",
            marker=dict(color=colors),
            text=[f"{s:.0f}%" for s in scores],
            textposition="outside",
            textfont=dict(family="Courier New", color="#c9d1d9", size=11),
        ))
        fig.update_layout(
            title=dict(text="ELINT Match Confidence",
                       font=dict(color="#c9d1d9", family="Courier New")),
            xaxis=dict(title="Match score (%)", range=[0, 120], gridcolor="#21262d"),
            yaxis=dict(autorange="reversed", tickfont=dict(family="Courier New", size=9)),
            height=300, **_L,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Top match detail
        top = results[0]
        st.subheader(f"Top match: {top['name']}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Role",     top["role"])
        c2.metric("Band",     top["band"])
        c3.metric("Platform", top["platform"])

        # Per-parameter radar chart
        cats = list(top["breakdown"].keys())
        vals = [top["breakdown"][c] * 100 for c in cats]
        vals_closed = vals + [vals[0]]
        cats_closed = cats + [cats[0]]
        fig_r = go.Figure(data=go.Scatterpolar(
            r=vals_closed, theta=cats_closed,
            fill="toself", fillcolor="rgba(57,211,83,0.15)",
            line=dict(color="#39d353", width=2),
            name=top["name"],
        ))
        fig_r.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100],
                                 tickfont=dict(family="Courier New", color="#c9d1d9", size=8),
                                 gridcolor="#21262d"),
                angularaxis=dict(tickfont=dict(family="Courier New", color="#c9d1d9", size=9),
                                  gridcolor="#21262d"),
                bgcolor="#0d1117",
            ),
            showlegend=False,
            paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            height=280,
            margin=dict(l=60, r=60, t=40, b=40),
        )
        st.plotly_chart(fig_r, use_container_width=True)

        # Candidates table
        with st.expander("All candidates — parameter ranges"):
            import pandas as pd
            rows = [{
                "Rank": i + 1,
                "Emitter": r["name"],
                "Role": r["role"],
                "Score": f"{r['score']*100:.0f}%",
                "Freq (GHz)": f"{r['freq_range'][0]}–{r['freq_range'][1]}",
                "PRF (Hz)":   f"{int(r['prf_range'][0])}–{int(r['prf_range'][1])}",
                "PW (µs)":    f"{r['pw_range'][0]}–{r['pw_range'][1]}",
            } for i, r in enumerate(results)]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Confidence tier interpretation
        top_score = results[0]["score"] * 100
        if top_score >= 80:
            st.success(f"High confidence ({top_score:.0f}%) — parameters strongly consistent with top match.")
        elif top_score >= 50:
            st.warning(f"Medium confidence ({top_score:.0f}%) — ambiguous between top candidates. "
                        "Collect additional parameters (scan rate, polarisation, PRI jitter).")
        else:
            st.error(f"Low confidence ({top_score:.0f}%) — no strong library match. "
                      "Possible novel emitter or parameters outside library range.")
