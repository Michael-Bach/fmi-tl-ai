"""
Cognitive / Frequency-Agile Radar simulation.

Models an AESA-style frequency-hopping radar and shows how different
jamming strategies perform as a function of hop rate and band coverage.

Strategies:
  Barrage:    cover the entire hop band → reduced J/S per Hz
  Spot:       guess the current hop frequency → 1/N hit probability
  Predictive: learn a deterministic hop sequence → 100% hit probability
  Reactive:   detect-and-retune → limited by reaction time vs hop rate
"""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

SPEED_OF_LIGHT = 3e8

_L = dict(
    plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
    font=dict(color="#c9d1d9", family="Courier New"),
    legend=dict(bgcolor="#0d1117", bordercolor="#21262d"),
    margin=dict(l=60, r=20, t=60, b=50),
)


@st.cache_data
def compute_strategies(
    jammer_erp_dbw: float,
    radar_erp_dbw: float,
    rcs_dbsm: float,
    base_freq_ghz: float,
    hop_band_ghz: float,
    n_hop_freqs: int,
    range_km: float,
    reaction_time_ms: float,
    hop_rate_hz_range: tuple,
    n_points: int = 80,
) -> dict:
    hop_rates = np.logspace(
        np.log10(hop_rate_hz_range[0]),
        np.log10(hop_rate_hz_range[1]),
        n_points,
    )

    pen_spot = 0.0      # spot jammer ERP penalty (dB) — no bandwidth spread
    pen_barrage_base = -10 * np.log10(n_hop_freqs)   # spread over N frequencies

    r_m = range_km * 1e3
    wl_base = SPEED_OF_LIGHT / (base_freq_ghz * 1e9)

    def js_spot(hit_prob):
        """Expected J/S given probability of being on the right hop frequency."""
        # When on freq: J/S = nominal spot J/S
        # When off freq: J/S ≪ 0 (assume −30 dB)
        js_on  = (jammer_erp_dbw + pen_spot - radar_erp_dbw
                  + 10 * np.log10(4 * np.pi) + 20 * np.log10(r_m) - rcs_dbsm)
        js_off = js_on - 30
        return hit_prob * js_on + (1 - hit_prob) * js_off

    # Barrage: constant — does not change with hop rate (already spread over band)
    js_barrage = np.full(n_points, jammer_erp_dbw + pen_barrage_base - radar_erp_dbw
                          + 10 * np.log10(4 * np.pi) + 20 * np.log10(r_m) - rcs_dbsm)

    # Spot (random guess): P(hit) = 1/N_freqs, independent of hop rate
    js_spot_random = np.full(n_points, js_spot(1.0 / n_hop_freqs))

    # Predictive (deterministic sequence): P(hit)=1 if hop period > reaction time
    hop_period_ms = 1000.0 / hop_rates                   # ms per hop
    react_ms = reaction_time_ms
    p_predict = np.where(hop_period_ms > react_ms, 1.0, hop_period_ms / react_ms)
    js_predictive = np.array([js_spot(p) for p in p_predict])

    # Reactive: sense current hop, retune, jam for remaining dwell
    dwell_efficiency = np.maximum(0, (hop_period_ms - react_ms) / hop_period_ms)
    js_reactive = np.array([js_spot(de) for de in dwell_efficiency])

    return {
        "hop_rates": hop_rates,
        "js_barrage":    js_barrage,
        "js_spot":       js_spot_random,
        "js_predictive": js_predictive,
        "js_reactive":   js_reactive,
        "hop_period_ms": hop_period_ms,
    }


@st.cache_data
def compute_hop_sequence(
    n_hops: int,
    n_freqs: int,
    base_ghz: float,
    band_ghz: float,
    deterministic: bool,
    seed: int,
) -> dict:
    freqs = np.linspace(base_ghz, base_ghz + band_ghz, n_freqs)
    rng = np.random.default_rng(seed)
    if deterministic:
        seq_idx = np.arange(n_hops) % n_freqs
    else:
        seq_idx = rng.integers(0, n_freqs, n_hops)
    hop_freqs = freqs[seq_idx]
    return {"freqs": freqs, "hop_freqs": hop_freqs, "seq_idx": seq_idx}


