"""
EW Advisory Agent

A multi-turn conversational agent that answers complex EW/sensor/acquisition
questions by calling physics simulation tools and synthesising the results
into plain-language advisory briefs.

Architecture:
- Native Anthropic SDK with tool_use (not LangChain)
- Prompt caching on DANISH_DEFENCE_CONTEXT system block
- Five tools: J/S simulation, Bayesian ERP estimation, threat profile lookup,
  TRL assessment, capability gap query
- Conversation history persisted in st.session_state across turns
- Tool calls and results surfaced in the UI as collapsible detail cards
"""
import json
import math

import streamlit as st

# ---------------------------------------------------------------------------
# Pure-Python physics / knowledge tools (no Streamlit dependencies)
# ---------------------------------------------------------------------------

def _tool_compute_js_ratio(
    jammer_erp_dbw: float,
    radar_erp_dbw: float,
    rcs_dbsm: float,
    range_km: float,
    jamming_mode: str = "Spot",
) -> dict:
    """J/S ratio (dB) at given range via Nathanson/Barton self-screening equation.

    Also returns burn-through range and whether jamming is effective (J/S > 0).
    """
    penalties = {"Barrage": -10, "Spot": 0, "Sweep": -5}
    penalty   = penalties.get(jamming_mode, 0)
    r_m       = range_km * 1e3
    js        = (
        jammer_erp_dbw + penalty
        - radar_erp_dbw
        + 10 * math.log10(4 * math.pi)
        + 20 * math.log10(r_m)
        - rcs_dbsm
    )
    # Burn-through: J/S = 0 → solve for R
    r_bt_m = 10 ** (
        (radar_erp_dbw - jammer_erp_dbw - penalty + rcs_dbsm
         - 10 * math.log10(4 * math.pi)) / 20
    )
    return {
        "js_db":             round(js, 1),
        "burnthrough_km":    round(r_bt_m / 1e3, 1),
        "jamming_effective": js > 0,
        "mode":              jamming_mode,
        "note": (
            "J/S > 0 dB means jammer output exceeds radar return — effective jamming. "
            "Burn-through is the range at which radar breaks through the jamming."
        ),
    }


def _tool_estimate_radar_erp(
    measurements_dbm: list,
    prior_mean_dbw: float = 40.0,
    prior_std_db: float   = 15.0,
    measurement_noise_db: float = 3.0,
) -> dict:
    """Bayesian posterior estimate of threat radar ERP from noisy ESM observations.

    Uses conjugate Gaussian-Gaussian update. Each element of measurements_dbm
    is a received-power reading in dBm from an ESM sensor.
    """
    n = len(measurements_dbm)
    if n == 0:
        return {"error": "Provide at least one ESM measurement in measurements_dbm."}
    mean_meas    = sum(measurements_dbm) / n
    sig_prior2   = prior_std_db ** 2
    sig_obs2     = measurement_noise_db ** 2
    post_prec    = 1 / sig_prior2 + n / sig_obs2
    post_mean    = (prior_mean_dbw / sig_prior2 + mean_meas * n / sig_obs2) / post_prec
    post_std     = math.sqrt(1 / post_prec)
    return {
        "posterior_mean_dbw": round(post_mean, 1),
        "posterior_std_db":   round(post_std, 1),
        "95pct_interval_dbw": [
            round(post_mean - 2 * post_std, 1),
            round(post_mean + 2 * post_std, 1),
        ],
        "n_measurements": n,
        "prior_mean_dbw": prior_mean_dbw,
        "note": (
            "Posterior narrows with more measurements. "
            "95% interval = mean ± 2σ under Gaussian assumption."
        ),
    }


_THREAT_DB: dict[str, dict] = {
    "SA-10/S-300 (Fire Control)": {
        "erp_dbw": 55, "freq_ghz": 3.0,
        "type": "SAM engagement radar (30N6E2 'Tomb Stone')",
        "itar_concern": False,
        "source_note": "Open-source OSINT estimates. Actual value classified.",
    },
    "SA-15/Tor-M2 (Engagement)": {
        "erp_dbw": 48, "freq_ghz": 8.5,
        "type": "SHORAD engagement radar",
        "itar_concern": False,
        "source_note": "Published specifications. Operational variant may differ.",
    },
    "Nebo-M (VHF Search)": {
        "erp_dbw": 52, "freq_ghz": 0.15,
        "type": "Long-range VHF early-warning search radar",
        "itar_concern": False,
        "source_note": "Russian open technical press.",
    },
    "Sun Visor (Naval FC)": {
        "erp_dbw": 45, "freq_ghz": 9.0,
        "type": "Naval fire-control radar",
        "itar_concern": False,
        "source_note": "Jane's Electronic Systems.",
    },
    "Irbis-E / Su-35 (AI Radar)": {
        "erp_dbw": 47, "freq_ghz": 10.0,
        "type": "Airborne intercept pulse-Doppler",
        "itar_concern": False,
        "source_note": "Manufacturer data sheet (Tikhomirov NIIP).",
    },
    "AESA generic (threat estimate)": {
        "erp_dbw": 50, "freq_ghz": 10.0,
        "type": "Generic AESA engagement radar — planning estimate",
        "itar_concern": False,
        "source_note": "Generic planning figure — not specific to any system.",
    },
}


