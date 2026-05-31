# EW M&S Foundation — FMI TEW

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?logo=streamlit&logoColor=white)
![Claude](https://img.shields.io/badge/Claude-Opus%204.8%20%2F%20Sonnet%204.6-D97706)
![NumPy](https://img.shields.io/badge/NumPy-physics%20engine-013243?logo=numpy)
![Plotly](https://img.shields.io/badge/Plotly-interactive-3F4F75?logo=plotly)

A working demonstration for the Team Lead, AI Modelling & Simulation role at FMI TEW (Danish Defence Acquisition and Logistics Organisation — Electronic Warfare). Built to show what an indigenous Danish EW signal-level M&S function would do and how it would do it.

**11 tabs · 30+ interactive modules · real physics · 3 LLM integration patterns**

---

## What this application does

The app grounds EW acquisition decisions in physics rather than vendor datasheets. It covers three things the current Danish setup lacks:

1. **Signal-level stress-testing** — back-calculate what a vendor's claimed J/S figure implies about the threat radar, and flag implausible assumptions before a kravspecifikation is signed.
2. **AI/ML capability assessment** — demonstrate and benchmark adaptive jamming (RL), anomaly detection, sensor fusion, and ELINT classification at the level of detail an acquisition advisor needs.
3. **Decision-ready advisory output** — generate structured technical notes (tekniske notater), vendor assessments, and strategic briefs in the format FMI programme managers and operational commanders actually use.

---

## Module map

### Signal physics & simulation
| Module | What it models |
|--------|---------------|
| `simulation.py` | J/S ratio (Nathanson/Barton), burn-through range, ESM detection range, Monte Carlo uncertainty |
| `sead.py` | Stand-off Electronic Attack vs. defence geometry; jammer placement optimisation |
| `bayesian.py` | Conjugate Gaussian-Gaussian Bayesian update of threat radar ERP from noisy ESM intercepts |
| `fusion.py` | Multi-sensor Kalman filter (radar + ESM + IFF) with track uncertainty bands |
| `drfm.py` | Digital RF Memory deception jamming — range gate/velocity gate pull-off models |
| `network_ew.py` | Networked multi-platform EW coordination; signal geometry across distributed nodes |
| `cognitive_radar.py` | Adaptive radar response to jamming — waveform agility, PRF variation |
| `sensor_perf.py` | ERP sweep curves; detection range validation against manufacturer specs |

### AI & machine learning
| Module | What it demonstrates |
|--------|---------------------|
| `rl_jammer.py` | Q-learning adaptive jammer — mode selection against dynamic threat radar |
| `deep_rl.py` | Deep Q-network (DQN) jammer control — multi-layer neural network policy |
| `arms_race.py` | Multi-jammer coordination + attacker-defender co-evolution (arms race dynamics) |
| `anomaly.py` | Mahalanobis-distance anomaly detection on signals + ML vs threshold benchmark |
| `trl.py` | Technology Readiness Level assessment framework for AI/EW technologies |

### Acquisition advisory
| Module | What it produces |
|--------|-----------------|
| `vendor.py` | Vendor claim stress-tester (back-calculates implied radar ERP) + kravspec section generator |
| `teknisk_vurdering.py` | Technical evaluation rubric with weighted scoring |
| `risk.py` | Procurement risk engine — cost-of-inaction calculator for under-spec systems |
| `elint.py` | ELINT emitter fingerprinting and threat characterisation database |
| `eob.py` | Electronic Order of Battle — friendly and threat emitter mapping |
| `emcon.py` | EMCON compliance planner — ESM detectability under different emission states |

### Scenarios & operational planning
| Module | What it covers |
|--------|---------------|
| `killchain.py` | EW kill chain sequence modelling — detect, identify, locate, engage |
| `threat_evolution.py` | Multi-year threat parameter forecasting with uncertainty |
| `scenarios.py` | Operational scenario library — Baltic maritime, SEAD, IADS suppression |

### LLM integrations (native Anthropic SDK)
| Module | LLM pattern |
|--------|-------------|
| `teknisk_notat.py` | **Extended thinking** — `claude-opus-4-8` with 8k thinking budget; generates structured decision-ready technical notes; thinking trace visible in UI |
| `ew_agent.py` | **Tool use** — multi-turn advisory agent with 5 physics tools; `compute_js_ratio`, `estimate_radar_erp`, `lookup_threat_profile`, `assess_technology_trl`, `query_capability_gaps` |
| `gap_map.py` | **Prompt caching** — `cache_control: ephemeral` on 750-token context block; LLM-synthesised allied contribution strategy from capability matrix |
| `vendor.py` | **Structured output** — 3-step agentic pipeline (extract → verify → assess); Pydantic-enforced `ProductAnalysis` + `DanishAssessment` schemas |

### Strategic & landscape
| Module | What it covers |
|--------|---------------|
| `landscape.py` | Nordic/NATO capability heatmap across 8 organisations |
| `gap_map.py` | Allied EW M&S maturity matrix (15 areas × 6 orgs, 0–4 scale) + LLM synthesis |
| `intelligence.py` | Threat analysis interface — LangChain scrape → analyse → assess pipeline |
| `intel_kb.py` | Threat parameter knowledge base |
| `function.py` | Operational proof-points: intake workflow, capacity model, bilateral tracker, 3-year roadmap |
| `strategy.py` | Strategic positioning: NATO fora contributions, team composition, cost-of-inaction |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Streamlit UI (app.py)  ·  11 tabs  ·  30+ interactive modules  │
└──────────────┬──────────────────────────────┬───────────────────┘
               │                              │
    ┌──────────▼──────────┐       ┌───────────▼────────────┐
    │   Physics engine     │       │   LLM workflow layer   │
    │  NumPy · SciPy       │       │  workflow/llm.py       │
    │  Plotly (vis)        │       │  workflow/context.py   │
    │                      │       │  workflow/pipeline.py  │
    │  Nathanson/Barton    │       │  workflow/structured.py│
    │  Kalman filter       │       └───────────┬────────────┘
    │  Bayesian inference  │                   │
    │  Q-learning / DQN    │       ┌───────────▼────────────┐
    └──────────────────────┘       │  Anthropic SDK (native) │
                                   │  · Extended thinking    │
    ┌─────────────────────┐        │  · Tool use (agent)     │
    │   Static data layer  │        │  · Prompt caching      │
    │  data/landscape_data │        │  · Structured output   │
    │  data/function_data  │        │  LangChain (pipeline)  │
    │  data/strategy_data  │        └────────────────────────┘
    │  data/roadmap        │
    └─────────────────────┘
```

---

## Quick start

```bash
git clone https://github.com/Michael-Bach/fmi-tl-ai
cd fmi-tl-ai
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Add your Anthropic API key
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

streamlit run app.py
```

The app runs without an API key — all simulation and visualisation modules work offline. LLM features (Teknisk Notat, EW Advisor, Vendor Kravspec, Allied Synthesis) require `ANTHROPIC_API_KEY`.

---

## Stack

| Layer | Technology |
|-------|-----------|
| UI | Streamlit 1.35+ |
| Physics | NumPy, SciPy |
| Visualisation | Plotly |
| LLM (native) | Anthropic SDK — `claude-opus-4-8`, `claude-sonnet-4-6` |
| LLM (pipeline) | LangChain-Anthropic, LangChain-MistralAI |
| Data validation | Pydantic v2 |
| PDF ingestion | PyPDF |

---

## The case for this function

Danish EW acquisition currently happens without analytical grounding at the signal level. Vendor performance claims go unchallenged. Kravspecifikationer are written without simulation to stress-test the assumptions behind them. Procurement officers have no internal technical counterpart who speaks both physics and acquisition language.

Allied partners are building this capacity now. FFI (Norway) has the ALERT suite. FOI (Sweden) has radar signature and electronic attack modelling. Both are active contributors to NATO NMSG working groups. Denmark does not have a comparable node. The window to establish one — and to do it on Danish terms, with Danish acquisition priorities — is a short one.

TEW's AI M&S function is not a research unit. It is an acquisition advisory function that uses simulation and AI to do three things the current setup cannot:

1. **Stress-test vendor claims** before a kravspecifikation is signed.
2. **Model threat evolution** so that sensor procurement decisions remain valid five years out, not just at point of signature.
3. **Establish FMI as a contributing node** in Allied M&S networks — which means Denmark shapes standards rather than adopting them after the fact.

---

## Year 1 — four quarters, four deliverables

| Quarter | Period | Deliverable |
|---------|--------|-------------|
| Q1 | Aug–Oct | Internal landscape report — who has what, where TEW adds unique value |
| Q2 | Nov–Jan | Working signal-environment prototype + one-pager in decision-brief format |
| Q3 | Feb–Apr | AI prototype with benchmark vs classical baseline + NMSG working group draft |
| Q4 | May–Jul | 3-year capability roadmap + signed MOU with one industry or academic partner |

Q1 costs nothing but time and produces a document that prevents duplicating Allied work for the next three years. Q2 produces a tool that acquisition project teams can use immediately. Q3 establishes the international footprint. Q4 institutionalises the function so it survives beyond the first hire.

---

## What I bring

**Domain fluency.** Eight years Royal Danish Navy, Lieutenant Commander. I understand how EW decisions are made operationally — what a sensor procurement officer needs to know, what a programme manager will ask, where the gap between a vendor datasheet and a real threat environment actually is.

**Technical depth.** MSc Computational Physics. MSc thesis: multi-agent reinforcement learning for naval tactical decision-making using synthetic simulation data. I know where AI genuinely beats classical methods and where it introduces risk without benefit.

**Translation ability.** The simulation tab in this app produces numbers. The value is in translating those numbers into acquisition language — which is what the Q2 decision-brief deliverable is about. Technical credibility with leadership accessibility is the combination this role requires.

**Honest scope.** This is a Year 1 foundation-building role, not a production ML engineering role. The plan reflects that. Q1 and Q2 deliver real value before a single model is trained.

---

## Scope boundaries

**Not a duplication of DDRE.** DDRE does wargaming and campaign-level analysis. TEW works at the signal level — jammer vs radar vs ESM receiver physics, sensor performance modelling, electronic attack and protection in specific acquisition contexts. The landscape tab maps exactly who has what so TEW's scope is defined by genuine gaps, not ambition.

**Not AI for AI's sake.** The simulation comes first. AI enters where classical methods fail: anomaly detection on novel threat signatures, adaptive jamming response in simulation, Bayesian updating in scenarios where fixed decision rules break. The roadmap sequences this deliberately — credibility before capability, M&S before ML.

---

## Stakeholder map

| Stakeholder | Relationship |
|-------------|-------------|
| DDRE | Coordinate — campaign analysis, not signal physics |
| FFI (Norway) | Primary bilateral M&S partner — ALERT suite; avoid duplication |
| FOI (Sweden) | Nordic partner via NORDEFCO — radar signatures and EA modelling |
| TERMA / Systematic | Industry partners — hardware-in-the-loop and software environments |
| DTU / KU | Academic pipeline — unclassified layer only |
| NMSG | Standards body — FMI should contribute, not passively adopt |
