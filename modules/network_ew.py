"""
Networked EW — collaborative TDOA/AOA geolocation.

Multiple platforms share ESM data to geolocate an emitter.
Shows how platform separation, geometry, and count affect CEP.
TDOA: time-difference-of-arrival (hyperbolic LoP).
AOA:  angle-of-arrival (bearing cross-fix).
CEP computed empirically via Monte Carlo.
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

SPEED_OF_LIGHT = 3e8
_COLORS = ["#58a6ff", "#e3b341", "#d2a8ff", "#f85149", "#39d353"]

_DEFAULT_PLATFORMS = [
    (0.0,   0.0),
    (120.0, 0.0),
    (60.0,  100.0),
    (0.0,   180.0),
]
_DEFAULT_EMITTER = (70.0, 60.0)


@st.cache_data
def compute_geolocation(
    platforms: tuple,        # ((x0,y0), (x1,y1), ...)
    emitter: tuple,          # (xe, ye)
    tdoa_sigma_us: float,    # timing uncertainty µs
    aoa_sigma_deg: float,    # bearing uncertainty degrees
    n_mc: int = 1000,
    seed: int = 42,
    _top_level: bool = True,  # False in recursive CEP-vs-N sub-calls
) -> dict:
    rng = np.random.default_rng(seed)
    plat = np.array(platforms)
    em   = np.array(emitter)
    N    = len(plat)

    # True distances and ToAs
    dists = np.linalg.norm(plat - em, axis=1) * 1e3   # km → m
    toa   = dists / SPEED_OF_LIGHT                      # s

    tdoa_sigma_s = tdoa_sigma_us * 1e-6

    # TDOA LS geolocation via Monte Carlo
    tdoa_positions = []
    for _ in range(n_mc):
        noise_t = rng.normal(0, tdoa_sigma_s, N)
        toa_meas = toa + noise_t
        # Use reference = platform 0; TDOA = toa_i - toa_0
        if N >= 2:
            # Linearised LS: iterate from true position
            pos = em.copy() + rng.normal(0, 5, 2)   # start near truth
            for _ in range(10):
                dists_est = np.linalg.norm(plat - pos, axis=1) * 1e3
                toa_est   = dists_est / SPEED_OF_LIGHT
                tdoa_meas = toa_meas[1:] - toa_meas[0]
                tdoa_est  = toa_est[1:]  - toa_est[0]
                J = np.zeros((N - 1, 2))
                for i in range(1, N):
                    r0 = max(np.linalg.norm(pos - plat[0]) * 1e3, 1)
                    ri = max(np.linalg.norm(pos - plat[i]) * 1e3, 1)
                    J[i - 1, 0] = ((pos[0] - plat[i, 0]) * 1e3 / ri -
                                    (pos[0] - plat[0, 0]) * 1e3 / r0) / SPEED_OF_LIGHT
                    J[i - 1, 1] = ((pos[1] - plat[i, 1]) * 1e3 / ri -
                                    (pos[1] - plat[0, 1]) * 1e3 / r0) / SPEED_OF_LIGHT
                resid = tdoa_meas - tdoa_est
                try:
                    delta = np.linalg.lstsq(J, resid, rcond=None)[0]
                except Exception:
                    break
                pos = pos + delta / 1e3   # Jacobian gives metres; pos is in km
                if np.linalg.norm(delta) / 1e3 < 0.01:
                    break
            tdoa_positions.append(pos.copy())

    # AOA LS geolocation via Monte Carlo
    aoa_positions = []
    aoa_sigma_rad = np.radians(aoa_sigma_deg)
    for _ in range(n_mc):
        bearings = np.arctan2(em[1] - plat[:, 1], em[0] - plat[:, 0])
        b_meas   = bearings + rng.normal(0, aoa_sigma_rad, N)
        # Cross-bearing least squares
        A = np.zeros((N, 2))
        b = np.zeros(N)
        for i in range(N):
            cos_b = np.cos(b_meas[i])
            sin_b = np.sin(b_meas[i])
            A[i] = [-sin_b, cos_b]
            b[i] = -sin_b * plat[i, 0] + cos_b * plat[i, 1]
        try:
            pos_aoa = np.linalg.lstsq(A, b, rcond=None)[0]
        except Exception:
            pos_aoa = em.copy()
        aoa_positions.append(pos_aoa)

    tdoa_arr = np.array(tdoa_positions)
    aoa_arr  = np.array(aoa_positions)

    def cep(pts):
        errs = np.linalg.norm(pts - em, axis=1)
        return float(np.percentile(errs, 50))

    def rmse(pts):
        return float(np.sqrt(np.mean(np.sum((pts - em) ** 2, axis=1))))

    # CEP vs N platforms (subsets) — only computed at top level to avoid recursion
    tdoa_cep_vs_n, aoa_cep_vs_n = [], []
    if _top_level:
        for n in range(2, N + 1):
            sub = tuple(map(tuple, plat[:n]))
            sub_res = compute_geolocation(sub, tuple(emitter), tdoa_sigma_us, aoa_sigma_deg,
                                           n_mc=300, seed=seed, _top_level=False)
            tdoa_cep_vs_n.append(sub_res["tdoa_cep"])
            aoa_cep_vs_n.append(sub_res["aoa_cep"])

    # TDOA hyperbolas for display (pairs with reference platform 0)
    hyperbolas = []
    for i in range(1, N):
        dt_true = (dists[i] - dists[0]) / SPEED_OF_LIGHT
        # Parametric: points where |d_i - d_0| = c * dt_true
        x_scan = np.linspace(-50, 250, 400)
        y_scan = np.linspace(-80, 280, 400)
        XX, YY = np.meshgrid(x_scan, y_scan)
        d0 = np.sqrt((XX - plat[0, 0]) ** 2 + (YY - plat[0, 1]) ** 2) * 1e3
        di = np.sqrt((XX - plat[i, 0]) ** 2 + (YY - plat[i, 1]) ** 2) * 1e3
        Z  = (di - d0) / SPEED_OF_LIGHT - dt_true
        hyperbolas.append((XX, YY, Z, _COLORS[i % len(_COLORS)]))

    return {
        "tdoa_positions": tdoa_arr,
        "aoa_positions":  aoa_arr,
        "tdoa_cep":   cep(tdoa_arr),
        "aoa_cep":    cep(aoa_arr),
        "tdoa_rmse":  rmse(tdoa_arr),
        "aoa_rmse":   rmse(aoa_arr),
        "tdoa_cep_vs_n": tdoa_cep_vs_n,
        "aoa_cep_vs_n":  aoa_cep_vs_n,
        "hyperbolas": hyperbolas,
        "plat": plat,
        "em":   em,
    }


def render():
    st.header("Networked EW — Collaborative TDOA / AOA Geolocation")
    st.caption(
        "Distributed ESM receivers share timing and bearing data to geolocate an emitter. "
        "TDOA (time-difference-of-arrival) gives hyperbolic lines of position; "
        "AOA (angle-of-arrival) gives bearing cross-fixes. "
        "Both improve with platform count and favourable geometry."
    )

    col_a, col_b = st.columns([1, 2])

    with col_a:
        n_plat = st.slider("Number of platforms", 2, 4, 3, 1)
        st.markdown("**Platform positions (km East / North)**")
        plat_raw = list(_DEFAULT_PLATFORMS[:n_plat])
        plat_edit = []
        for i in range(n_plat):
            cx, cy = st.columns(2)
            px = cx.number_input(f"P{i+1} East", value=float(plat_raw[i][0]), step=10.0, key=f"px{i}")
            py = cy.number_input(f"P{i+1} North", value=float(plat_raw[i][1]), step=10.0, key=f"py{i}")
            plat_edit.append((px, py))
        st.markdown("**Emitter position (km)**")
        cc, cd = st.columns(2)
        ex = cc.number_input("East",  value=_DEFAULT_EMITTER[0], step=5.0, key="em_e")
        ey = cd.number_input("North", value=_DEFAULT_EMITTER[1], step=5.0, key="em_n")
        st.divider()
        tdoa_sigma = st.slider("TDOA timing uncertainty (µs)", 0.01, 5.0, 0.1, 0.01,
                                format="%.2f")
        aoa_sigma  = st.slider("AOA bearing uncertainty (deg)", 0.1, 10.0, 1.0, 0.1)
        n_mc = st.select_slider("MC samples", options=[200, 500, 1000], value=500)

    plat_tuple = tuple(map(tuple, plat_edit))
    em_tuple   = (float(ex), float(ey))

    with st.spinner("Computing…"):
        res = compute_geolocation(plat_tuple, em_tuple, tdoa_sigma, aoa_sigma, n_mc)

    with col_b:
        fig = go.Figure()

        # TDOA scatter
        tp = res["tdoa_positions"]
        fig.add_trace(go.Scatter(x=tp[:, 0], y=tp[:, 1], mode="markers",
                                  name=f"TDOA fixes (CEP {res['tdoa_cep']:.1f} km)",
                                  marker=dict(color="#58a6ff", size=3, opacity=0.4)))
        # AOA scatter
        ap = res["aoa_positions"]
        fig.add_trace(go.Scatter(x=ap[:, 0], y=ap[:, 1], mode="markers",
                                  name=f"AOA fixes (CEP {res['aoa_cep']:.1f} km)",
                                  marker=dict(color="#d2a8ff", size=3, opacity=0.4)))

        # Platforms
        plat_arr = res["plat"]
        fig.add_trace(go.Scatter(
            x=plat_arr[:, 0], y=plat_arr[:, 1],
            mode="markers+text",
            marker=dict(color="#e3b341", size=14, symbol="triangle-up"),
            text=[f"P{i+1}" for i in range(n_plat)],
            textposition="top center",
            textfont=dict(family="Courier New", color="#e3b341", size=10),
            name="Platforms",
        ))

        # True emitter
        fig.add_trace(go.Scatter(
            x=[res["em"][0]], y=[res["em"][1]], mode="markers", name="True emitter",
            marker=dict(color="#f85149", size=16, symbol="star",
                         line=dict(color="#fff", width=1)),
        ))

        fig.update_layout(
            title=dict(text="Geolocation Scatter — TDOA vs AOA",
                       font=dict(color="#c9d1d9", family="Courier New")),
            xaxis=dict(title="East (km)", gridcolor="#21262d", scaleanchor="y"),
            yaxis=dict(title="North (km)", gridcolor="#21262d"),
            height=420, **_L,
        )
        st.plotly_chart(fig, use_container_width=True)

        # CEP vs N platforms
        n_vals = list(range(2, len(plat_tuple) + 1))
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=n_vals, y=res["tdoa_cep_vs_n"], mode="lines+markers",
                                   name="TDOA CEP", line=dict(color="#58a6ff", width=2),
                                   marker=dict(size=8)))
        fig2.add_trace(go.Scatter(x=n_vals, y=res["aoa_cep_vs_n"], mode="lines+markers",
                                   name="AOA CEP", line=dict(color="#d2a8ff", width=2),
                                   marker=dict(size=8)))
        fig2.update_layout(
            title=dict(text="CEP (km) vs Number of Platforms",
                       font=dict(color="#c9d1d9", family="Courier New")),
            xaxis=dict(title="Platforms", gridcolor="#21262d", dtick=1),
            yaxis=dict(title="CEP (km)", gridcolor="#21262d"),
            height=220, **_L,
        )
        st.plotly_chart(fig2, use_container_width=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("TDOA CEP (km)", f"{res['tdoa_cep']:.2f}")
        m2.metric("TDOA RMSE (km)", f"{res['tdoa_rmse']:.2f}")
        m3.metric("AOA CEP (km)", f"{res['aoa_cep']:.2f}")
        m4.metric("AOA RMSE (km)", f"{res['aoa_rmse']:.2f}")

        with st.expander("Acquisition relevance"):
            st.markdown(
                "Networked EW is the acquisition argument for datalinks between distributed "
                "sensor platforms. A single ESM receiver gets a bearing line (AOA). "
                "Two gives a cross-bearing fix. Three or more TDOA gives a hyperbolic fix "
                "with CEP that drops non-linearly with platform count and geometry. "
                "The cost model: each additional platform reduces CEP, improving weapons targeting "
                "and force protection. This simulation supports the case for NetEW investment "
                "and informs kravspecifikation requirements on ESM timing accuracy."
            )