def _tool_lookup_threat_profile(threat_name: str) -> dict:
    """Return open-source ERP and frequency parameters for a known threat radar.

    Call with threat_name = 'list' to get all available names.
    """
    if threat_name.lower() in ("list", "all", "?"):
        return {"available_threats": list(_THREAT_DB.keys())}
    if threat_name in _THREAT_DB:
        return _THREAT_DB[threat_name]
    # Fuzzy match on substring
    matches = [k for k in _THREAT_DB if threat_name.lower() in k.lower()]
    if matches:
        return {
            "closest_match": matches[0],
            "data": _THREAT_DB[matches[0]],
            "other_matches": matches[1:],
        }
    return {
        "error": f"No record for '{threat_name}'.",
        "available_threats": list(_THREAT_DB.keys()),
    }


_TRL_DB: dict[str, dict] = {
    "RL adaptive jamming": {
        "trl": 3,
        "label": "Proof-of-concept",
        "description": (
            "Demonstrated in lab environments (DSTL, FOI research programmes). "
            "Convergence in non-stationary RF environments remains an open problem. "
            "Not deployed in any known operational system (open source)."
        ),
        "allied_work": "DSTL TRL 3–4; FOI early research; US DARPA BLADE programme (classified).",
        "acquisition_implication": (
            "Do not accept TRL 7+ vendor claims without independent test evidence. "
            "Suitable for technology demonstration contracts, not operational procurement."
        ),
    },
    "AI signal classification": {
        "trl": 5,
        "label": "Validated in relevant environment",
        "description": (
            "Validated against curated signal libraries in controlled RF environments. "
            "Commercial SIGINT integrations beginning. "
            "Accuracy against novel/unknown waveforms remains <70% in published benchmarks."
        ),
        "allied_work": "FFI active programme. FOI NORDEFCO channel. UK DSTL SIGINT trial.",
        "acquisition_implication": (
            "Emerging capability. Specify independent test dataset in kravspec — "
            "do not accept vendor test results against vendor-curated library only."
        ),
    },
    "Kalman/IMM sensor fusion": {
        "trl": 8,
        "label": "Complete and qualified",
        "description": (
            "Mature operational technology deployed across NATO IADS, "
            "ship combat management systems, and airborne ISR platforms."
        ),
        "allied_work": "Widely deployed. TERMA, Systematic, Thales, Raytheon all offer qualified solutions.",
        "acquisition_implication": (
            "Mature COTS/MOTS options available. Focus procurement on integration, "
            "not development. Specify STANAG 4586 / ASTERIX compliance."
        ),
    },
    "Cognitive radar": {
        "trl": 4,
        "label": "Technology demonstrated",
        "description": (
            "Demonstrated in controlled environments. DARPA ACT programme, "
            "some EU Horizon work. No confirmed operational deployment (open source). "
            "Regulatory spectrum management issues unresolved for adaptive waveforms."
        ),
        "allied_work": "DSTL, TNO. US DARPA ACT (classified). NATO SET-302 STO panel.",
        "acquisition_implication": (
            "Monitor only. Not suitable for near-term procurement. "
            "Useful for NMSG MSG contribution and technology watch briefings."
        ),
    },
    "DRFM deception jamming": {
        "trl": 9,
        "label": "Operational deployment proven",
        "description": (
            "Mature technology deployed in ALQ-99, ASPIS, ALQ-218, TERMA ALQ-213, "
            "and others. Range gate pull-off and velocity gate pull-off are "
            "well-understood. Counter-DRFM techniques being fielded by adversaries."
        ),
        "allied_work": "Widely deployed. TERMA ALQ-213 directly relevant to Danish programmes.",
        "acquisition_implication": (
            "Procurement-ready COTS solutions exist. "
            "Focus on adversary counter-DRFM resilience in kravspec. "
            "ITAR applies to US-origin DRFM components."
        ),
    },
    "Networked EW (collaborative)": {
        "trl": 5,
        "label": "Validated in relevant environment",
        "description": (
            "MALD-J and some classified US cooperative EW programmes. "
            "EU: research stage only. Datalink latency and spectrum deconfliction "
            "remain open technical challenges."
        ),
        "allied_work": "US: classified. EU/NATO: research (NMSG MSG-173, STO SET-panel).",
        "acquisition_implication": (
            "Flag ITAR risk on any US-origin cooperative EW system. "
            "Specify datalink latency ≤ 50 ms and JEMSO compliance in kravspec."
        ),
    },
    "AI threat prediction": {
        "trl": 3,
        "label": "Proof-of-concept",
        "description": (
            "Multiple academic papers. No confirmed operational system. "
            "Data requirements (labelled threat tracks at scale) are the primary barrier."
        ),
        "allied_work": "Academic / research only. No NATO programme of record identified.",
        "acquisition_implication": (
            "Reject vendor claims of TRL ≥ 6 without independent validation. "
            "Suitable for exploratory R&D contracts only."
        ),
    },
}