def _render_js_vs_hop():
    st.subheader("J/S vs Hop Rate — Strategy Comparison")
    st.caption(
        "Four jamming strategies against a frequency-hopping radar. "
        "Barrage degrades with more hop frequencies (power spread). "
        "Spot is poor unless the jammer can predict or react to the hop sequence."
    )
    col_a, col_b = st.columns([1, 2])
    with col_a:
        j_erp   = st.slider("Jammer ERP (dBW)", -10, 60, 20, 1, key="cog_j")
        r_erp   = st.slider("Radar ERP (dBW)",   20, 80, 50, 1, key="cog_r")
        rcs     = st.slider("Target RCS (dBsm)", -25, 20, -15, 1, key="cog_rcs")
        base_f  = st.slider("Radar base frequency (GHz)", 1, 18, 10, 1, key="cog_f")
        band    = st.slider("Hop band (GHz)", 0.1, 4.0, 1.0, 0.1, key="cog_band")
        n_freqs = st.slider("Number of hop frequencies", 2, 64, 8, 2, key="cog_nf")
        range_km = st.slider("Range (km)", 10, 300, 80, 10, key="cog_range")
        react_ms = st.slider("Jammer reaction time (ms)", 0.5, 20.0, 2.0, 0.5,
                              help="Time to detect hop and retune the spot jammer.")
        st.caption(
            f"Barrage penalty: −{10 * np.log10(n_freqs):.1f} dB "
            f"for covering {n_freqs} frequencies."
        )

    res = compute_strategies(j_erp, r_erp, rcs, base_f, band, n_freqs, range_km,
                              react_ms, (1, 10000))

    with col_b:
        fig = go.Figure()
        pairs = [
            ("js_barrage",    "Barrage",           "#e3b341"),
            ("js_spot",       "Spot (random guess)", "#f85149"),
            ("js_reactive",   "Reactive (sense+retune)", "#58a6ff"),
            ("js_predictive", "Predictive (learned sequence)", "#39d353"),
        ]
        for key, name, color in pairs:
            fig.add_trace(go.Scatter(
                x=res["hop_rates"], y=res[key],
                mode="lines", name=name,
                line=dict(color=color, width=2),
            ))
        fig.add_hline(y=0, line=dict(color="#8b949e", dash="dot", width=1))
        fig.update_layout(
            title=dict(text="Effective J/S vs Hop Rate",
                       font=dict(color="#c9d1d9", family="Courier New")),
            xaxis=dict(title="Hop rate (Hz)", type="log", gridcolor="#21262d"),
            yaxis=dict(title="Effective J/S (dB)", gridcolor="#21262d"),
            height=380, **_L,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Crossover: hop rate where predictive beats barrage
        js_b = res["js_barrage"][0]
        crossover = None
        for i, (hr, jp) in enumerate(zip(res["hop_rates"], res["js_predictive"])):
            if jp < js_b and crossover is None:
                crossover = hr
                break

        m1, m2, m3 = st.columns(3)
        m1.metric("Barrage J/S", f"{res['js_barrage'][0]:.1f} dB")
        m2.metric("Spot J/S (random)", f"{res['js_spot'][0]:.1f} dB")
        m3.metric("Predictive J/S (low hop rate)", f"{res['js_predictive'][0]:.1f} dB")

        st.info(
            f"Against a {n_freqs}-frequency hopper, barrage suffers "
            f"−{10 * np.log10(n_freqs):.1f} dB spread loss. "
            f"Predictive jamming beats barrage below ~{react_ms:.0f} ms hop period "
            f"({1000/react_ms:.0f} Hz). Above that, the jammer cannot retune fast enough. "
            "Modern AESA radars exceed 10 kHz hop rates — barrage becomes the only viable strategy."
        )


def _render_hop_sequence():
    st.subheader("Hop Sequence Visualisation")
    st.caption(
        "Deterministic hopping (cyclic) can be predicted once the jammer learns the sequence. "
        "Pseudo-random hopping with a cryptographic key cannot. "
        "This determines whether predictive jamming is feasible."
    )
    col_a, col_b = st.columns([1, 2])
    with col_a:
        n_hops  = st.slider("Pulses to display", 10, 80, 40, 5)
        n_freqs2 = st.slider("Hop frequencies",  2, 32, 8, 2, key="hs_nf")
        base2   = st.slider("Base freq (GHz)",   2, 16, 9, 1, key="hs_base")
        band2   = st.slider("Hop band (GHz)",    0.2, 3.0, 1.0, 0.2, key="hs_band")
        det     = st.checkbox("Deterministic (cyclic) sequence", value=True)
        seed    = int(st.number_input("Seed", value=7, step=1, key="hs_seed"))

    hs = compute_hop_sequence(n_hops, n_freqs2, base2, band2, det, seed)

    with col_b:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(n_hops)), y=hs["hop_freqs"],
            mode="lines+markers",
            line=dict(color="#39d353", width=1.5),
            marker=dict(color="#39d353", size=6),
            name="Radar hop sequence",
        ))
        if det:
            # Show predicted next hop (offset by 1 — known if deterministic)
            pred_freqs = hs["freqs"][hs["seq_idx"]]
            fig.add_trace(go.Scatter(
                x=list(range(n_hops)), y=pred_freqs,
                mode="markers", name="Jammer prediction (correct)",
                marker=dict(color="#58a6ff", size=8, symbol="x",
                             line=dict(color="#58a6ff", width=1)),
            ))
        fig.update_layout(
            title=dict(text=f"{'Deterministic' if det else 'Random'} Hop Sequence",
                       font=dict(color="#c9d1d9", family="Courier New")),
            xaxis=dict(title="Pulse number", gridcolor="#21262d"),
            yaxis=dict(title="Frequency (GHz)", gridcolor="#21262d"),
            height=320, **_L,
        )
        st.plotly_chart(fig, use_container_width=True)

        if det:
            st.success(
                "Deterministic (cyclic) sequence: after one full cycle the jammer knows "
                "the next frequency with certainty. "
                "Predictive jamming achieves full spot J/S regardless of hop rate."
            )
        else:
            st.warning(
                "Pseudo-random sequence: jammer cannot predict the next hop. "
                "Spot jamming achieves at most 1/N hit probability. "
                "At N=8, expected J/S advantage over barrage requires P(hit) > N × ERP_barrage_fraction."
            )


def render():
    c1, c2 = st.tabs(["📊 J/S vs Hop Rate", "〰 Hop Sequence"])
    with c1: _render_js_vs_hop()
    with c2: _render_hop_sequence()
