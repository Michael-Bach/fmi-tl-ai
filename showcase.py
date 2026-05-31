"""
showcase.py — Repository showcase for fmi-tl-ai

A guided tour of the repo for a hiring panel or technical reviewer.
Run with:   streamlit run showcase.py

Self-contained: the physics demos are implemented inline so this file
can be read and run independently of the full application.
"""
from dotenv import load_dotenv
load_dotenv()

import math
import os
import streamlit as _st_secrets

# Bridge Streamlit Cloud secrets → os.environ
try:
    for _k, _v in _st_secrets.secrets.items():
        os.environ.setdefault(_k, str(_v))
except Exception:
    pass

import numpy as np
import plotly.graph_objects as go
import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="fmi-tl-ai — Showcase",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
html, body, [class*="css"] { background-color: #0d1117; color: #c9d1d9; }
.stApp { background-color: #0d1117; }
h1, h2, h3 { font-family: 'Courier New', monospace !important; }
.stMetric label { font-family: 'Courier New', monospace !important; font-size: 12px !important; }
.stMetric div[data-testid="stMetricValue"] {
    font-family: 'Courier New', monospace !important;
    font-size: 28px !important;
    color: #39d353 !important;
}
code { font-size: 12px !important; }
.section-divider {
    border: none; border-top: 1px solid #21262d; margin: 32px 0;
}
.badge {
    display: inline-block; padding: 3px 10px; border-radius: 12px;
    font-size: 11px; font-family: 'Courier New', monospace;
    margin-right: 6px; margin-bottom: 4px;
}
</style>
""", unsafe_allow_html=True)

_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
_has_api = bool(_api_key)

# ──────────────────────────────────────────────────────────────────────────────
# Hero
# ──────────────────────────────────────────────────────────────────────────────

col_title, col_status = st.columns([5, 1])
with col_title:
    st.markdown("""
<h1 style='font-size:28px; margin-bottom:4px;'>
EW M&amp;S Foundation — FMI TEW
</h1>
<p style='color:#8b949e; font-family:Courier New; font-size:13px; margin-top:0;'>
Team Lead, AI Modellering og Simulering &nbsp;·&nbsp;
Forsvarsministeriets Materiel- og Indkøbsstyrelse
</p>
""", unsafe_allow_html=True)

with col_status:
    if _has_api:
        st.markdown(
            "<div style='background:#0f2a1a; border:1px solid #39d353; border-radius:4px; "
            "padding:8px; text-align:center; font-family:Courier New; font-size:11px; "
            "margin-top:12px;'>API KEY<br><span style='color:#39d353;'>✓ LOADED</span></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div style='background:#2a1a0d; border:1px solid #e3b341; border-radius:4px; "
            "padding:8px; text-align:center; font-family:Courier New; font-size:11px; "
            "margin-top:12px;'>API KEY<br><span style='color:#e3b341;'>⚠ NOT SET</span></div>",
            unsafe_allow_html=True,
        )

# Badge row
st.markdown("""
<div style='margin:12px 0 8px;'>
<span class='badge' style='background:#1a3a5c; color:#58a6ff;'>Python 3.11+</span>
<span class='badge' style='background:#3a1a1a; color:#f85149;'>Streamlit</span>
<span class='badge' style='background:#2a1e0d; color:#e3b341;'>Claude Opus 4.8</span>
<span class='badge' style='background:#0f2a1a; color:#39d353;'>Claude Sonnet 4.6</span>
<span class='badge' style='background:#1a1a3a; color:#a5a0f7;'>NumPy · SciPy</span>
<span class='badge' style='background:#1a2a2a; color:#56d364;'>Plotly</span>
<span class='badge' style='background:#21262d; color:#8b949e;'>LangChain</span>
<span class='badge' style='background:#21262d; color:#8b949e;'>Pydantic v2</span>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<p style='font-size:15px; max-width:860px; line-height:1.7; color:#c9d1d9;'>
A working demonstration for the FMI TEW Team Lead role: signal-level physics simulation,
AI/ML capability benchmarking, and LLM-powered acquisition advisory — in one application.
Built to show what this function would actually produce, not describe it.
</p>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# By the numbers
# ──────────────────────────────────────────────────────────────────────────────

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Simulation modules", "31")
m2.metric("Lines of Python", "~9 000")
m3.metric("LLM patterns", "4")
m4.metric("Physics engines", "8")
m5.metric("Tabs / sub-tabs", "11 / 40+")

# ──────────────────────────────────────────────────────────────────────────────
# Navigation
# ──────────────────────────────────────────────────────────────────────────────

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

nav = st.radio(
    "Jump to section",
    ["📡 Physics demo", "🤖 LLM integrations", "🗂️ Module directory",
     "🏗️ Architecture", "📋 Role context"],
    horizontal=True,
    label_visibility="collapsed",
)

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION: Physics demo
# ══════════════════════════════════════════════════════════════════════════════

if nav == "📡 Physics demo":
    st.header("Signal-level physics — live demonstration")
    st.caption(
        "The same equations used in the full application, running here. "
        "Adjust parameters to stress-test a vendor claim or model a scenario."
    )

    # ── J/S simulator ──────────────────────────────────────────────────────
    st.subheader("Jammer-to-Signal (J/S) ratio — Nathanson/Barton equation")

    with st.expander("What this shows", expanded=False):
        st.markdown("""
**The core EW physics problem:** at what range does a jammer provide effective
protection, and when does the threat radar break through?

The **self-screening J/S equation** (Nathanson/Barton):

```
J/S (dB) = ERP_J − ERP_R + 10·log₁₀(4π) + 20·log₁₀(R) − RCS + mode_penalty
```

- Grows with range because radar return falls as **R⁴** while jammer signal falls as **R²**
- **Burn-through range** = the crossover point where J/S = 0 dB
- **Acquisition use:** back-calculate implied threat ERP from a vendor's claimed J/S at range
""")

    col_a, col_b = st.columns([2, 3])

    with col_a:
        st.markdown("**Jammer platform**")
        j_erp = st.slider("Jammer ERP (dBW)", 20, 55, 35,
                          help="Effective Radiated Power of the self-protection jammer")
        rcs = st.slider("Platform RCS (dBsm)", -25, 15, -15,
                        help="Radar Cross Section of the jammed platform (F-35A ≈ −15 dBsm)")
        mode = st.selectbox("Jamming mode", ["Spot", "Sweep", "Barrage"],
                            help="Mode penalty: Spot 0 dB, Sweep −5 dB, Barrage −10 dB")
        st.markdown("**Threat radar**")

        threat = st.selectbox("Threat preset", [
            "SA-10/S-300 (55 dBW, 3 GHz)",
            "SA-15/Tor (48 dBW, 8.5 GHz)",
            "Custom",
        ])
        presets = {
            "SA-10/S-300 (55 dBW, 3 GHz)": (55, 3.0),
            "SA-15/Tor (48 dBW, 8.5 GHz)": (48, 8.5),
        }
        if threat == "Custom":
            r_erp = st.slider("Threat ERP (dBW)", 30, 65, 50)
        else:
            r_erp, _ = presets[threat]
            st.metric("Threat ERP", f"{r_erp} dBW")

        max_range = st.slider("Plot range (km)", 20, 200, 100)

    with col_b:
        mode_penalties = {"Spot": 0, "Sweep": -5, "Barrage": -10}
        penalty = mode_penalties[mode]
        ranges_km = np.linspace(0.5, max_range, 500)
        ranges_m  = ranges_km * 1e3
        js = (j_erp + penalty - r_erp
              + 10 * np.log10(4 * np.pi)
              + 20 * np.log10(ranges_m)
              - rcs)

        # Burn-through
        r_bt = 10 ** ((r_erp - j_erp - penalty + rcs - 10 * np.log10(4 * np.pi)) / 20) / 1e3

        fig = go.Figure()
        fig.add_hline(y=0, line=dict(color="#e3b341", width=1, dash="dash"))
        fig.add_trace(go.Scatter(
            x=ranges_km, y=js,
            mode="lines", name="J/S",
            line=dict(color="#58a6ff", width=2),
            fill="tozeroy",
            fillcolor="rgba(88,166,255,0.08)",
        ))
        if 0 < r_bt < max_range:
            fig.add_vline(x=r_bt, line=dict(color="#f85149", width=1.5, dash="dot"))
            fig.add_annotation(
                x=r_bt, y=max(js) * 0.7,
                text=f"Burn-through<br>{r_bt:.1f} km",
                font=dict(color="#f85149", family="Courier New", size=11),
                showarrow=False,
            )

        fig.update_layout(
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(title="Range (km)", gridcolor="#21262d"),
            yaxis=dict(title="J/S (dB)", gridcolor="#21262d",
                       zeroline=False),
            margin=dict(l=50, r=20, t=30, b=50),
            height=380,
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Key numbers
        k1, k2, k3 = st.columns(3)
        js_at_50  = float(np.interp(50, ranges_km, js))
        js_at_100 = float(np.interp(min(100, max_range), ranges_km, js))
        k1.metric("J/S at 50 km", f"{js_at_50:+.1f} dB",
                  delta="effective" if js_at_50 > 0 else "radar breaks through",
                  delta_color="normal" if js_at_50 > 0 else "inverse")
        k2.metric("Burn-through range", f"{r_bt:.1f} km")
        k3.metric("Mode penalty", f"{penalty:+d} dB")

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # ── Bayesian ERP estimator ──────────────────────────────────────────────
    st.subheader("Bayesian ERP estimation from ESM intercepts")
    st.caption(
        "Each ESM power measurement gives a noisy estimate of the threat radar ERP. "
        "Conjugate Gaussian-Gaussian update narrows the posterior with each observation."
    )

    col_c, col_d = st.columns([2, 3])
    with col_c:
        prior_mean = st.slider("Prior mean ERP (dBW)", 20, 60, 35)
        prior_std  = st.slider("Prior σ (dB)", 3, 20, 15)
        n_obs      = st.slider("Number of ESM observations", 1, 30, 8)
        true_erp   = st.slider("True threat ERP — simulation ground truth (dBW)", 30, 65, 50)
        noise_db   = st.slider("ESM measurement noise σ (dB)", 1, 10, 3)

    with col_d:
        rng = np.random.default_rng(42)
        obs = true_erp + rng.normal(0, noise_db, n_obs)

        # Sequential update
        mu, sigma = float(prior_mean), float(prior_std)
        mus, sigmas = [mu], [sigma]
        for o in obs:
            prec  = 1/sigma**2 + 1/noise_db**2
            mu    = (mu/sigma**2 + o/noise_db**2) / prec
            sigma = math.sqrt(1/prec)
            mus.append(mu); sigmas.append(sigma)

        erp_axis = np.linspace(prior_mean - 3*prior_std, true_erp + 3*prior_std, 400)

        def gauss(x, m, s):
            return np.exp(-0.5*((x-m)/s)**2) / (s * math.sqrt(2*math.pi))

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=erp_axis, y=gauss(erp_axis, prior_mean, prior_std),
            name="Prior", line=dict(color="#8b949e", dash="dash", width=1.5),
        ))
        fig2.add_trace(go.Scatter(
            x=erp_axis, y=gauss(erp_axis, mus[-1], sigmas[-1]),
            name=f"Posterior (n={n_obs})",
            line=dict(color="#58a6ff", width=2),
            fill="tozeroy", fillcolor="rgba(88,166,255,0.08)",
        ))
        fig2.add_vline(x=true_erp, line=dict(color="#39d353", dash="dot", width=1.5))
        fig2.add_annotation(
            x=true_erp, y=gauss(erp_axis, mus[-1], sigmas[-1]).max() * 0.5,
            text="True ERP", font=dict(color="#39d353", family="Courier New", size=11),
            showarrow=False,
        )
        fig2.update_layout(
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(title="ERP estimate (dBW)", gridcolor="#21262d"),
            yaxis=dict(title="Probability density", gridcolor="#21262d"),
            margin=dict(l=50, r=20, t=30, b=50), height=300,
            legend=dict(bgcolor="#0d1117"),
        )
        st.plotly_chart(fig2, use_container_width=True)

        b1, b2, b3 = st.columns(3)
        b1.metric("Posterior mean", f"{mus[-1]:.1f} dBW")
        b2.metric("Posterior σ", f"{sigmas[-1]:.1f} dB")
        b3.metric("95% CI", f"[{mus[-1]-2*sigmas[-1]:.0f}, {mus[-1]+2*sigmas[-1]:.0f}] dBW")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION: LLM integrations
# ══════════════════════════════════════════════════════════════════════════════

elif nav == "🤖 LLM integrations":
    st.header("LLM integration patterns")
    st.caption(
        "Four distinct Anthropic SDK patterns, each chosen for the task it serves. "
        "Click a pattern to see the implementation and rationale."
    )

    # ── Pattern 1: Extended Thinking ───────────────────────────────────────
    with st.expander("1 · Extended thinking — Teknisk Notat Generator", expanded=True):
        col_l, col_r = st.columns([1, 1])
        with col_l:
            st.markdown("""
**What:** `claude-opus-4-8` with `thinking={"type":"enabled","budget_tokens":8000}`
generates full-length structured technical notes in the format FMI decision-makers use.

**Why extended thinking here:**
The model needs to reason through technical parameters, cross-reference Allied capability,
flag ITAR/dual-use concerns, and calibrate confidence — before producing a document
that will inform a procurement decision. Extended thinking gives it the depth to do that
without hallucinating specifics.

**What's shown in the UI:**
The thinking blocks are rendered in a collapsible expander alongside the finished document,
so a technically fluent reviewer can audit the reasoning chain.
""")
        with col_r:
            st.code("""
from workflow.llm import get_native_client, THINKING_MODEL
from workflow.context import get_cached_system_blocks

client = get_native_client()

response = client.messages.create(
    model=THINKING_MODEL,          # claude-opus-4-8
    max_tokens=16_000,
    thinking={
        "type": "enabled",
        "budget_tokens": 8_000,    # 8k reasoning budget
    },
    system=get_cached_system_blocks(),  # cached context
    messages=[{"role": "user", "content": prompt}],
)

# Separate thinking blocks from text output
thinking = [b for b in response.content if b.type == "thinking"]
text      = [b for b in response.content if b.type == "text"]

# Show reasoning in UI
with st.expander(f"Reasoning ({sum(len(b.thinking) for b in thinking):,} chars)"):
    for tb in thinking:
        st.code(tb.thinking, language="text")
""", language="python")

        if _has_api:
            if st.button("Open Teknisk Notat tab in full app →",
                         key="open_notat"):
                st.info("Run `streamlit run app.py` and navigate to the 📄 Teknisk Notat tab.")
        else:
            st.caption("⚠ Set ANTHROPIC_API_KEY in .env to run live. "
                       "Physics and visualisation tabs work without a key.")

    # ── Pattern 2: Tool Use Agent ───────────────────────────────────────────
    with st.expander("2 · Tool use — EW Advisory Agent"):
        col_l, col_r = st.columns([1, 1])
        with col_l:
            st.markdown("""
**What:** A multi-turn conversational agent backed by `claude-sonnet-4-6`.
Five tools expose the physics simulation layer:

| Tool | Physics |
|------|---------|
| `compute_js_ratio` | Nathanson/Barton J/S equation |
| `estimate_radar_erp` | Conjugate Gaussian-Gaussian Bayesian update |
| `lookup_threat_profile` | Open-source ERP/frequency database |
| `assess_technology_trl` | TRL register with acquisition implications |
| `query_capability_gaps` | FMI-TEW gap register |

**Why tool use here:** Advisory questions like *"What J/S does a 30 dBW
jammer achieve against an SA-10 at 40 km?"* require computation, not recall.
Tool use forces the model to produce verifiable numbers from physics,
not plausible-sounding estimates.

**Agentic loop:** the model calls tools, sees results, reasons, then decides
whether to call more tools or produce a final answer. Tool calls and results
are surfaced in the UI.
""")
        with col_r:
            st.code("""
# Agentic tool-call loop
messages = history + [{"role": "user", "content": user_input}]

while True:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4_096,
        tools=TOOLS,                        # 5 physics tools
        system=get_cached_system_blocks(),  # prompt caching
        messages=messages,
    )

    # Serialise content blocks for session state
    content_dicts = _content_to_dicts(response.content)
    messages.append({"role": "assistant", "content": content_dicts})

    if response.stop_reason == "end_turn":
        return extract_text(content_dicts), messages

    if response.stop_reason == "tool_use":
        results = []
        for block in content_dicts:
            if block["type"] == "tool_use":
                result = execute_tool(block["name"], block["input"])
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block["id"],
                    "content": json.dumps(result),
                })
        messages.append({"role": "user", "content": results})
""", language="python")

    # ── Pattern 3: Prompt Caching ───────────────────────────────────────────
    with st.expander("3 · Prompt caching — Allied Contribution Synthesis"):
        col_l, col_r = st.columns([1, 1])
        with col_l:
            st.markdown("""
**What:** The 750-token `DANISH_DEFENCE_CONTEXT` — FMI structure, acquisition
process, EW priorities, NATO relationships — is marked with
`cache_control: {"type": "ephemeral"}`.

**Why caching here:**
- Context is identical across every LLM call in the application
- Without caching: 750 tokens re-tokenised on every call
- With caching: served from cache for 5 minutes, ~4× faster for repeat calls
  and no input-token cost on cache hits

**In the UI:** the `Cache read` metric is displayed alongside `Input tokens`
on every LLM-powered tab, so the cache behaviour is observable.

**Where it's applied:**
- EW Advisory Agent (every turn in a multi-turn conversation)
- Teknisk Notat Generator
- Allied Contribution Synthesis
- Vendor Kravspec pipeline
""")
        with col_r:
            st.code("""
# workflow/context.py

def get_cached_system_blocks() -> list[dict]:
    \"\"\"System message with cache_control.
    Context is re-used across all LLM calls —
    caching cuts latency and input-token cost.
    \"\"\"
    return [
        {
            "type": "text",
            "text": DANISH_DEFENCE_CONTEXT,   # 750 tokens
            "cache_control": {"type": "ephemeral"},
        }
    ]


# Usage in any module:
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=2_048,
    system=get_cached_system_blocks(),   # ← cached
    messages=[...],
)

# Inspect cache hit in response
cache_read    = response.usage.cache_read_input_tokens
cache_created = response.usage.cache_creation_input_tokens
""", language="python")

    # ── Pattern 4: Structured Output ───────────────────────────────────────
    with st.expander("4 · Structured output — Vendor Acquisition Pipeline"):
        col_l, col_r = st.columns([1, 1])
        with col_l:
            st.markdown("""
**What:** A 3-step agentic pipeline using LangChain + `with_structured_output()`.
Pydantic schemas enforce the output contract at each step.

**Pipeline steps:**
1. **Extract** → `ProductAnalysis` (product name, specs, use cases, flagged claims)
2. **Verify** → for each flagged/unsubstantiated claim, generate a targeted
   verification question
3. **Assess** → `DanishAssessment` (relevance, ITAR flag, recommendation:
   `evaluate | monitor | reject`, named next step)

**Why structured output here:**
The downstream consumer is a programme manager who needs machine-readable
fields (ITAR flag, recommendation) for database entry and dashboard display —
not free-text prose.

**Pydantic enforces:**
- `recommendation` is one of `["evaluate", "monitor", "reject"]`
- `itar_flag` and `dual_use_flag` are `bool` (not "yes/no" strings)
- `next_step` names a responsible party (prompt constraint + schema)
""")
        with col_r:
            st.code("""
# workflow/structured.py

class DanishAssessment(BaseModel):
    relevance:             str
    fit:                   str
    acquisition_pathway:   str
    itar_flag:             bool
    dual_use_flag:         bool
    classification_concern: bool
    recommendation: Literal["evaluate", "monitor", "reject"]
    next_step:             str   # must name responsible party
    risk_summary:          str


# workflow/pipeline.py — step 1

analysis_llm = llm.with_structured_output(ProductAnalysis)
analysis: ProductAnalysis = analysis_llm.invoke(
    ANALYZE_PROMPT.format_messages(
        content=content,
        source_type=source_type,
    )
)

# step 2 — agentic: verify each flagged claim
for claim_check in analysis.flagged_claims:
    if claim_check.credibility in ("unsubstantiated", "marketing"):
        question = (VERIFY_PROMPT | llm | StrOutputParser()).invoke(
            {"claim": claim_check.claim}
        )
        verification_steps.append((claim_check.claim, question))

# step 3 — structured assessment
assessment_llm = llm.with_structured_output(DanishAssessment)
assessment: DanishAssessment = assessment_llm.invoke(...)
""", language="python")

    # Summary comparison
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown("#### Pattern selection rationale")
    st.markdown("""
| Task | Pattern | Why |
|------|---------|-----|
| Technical note drafting | Extended thinking | Complex multi-step reasoning; output audited by technical staff |
| Interactive advisory Q&A | Tool use | Forces physics-grounded answers; not recall-based |
| Repeated context across all calls | Prompt caching | Cost and latency reduction for a fixed knowledge block |
| Procurement pipeline output | Structured output | Machine-readable fields consumed by dashboards and PM workflow |
""")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION: Module directory
# ══════════════════════════════════════════════════════════════════════════════

elif nav == "🗂️ Module directory":
    st.header("Module directory")
    st.caption("30+ modules across signal physics, AI/ML, acquisition advisory, LLM, and strategic planning.")

    categories = {
        "Signal physics & simulation": [
            ("simulation.py", "J/S ratio (Nathanson/Barton), burn-through range, ESM detection, Monte Carlo"),
            ("sead.py",       "SEAD geometry — stand-off EA vs defence, jammer placement"),
            ("bayesian.py",   "Bayesian ERP estimation from ESM intercepts (conjugate Gaussian)"),
            ("fusion.py",     "Multi-sensor Kalman filter: radar + ESM + IFF track fusion"),
            ("drfm.py",       "DRFM deception — range gate and velocity gate pull-off models"),
            ("network_ew.py", "Distributed multi-platform EW coordination; signal geometry"),
            ("cognitive_radar.py", "Adaptive radar response: waveform agility, PRF variation under jamming"),
            ("sensor_perf.py", "ERP sweep curves; detection range vs manufacturer spec"),
        ],
        "AI & machine learning": [
            ("rl_jammer.py",  "Q-learning adaptive jammer — mode selection against dynamic threat"),
            ("deep_rl.py",    "Deep Q-network (DQN) jammer — multi-layer neural network policy"),
            ("arms_race.py",  "Multi-jammer coordination + attacker/defender co-evolution"),
            ("anomaly.py",    "Mahalanobis anomaly detection + ML vs threshold benchmark"),
            ("trl.py",        "Technology Readiness Level framework for AI/EW technologies"),
        ],
        "Acquisition advisory": [
            ("vendor.py",           "Vendor stress-tester (back-calc ERP) + kravspec section generator"),
            ("teknisk_vurdering.py", "Technical evaluation rubric with weighted scoring"),
            ("risk.py",             "Procurement risk — cost-of-inaction calculator"),
            ("elint.py",            "ELINT emitter fingerprinting and characterisation database"),
            ("eob.py",              "Electronic Order of Battle — friendly and threat emitter mapping"),
            ("emcon.py",            "EMCON compliance planner — detectability under emission states"),
        ],
        "LLM integrations": [
            ("teknisk_notat.py", "Extended thinking — structured technical note generation (Opus 4.8)"),
            ("ew_agent.py",      "Tool-use agent — multi-turn EW advisory with 5 physics tools"),
            ("gap_map.py",       "Prompt caching — allied contribution synthesis from capability matrix"),
            ("vendor.py",        "Structured output — 3-step Pydantic-enforced acquisition pipeline"),
        ],
        "Scenarios & operational planning": [
            ("killchain.py",        "EW kill chain — detect / identify / locate / engage sequence"),
            ("threat_evolution.py", "Multi-year threat parameter forecast with uncertainty"),
            ("scenarios.py",        "Scenario library — Baltic maritime, SEAD, IADS suppression"),
        ],
        "Strategic & landscape": [
            ("landscape.py",   "Nordic/NATO capability heatmap — 8 organisations × 6 areas"),
            ("gap_map.py",     "Allied EW M&S maturity matrix (15 areas × 6 orgs) + LLM synthesis"),
            ("intelligence.py","Threat analysis — LangChain scrape → analyse → compare pipeline"),
            ("intel_kb.py",    "Threat parameter knowledge base"),
            ("function.py",    "Intake workflow, capacity model, bilateral tracker, 3-year roadmap"),
            ("strategy.py",    "NATO fora contributions, team composition, cost-of-inaction"),
        ],
    }

    for cat, modules in categories.items():
        with st.expander(cat, expanded=True):
            import pandas as pd
            df = pd.DataFrame(modules, columns=["Module", "What it does"])
            st.dataframe(df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION: Architecture
# ══════════════════════════════════════════════════════════════════════════════

elif nav == "🏗️ Architecture":
    st.header("Architecture")

    st.markdown("""
```
┌─────────────────────────────────────────────────────────────────────────────┐
│         Streamlit UI — app.py   ·   11 tabs  ·  40+ sub-tabs               │
└──────────────────┬──────────────────────────────┬──────────────────────────┘
                   │                              │
       ┌───────────▼──────────┐      ┌────────────▼───────────────┐
       │   Physics engine      │      │   LLM workflow layer        │
       │                       │      │                             │
       │  NumPy · SciPy        │      │  workflow/llm.py            │
       │  Plotly               │      │    get_llm()          ←─ LangChain
       │                       │      │    get_native_client() ←─ Anthropic SDK
       │  Nathanson/Barton J/S │      │    THINKING_MODEL      ← claude-opus-4-8
       │  Kalman filter        │      │    CACHING_MODEL       ← claude-sonnet-4-6
       │  Bayesian inference   │      │                             │
       │  Q-learning (tabular) │      │  workflow/context.py        │
       │  DQN (neural net)     │      │    DANISH_DEFENCE_CONTEXT   │
       │  Monte Carlo          │      │    get_cached_system_blocks()│
       └───────────────────────┘      │                             │
                                      │  workflow/pipeline.py       │
       ┌───────────────────────┐      │    run()              ←─ LangChain chain
       │   Static data layer    │      │    run_structured()   ←─ Pydantic output
       │                       │      │    generate_adversarial_qa()│
       │  data/landscape_data  │      │                             │
       │  data/function_data   │      │  workflow/structured.py     │
       │  data/strategy_data   │      │    ProductAnalysis          │
       │  data/roadmap         │      │    DanishAssessment         │
       └───────────────────────┘      │    ClaimCheck               │
                                      └─────────────────────────────┘
                                                    │
                                      ┌─────────────▼──────────────┐
                                      │   Anthropic API             │
                                      │                             │
                                      │  claude-opus-4-8            │
                                      │    thinking (extended)      │
                                      │    max_tokens 16k           │
                                      │    budget_tokens 8k         │
                                      │                             │
                                      │  claude-sonnet-4-6          │
                                      │    tool_use (agent)         │
                                      │    structured_output        │
                                      │    cache_control ephemeral  │
                                      └─────────────────────────────┘
```
""")

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    st.markdown("#### Data flow — acquisition advisory pipeline")
    st.markdown("""
```
Vendor datasheet / procurement question
            │
            ▼
  [LLM Step 1]  ProductAnalysis (structured)
  · product_name, core_capability, key_specs
  · flagged_claims → credibility: unsubstantiated | marketing | plausible
            │
            ▼
  [Agentic loop]  For each flagged claim:
  · generate targeted verification question
  · "What test evidence would substantiate this J/S claim at stated range?"
            │
            ▼
  [Physics check]  Back-calculate implied radar ERP from vendor's claimed J/S
  · If implied ERP > 60 dBW: flag as implausible (no known radar at that level)
            │
            ▼
  [LLM Step 3]  DanishAssessment (structured)
  · itar_flag: bool
  · recommendation: evaluate | monitor | reject
  · next_step: "FMI air office to request independent test protocol from vendor"
            │
            ▼
  Decision-ready output for programme manager
```
""")

    st.markdown("#### File tree")
    st.code("""
fmi-tl-ai/
├── app.py                   Main Streamlit entry point (11 tabs)
├── showcase.py              This file — guided repo tour
├── requirements.txt
│
├── data/
│   ├── landscape_data.py    Nordic/NATO capability matrix
│   ├── function_data.py     Gaps, bilaterals, intake workflow, roadmap
│   ├── strategy_data.py     TRL criteria, NATO fora, team composition
│   └── roadmap.py           Year 1 quarterly deliverables
│
├── workflow/
│   ├── llm.py               get_llm() + get_native_client() + model constants
│   ├── context.py           DANISH_DEFENCE_CONTEXT + get_cached_system_blocks()
│   ├── pipeline.py          3-step agentic vendor analysis pipeline
│   ├── structured.py        Pydantic schemas: ProductAnalysis, DanishAssessment
│   └── loaders.py           Data loaders
│
└── modules/                 31 Streamlit tab modules
    ├── simulation.py        J/S Nathanson/Barton engine
    ├── ew_agent.py          Tool-use advisory agent  ← NEW
    ├── teknisk_notat.py     Extended thinking notat generator  ← NEW
    ├── [28 more modules]
    └── ...
""", language="text")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION: Role context
# ══════════════════════════════════════════════════════════════════════════════

elif nav == "📋 Role context":
    st.header("Role context")

    col_p, col_q = st.columns(2)

    with col_p:
        st.subheader("The problem this function solves")
        st.markdown("""
Danish EW acquisition currently happens without signal-level analytical grounding.
Vendor J/S claims are written into kravspecifikationer without independent
burn-through range verification. Allied partners — FFI, FOI, DSTL — have been
building signal-level M&S capacity for five years. Denmark has not.

This function does three things:

**1. Stress-test vendor claims** before a kravspec is signed.
Back-calculate what a claimed J/S figure implies about the threat radar ERP.
Flag figures that require a radar ERP higher than any known system.

**2. Model threat evolution** so procurement decisions remain valid
at fielding date, not just at point of signature.

**3. Position Denmark as a contributing NMSG node** — shaping Allied
M&S standards rather than adopting what Norway and Sweden built
for their acquisition priorities.
""")

        st.subheader("Scope boundaries")
        st.markdown("""
**Not DDRE:** DDRE operates at campaign level. This function works at
signal level — jammer vs radar vs ESM receiver physics in specific
acquisition contexts. Complementary abstraction layers, not competitors.

**Not AI for AI's sake:** The simulation comes first. AI enters in Q3,
after a credible physics baseline exists to benchmark against.
A model without a physics baseline is an opinion, not an analysis.
""")

    with col_q:
        st.subheader("Year 1 plan")
        import pandas as pd
        df = pd.DataFrame([
            {"Q": "Q1", "Period": "Aug–Oct", "Deliverable": "Landscape report — who has what, where TEW adds unique value"},
            {"Q": "Q2", "Period": "Nov–Jan", "Deliverable": "Signal-environment prototype + decision brief (this app, Q2 state)"},
            {"Q": "Q3", "Period": "Feb–Apr", "Deliverable": "AI prototype benchmarked vs classical baseline + NMSG draft contribution"},
            {"Q": "Q4", "Period": "May–Jul", "Deliverable": "3-year capability roadmap + signed MOU (FFI or TERMA)"},
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader("What I bring")
        st.markdown("""
**Domain fluency.**
Eight years Royal Danish Navy, Lieutenant Commander.
I know how EW procurement decisions are made operationally and where
the gap between a vendor datasheet and a real threat environment is.

**Technical depth.**
MSc Computational Physics. Thesis: multi-agent RL for naval tactical
decision-making with synthetic simulation data. I know where AI genuinely
beats classical methods and where it introduces risk without benefit.

**Translation.**
This app produces numbers. The value is translating those numbers into
acquisition language. Technical credibility with leadership accessibility
is the combination this role requires.
""")

        st.subheader("Stakeholder map")
        df2 = pd.DataFrame([
            {"Stakeholder": "DDRE",            "Relationship": "Coordinate — campaign level, not signal physics"},
            {"Stakeholder": "FFI (Norway)",     "Relationship": "Primary bilateral — ALERT suite; avoid duplication"},
            {"Stakeholder": "FOI (Sweden)",     "Relationship": "Nordic partner — radar signatures, EA modelling"},
            {"Stakeholder": "TERMA/Systematic", "Relationship": "Industry — HW-in-the-loop, SW environments"},
            {"Stakeholder": "DTU/KU",           "Relationship": "Academic pipeline — unclassified layer only"},
            {"Stakeholder": "NMSG",             "Relationship": "Standards — contribute, do not just adopt"},
        ])
        st.dataframe(df2, use_container_width=True, hide_index=True)

# ──────────────────────────────────────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────────────────────────────────────

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    st.markdown(
        "<span style='font-family:Courier New; font-size:12px; color:#8b949e;'>"
        "github.com/Michael-Bach/fmi-tl-ai</span>",
        unsafe_allow_html=True,
    )
with col_f2:
    st.markdown(
        "<span style='font-family:Courier New; font-size:12px; color:#8b949e; "
        "text-align:center; display:block;'>"
        "streamlit run app.py &nbsp;·&nbsp; full application</span>",
        unsafe_allow_html=True,
    )
with col_f3:
    status = "API ready" if _has_api else "Set ANTHROPIC_API_KEY for LLM tabs"
    st.markdown(
        f"<span style='font-family:Courier New; font-size:12px; color:#8b949e; "
        f"float:right;'>{status}</span>",
        unsafe_allow_html=True,
    )