def _tool_assess_technology_trl(technology: str) -> dict:
    """Return TRL assessment and acquisition implications for an EW/AI technology.

    Call with technology = 'list' to see available entries.
    """
    if technology.lower() in ("list", "all", "?"):
        return {"available_technologies": list(_TRL_DB.keys())}
    if technology in _TRL_DB:
        return _TRL_DB[technology]
    matches = [k for k in _TRL_DB if technology.lower() in k.lower()]
    if matches:
        return {
            "closest_match": matches[0],
            "data": _TRL_DB[matches[0]],
            "other_matches": matches[1:],
        }
    return {
        "error": f"No TRL record for '{technology}'.",
        "available_technologies": list(_TRL_DB.keys()),
    }


def _tool_query_capability_gaps(area: str = "all") -> dict:
    """Return FMI-TEW capability gap register entries.

    Pass area='all' (default) for the full register, or a keyword
    (e.g. 'SHORAD', 'maritime', 'EMCON') to filter by capability area.
    """
    try:
        from data.function_data import CAPABILITY_GAPS
        if area.lower() == "all":
            return {"gaps": CAPABILITY_GAPS, "count": len(CAPABILITY_GAPS)}
        matches = [
            g for g in CAPABILITY_GAPS
            if area.lower() in g.get("capability_area", "").lower()
            or area.lower() in g.get("description", "").lower()
        ]
        return {
            "gaps": matches,
            "count": len(matches),
            "query": area,
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Tool definitions (Anthropic tool_use schema)
# ---------------------------------------------------------------------------

_TOOLS = [
    {
        "name": "compute_js_ratio",
        "description": (
            "Compute the Jammer-to-Signal (J/S) ratio in dB at a given range "
            "using the Nathanson/Barton self-screening jammer equation. "
            "Also returns burn-through range — the range at which the radar "
            "breaks lock through the jamming. Use this for any question about "
            "jamming effectiveness, required jammer ERP, or burn-through ranges."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "jammer_erp_dbw": {
                    "type": "number",
                    "description": "Jammer Effective Radiated Power in dBW",
                },
                "radar_erp_dbw": {
                    "type": "number",
                    "description": "Threat radar Effective Radiated Power in dBW",
                },
                "rcs_dbsm": {
                    "type": "number",
                    "description": "Target Radar Cross Section in dBsm (e.g. F-35A ≈ −15 dBsm)",
                },
                "range_km": {
                    "type": "number",
                    "description": "Slant range between jammer/target and threat radar in km",
                },
                "jamming_mode": {
                    "type": "string",
                    "enum": ["Spot", "Sweep", "Barrage"],
                    "description": "Jamming mode (default Spot)",
                },
            },
            "required": ["jammer_erp_dbw", "radar_erp_dbw", "rcs_dbsm", "range_km"],
        },
    },
    {
        "name": "estimate_radar_erp",
        "description": (
            "Bayesian posterior estimate of a threat radar's ERP from noisy ESM "
            "power measurements. Returns the posterior mean, standard deviation, "
            "and 95% credible interval. Use this when reasoning about what threat "
            "radar ERP can be inferred from ESM intercept data."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "measurements_dbm": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "List of received-power ESM measurements in dBm",
                },
                "prior_mean_dbw": {
                    "type": "number",
                    "description": "Prior mean ERP in dBW (default 40 dBW)",
                },
                "prior_std_db": {
                    "type": "number",
                    "description": "Prior standard deviation in dB (default 15 dB)",
                },
                "measurement_noise_db": {
                    "type": "number",
                    "description": "ESM measurement noise standard deviation in dB (default 3 dB)",
                },
            },
            "required": ["measurements_dbm"],
        },
    },
    {
        "name": "lookup_threat_profile",
        "description": (
            "Return open-source ERP and frequency parameters for a known threat radar. "
            "Use this to get baseline threat parameters before running J/S calculations. "
            "Pass threat_name='list' to see all available entries."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "threat_name": {
                    "type": "string",
                    "description": (
                        "Threat system name, e.g. 'SA-10/S-300 (Fire Control)'. "
                        "Pass 'list' to enumerate available threats."
                    ),
                },
            },
            "required": ["threat_name"],
        },
    },
    {
        "name": "assess_technology_trl",
        "description": (
            "Return the Technology Readiness Level (TRL) and acquisition implications "
            "for an EW or AI technology. Use this when asked about technology maturity, "
            "what can be procured now, or how to specify requirements for emerging tech. "
            "Pass technology='list' to see all available entries."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "technology": {
                    "type": "string",
                    "description": (
                        "Technology name, e.g. 'RL adaptive jamming'. "
                        "Pass 'list' to enumerate available technologies."
                    ),
                },
            },
            "required": ["technology"],
        },
    },
    {
        "name": "query_capability_gaps",
        "description": (
            "Query the FMI-TEW capability gap register. Returns open capability gaps "
            "with acquisition relevance, urgency, allied coverage, and linked programmes. "
            "Use this when asked about Danish EW/sensor acquisition priorities or gaps."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "area": {
                    "type": "string",
                    "description": (
                        "Filter keyword (e.g. 'SHORAD', 'maritime', 'EMCON'). "
                        "Pass 'all' for the full register."
                    ),
                },
            },
            "required": [],
        },
    },
]

_TOOL_REGISTRY = {
    "compute_js_ratio":       _tool_compute_js_ratio,
    "estimate_radar_erp":     _tool_estimate_radar_erp,
    "lookup_threat_profile":  _tool_lookup_threat_profile,
    "assess_technology_trl":  _tool_assess_technology_trl,
    "query_capability_gaps":  _tool_query_capability_gaps,
}

_AGENT_SYSTEM = """\
You are an EW advisory AI assistant for FMI TEW (Danish Defence Acquisition and Logistics — \
Electronic Warfare section). Your role is that of a Team Lead for AI, Modelling and Simulation: \
providing technically rigorous, acquisition-relevant advice on Electronic Warfare, sensor systems, \
AI/ML technologies, and defence procurement.

You have access to physics simulation tools and a knowledge base of threat profiles, \
TRL assessments, and Danish capability gaps. Use them — do not guess at numbers you can compute.

Principles:
• Answer with the precision of a physicist and the clarity of a briefer
• Always run the relevant tool before stating numerical conclusions
• Flag ITAR, dual-use, and classification concerns explicitly
• Be direct: if something is not relevant or not ready for procurement, say so
• Calibrate confidence: distinguish 'open-source estimate' from 'measured data'
• Your audience ranges from programme managers to operational commanders — adjust depth to the question
"""


def _execute_tool(name: str, tool_input: dict) -> str:
    fn = _TOOL_REGISTRY.get(name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        result = fn(**tool_input)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except TypeError as e:
        return json.dumps({"error": f"Bad tool input: {e}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


def _content_to_dicts(content) -> list[dict]:
    """Convert Anthropic SDK content-block objects to plain dicts for session storage."""
    result = []
    for block in content:
        t = getattr(block, "type", None)
        if t == "text":
            result.append({"type": "text", "text": block.text})
        elif t == "tool_use":
            result.append({
                "type":  "tool_use",
                "id":    block.id,
                "name":  block.name,
                "input": block.input,
            })
        elif t == "thinking":
            result.append({"type": "thinking", "thinking": block.thinking})
        else:
            result.append({"type": t or "unknown"})
    return result


def _run_agent_turn(user_input: str, history: list, client) -> tuple[str, list, list]:
    """Run one user turn through the agent loop.

    Returns (final_text, updated_history, tool_call_log).
    tool_call_log is a list of (tool_name, tool_input, tool_result) triples for UI display.
    """
    from workflow.context import get_cached_system_blocks

    messages = history + [{"role": "user", "content": user_input}]
    tool_call_log = []

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            tools=_TOOLS,
            system=get_cached_system_blocks(),
            messages=messages,
        )

        assistant_content = _content_to_dicts(response.content)
        messages.append({"role": "assistant", "content": assistant_content})

        if response.stop_reason == "end_turn":
            final_text = next(
                (b["text"] for b in assistant_content if b["type"] == "text"), ""
            )
            return final_text, messages, tool_call_log

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in assistant_content:
                if block["type"] == "tool_use":
                    result_str = _execute_tool(block["name"], block["input"])
                    tool_call_log.append((block["name"], block["input"], result_str))
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block["id"],
                        "content":     result_str,
                    })
            messages.append({"role": "user", "content": tool_results})
        else:
            # Unexpected stop — surface what we have
            final_text = next(
                (b["text"] for b in assistant_content if b["type"] == "text"),
                f"[Unexpected stop_reason: {response.stop_reason}]",
            )
            return final_text, messages, tool_call_log


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

_EXAMPLE_QUESTIONS = [
    "What J/S ratio does a 30 dBW self-protection jammer achieve against an SA-10 at 40 km? F-35A RCS −15 dBsm.",
    "Given three ESM measurements of −42, −45, −40 dBm from 80 km, what's the most likely threat radar ERP?",
    "What is the current TRL for RL-adaptive jamming and what are the acquisition implications for the F-35A EW upgrade?",
    "What are the highest-priority open EW capability gaps in the FMI-TEW register?",
    "Compare spot vs barrage jamming effectiveness against an SA-15 at 20 km for a legacy fighter (RCS 5 dBsm).",
]

_TOOL_ICONS = {
    "compute_js_ratio":      "📡",
    "estimate_radar_erp":    "📊",
    "lookup_threat_profile": "🎯",
    "assess_technology_trl": "🔬",
    "query_capability_gaps": "🗺️",
}


def _render_tool_call(name: str, tool_input: dict, result_str: str):
    icon = _TOOL_ICONS.get(name, "🔧")
    try:
        result_obj = json.loads(result_str)
        result_display = json.dumps(result_obj, indent=2, ensure_ascii=False)
    except Exception:
        result_display = result_str

    with st.expander(f"{icon} Tool: `{name}`", expanded=False):
        col_i, col_r = st.columns(2)
        with col_i:
            st.caption("Input")
            st.code(json.dumps(tool_input, indent=2), language="json")
        with col_r:
            st.caption("Result")
            st.code(result_display, language="json")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def render():
    st.header("EW Advisory Agent")
    st.caption(
        "Multi-turn conversational agent with access to EW physics tools, threat profiles, "
        "TRL assessments, and the Danish capability gap register. "
        "Tool calls and results are shown alongside each response."
    )

    # Sidebar controls
    with st.sidebar:
        st.divider()
        st.markdown("**EW Agent tools**")
        for name, icon in _TOOL_ICONS.items():
            st.markdown(f"{icon} `{name}`")
        if st.button("Clear conversation", key="ew_agent_clear"):
            st.session_state.pop("ew_agent_history", None)
            st.session_state.pop("ew_agent_display", None)
            st.rerun()

    # Session state initialisation
    if "ew_agent_history" not in st.session_state:
        st.session_state["ew_agent_history"] = []   # API messages
    if "ew_agent_display" not in st.session_state:
        st.session_state["ew_agent_display"] = []   # [(role, text, tool_calls)]

    # Render conversation history
    for role, text, tool_calls in st.session_state["ew_agent_display"]:
        with st.chat_message(role):
            st.markdown(text)
            for tc_name, tc_input, tc_result in tool_calls:
                _render_tool_call(tc_name, tc_input, tc_result)

    # Example question buttons (only when conversation is empty)
    if not st.session_state["ew_agent_display"]:
        st.markdown("**Example questions:**")
        cols = st.columns(1)
        for q in _EXAMPLE_QUESTIONS:
            if st.button(q, key=f"ew_ex_{hash(q)}"):
                st.session_state["ew_pending_input"] = q
                st.rerun()

    # Chat input
    user_input = st.chat_input("Ask the EW advisor…")
    if not user_input and "ew_pending_input" in st.session_state:
        user_input = st.session_state.pop("ew_pending_input")

    if user_input:
        # Show user message immediately
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state["ew_agent_display"].append(("user", user_input, []))

        # Run agent
        from workflow.llm import get_native_client
        client = get_native_client()

        with st.spinner("Thinking…"):
            final_text, new_history, tool_calls = _run_agent_turn(
                user_input,
                st.session_state["ew_agent_history"],
                client,
            )

        st.session_state["ew_agent_history"] = new_history
        st.session_state["ew_agent_display"].append(("assistant", final_text, tool_calls))

        # Show assistant response
        with st.chat_message("assistant"):
            st.markdown(final_text)
            for tc_name, tc_input, tc_result in tool_calls:
                _render_tool_call(tc_name, tc_input, tc_result)
