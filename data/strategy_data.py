"""
Static data for the Strategy tab: NATO fora, TRL criteria, team roles,
capability maturity dimensions, procurement examples for cost-of-inaction.
"""

# ---------------------------------------------------------------------------
# TRL criteria adapted for AI in EW sensor systems
# ---------------------------------------------------------------------------

TRL_CRITERIA = [
    {
        "level": 1,
        "label": "Basic principles observed",
        "description": "Scientific research shows the AI principle is applicable to EW signals. Published academic results only.",
        "evidence_needed": "Peer-reviewed publication demonstrating the algorithm on signal data.",
        "blocker": "No published evidence of feasibility for this specific technique + domain combination.",
    },
    {
        "level": 2,
        "label": "Technology concept formulated",
        "description": "Application to EW signals is theoretically defined. Algorithm architecture and data requirements are specified.",
        "evidence_needed": "Technical concept note mapping algorithm inputs/outputs to EW sensor data formats.",
        "blocker": "EW signal data requirements not yet defined; no concept of operations.",
    },
    {
        "level": 3,
        "label": "Experimental proof of concept",
        "description": "Algorithm validated on synthetic or controlled EW signal data. Lab conditions only.",
        "evidence_needed": "Experimental results on simulated/synthetic data with documented accuracy metrics vs. classical baseline.",
        "blocker": "No access to representative EW signal data (classified or otherwise).",
    },
    {
        "level": 4,
        "label": "Validated in lab environment",
        "description": "Algorithm validated on representative (but still controlled) EW signal datasets. Performance metrics established.",
        "evidence_needed": "Benchmark report with precision/recall, false alarm rate, computational cost vs. classical method.",
        "blocker": "No validated ground truth dataset; no hardware-in-the-loop test environment.",
    },
    {
        "level": 5,
        "label": "Validated in relevant environment",
        "description": "Tested on real or high-fidelity EW data in a simulated operational scenario. Hardware emulator or TERMA HIL.",
        "evidence_needed": "Test report from representative environment (HIL or field trial). Performance within operational tolerance.",
        "blocker": "Requires TERMA/industry HIL environment; MOU not yet in place.",
    },
    {
        "level": 6,
        "label": "Demonstrated in relevant environment",
        "description": "Prototype demonstrated in a scenario representative of operational conditions. Non-classified exercise or field demo.",
        "evidence_needed": "Technology demonstration report with operator feedback. Adversarial robustness tested.",
        "blocker": "Requires operational exercise access; classification handling for realistic threat data.",
    },
    {
        "level": 7,
        "label": "System prototype in operational environment",
        "description": "Prototype integrated with operational EW system (e.g., on ship, aircraft, or ground station). Operator-qualified.",
        "evidence_needed": "Integration test report. Operator training complete. Deployment plan approved.",
        "blocker": "Requires classified system access (FORTROLIGT+). Single-point failure risk without redundancy.",
    },
    {
        "level": 8,
        "label": "System complete and qualified",
        "description": "AI system meets all qualification requirements. Documented operational performance. Ready for procurement.",
        "evidence_needed": "Full qualification test report. Acceptance criteria met. Lifecycle support plan.",
        "blocker": "Requires full programme office engagement and kravspecifikation sign-off.",
    },
    {
        "level": 9,
        "label": "Proven in operational environment",
        "description": "System in operational service. Performance data collected over multiple deployments. Lessons learned fed back.",
        "evidence_needed": "Operational deployment records. Fleet-level performance assessment. Upgrade roadmap.",
        "blocker": "Requires sustained operational use. Not relevant for initial procurement.",
    },
]

AI_EW_TECHNIQUES = {
    "Bayesian threat parameter estimation": {
        "current_trl": 4,
        "rationale": "Conjugate Gaussian updates demonstrated on synthetic ESM data (this app). "
                     "Not yet tested on real or hardware-in-the-loop data.",
        "path_to_7": "Requires representative ESM dataset (classified or TERMA HIL). "
                     "TRL 5 needs field trial or HIL demo. TRL 6 needs exercise integration.",
    },
    "RL adaptive jamming mode selection": {
        "current_trl": 3,
        "rationale": "Q-learning demonstrated in simulation with simplified reward model (this app). "
                     "Not yet benchmarked against real jamming hardware or validated threat models.",
        "path_to_7": "TRL 4 requires realistic radar emulator. TRL 5 requires HIL. "
                     "Long path — likely Y3+ for TRL 5.",
    },
    "Anomaly detection on pulse trains": {
        "current_trl": 4,
        "rationale": "Mahalanobis-distance detection validated on synthetic pulse data. "
                     "Outperforms classical threshold on simulated novel threats. "
                     "Not yet tested on recorded real-world intercepts.",
        "path_to_7": "TRL 5 needs representative ESM recording dataset (classified). "
                     "Fastest path in the portfolio — possible Y2 if data access arranged.",
    },
    "Waveform classifier (multi-feature ML)": {
        "current_trl": 3,
        "rationale": "Simulated accuracy advantage demonstrated vs classical duty-cycle threshold. "
                     "No actual trained model — performance curve based on representative simulation.",
        "path_to_7": "TRL 4 requires actual trained classifier on real waveform data. "
                     "DTU academic collaboration could accelerate TRL 3→5 without classified data.",
    },
    "Multi-sensor Kalman fusion": {
        "current_trl": 5,
        "rationale": "Kalman fusion is a mature, well-validated technique in NATO context. "
                     "Applied here to EW sensor combination. "
                     "TRL 5 because the principle is demonstrated in relevant environments in Allied systems.",
        "path_to_7": "Not a research problem — integration engineering. "
                     "TRL 6 requires interface to operational sensor feed. "
                     "Closest to deployment-ready in the portfolio.",
    },
}

# ---------------------------------------------------------------------------
# NATO and research fora
# ---------------------------------------------------------------------------

NATO_FORA = [
    {
        "forum": "NMSG MSG-186",
        "topic": "AI in NATO Modelling and Simulation",
        "lead_nations": "USA, UK",
        "dk_status": "Not engaged",
        "tew_relevance": "Core — directly covers AI applied to M&S. First target for Danish contribution.",
        "next_event": "2026-09 (panel at I/ITSEC)",
        "contribution_type": "Case study: AI anomaly detection in EW simulation",
        "priority": "High",
    },
    {
        "forum": "NMSG MSG-173",
        "topic": "EW modelling and simulation",
        "lead_nations": "Norway (FFI), Germany",
        "dk_status": "Observer via FFI bilateral",
        "tew_relevance": "Direct — EW M&S standards and methodology. Denmark should move from observer to contributor.",
        "next_event": "2026-11 (working group meeting)",
        "contribution_type": "Baltic Sea threat environment scenario contribution",
        "priority": "High",
    },
    {
        "forum": "NATO STO SET-302",
        "topic": "Radar and EW sensor performance modelling",
        "lead_nations": "UK (DSTL), France (ONERA)",
        "dk_status": "Not engaged",
        "tew_relevance": "High — sensor performance modelling methodology directly supports TEW kravspecifikation work.",
        "next_event": "2027-03 (symposium)",
        "contribution_type": "Danish F-35A EW integration scenario (unclassified framing)",
        "priority": "Medium",
    },
    {
        "forum": "AOC Europe EW Conference",
        "topic": "Electronic Warfare — operational and technical",
        "lead_nations": "Industry + defence",
        "dk_status": "Not engaged",
        "tew_relevance": "Medium — good for vendor tracking and industry intelligence. Not a standards body.",
        "next_event": "2027-05 (annual conference)",
        "contribution_type": "Networking; no formal contribution needed",
        "priority": "Medium",
    },
    {
        "forum": "IET Radar conference",
        "topic": "Radar systems and signal processing",
        "lead_nations": "UK (IET)",
        "dk_status": "DTU publishes here occasionally",
        "tew_relevance": "Medium — academic research pipeline. Monitor for AI/ML in radar signal processing.",
        "next_event": "2026-10",
        "contribution_type": "Monitor; potential DTU collaboration vehicle",
        "priority": "Low",
    },
    {
        "forum": "NORDEFCO EW Working Group",
        "topic": "Nordic EW coordination",
        "lead_nations": "Sweden (FOI), Norway (FFI)",
        "dk_status": "Participant (Forsvaret), FMI TEW not yet engaged",
        "tew_relevance": "Very high — Nordic EW M&S is the bilateral corridor. TEW must be at the table.",
        "next_event": "2026-10 (biannual)",
        "contribution_type": "FMI TEW formal introduction; propose bilateral M&S scenario",
        "priority": "High",
    },
]

RECENT_PUBLICATIONS = [
    {
        "title": "ALERT: Advanced EW Simulation Suite for Threat Assessment",
        "authors": "FFI (Norway)",
        "year": 2024,
        "relevance": "ALERT is the primary Allied EW simulation tool. "
                     "Understanding its methodology prevents duplicating it.",
        "access": "Bilateral via FFI MOU",
    },
    {
        "title": "AI/ML Applications in Electronic Warfare: A NATO Perspective",
        "authors": "NATO STO",
        "year": 2023,
        "relevance": "NATO's current state-of-the-art survey for AI in EW. "
                     "Baseline reference for TEW's AI programme.",
        "access": "NATO UNCLASSIFIED — available via NATO TIDE",
    },
    {
        "title": "Sensor Fusion for EW Passive Geolocation",
        "authors": "FOI (Sweden)",
        "year": 2024,
        "relevance": "FOI's work on bearing-only fusion directly complements TEW's fusion work.",
        "access": "NORDEFCO channel",
    },
    {
        "title": "Machine Learning for Radar Waveform Classification",
        "authors": "IEEE AES (multiple)",
        "year": 2023,
        "relevance": "Academic baseline for the waveform classifier prototype. "
                     "DTU Electrical Engineering covers parts of this.",
        "access": "Open access (IEEE Xplore)",
    },
]

# ---------------------------------------------------------------------------
# Capability maturity model
# ---------------------------------------------------------------------------

CAPABILITY_DIMENSIONS = [
    {
        "name": "Simulation fidelity",
        "description": "Physics accuracy, validated against known references, uncertainty quantification",
        "current": 2,
        "y1_target": 3,
        "y2_target": 4,
        "y3_target": 5,
        "closing_action_y1": "Validate J/S model against FFI ALERT results; add two-way path loss",
        "closing_action_y2": "Hardware-in-the-loop validation via TERMA MOU",
        "closing_action_y3": "Classified scenario validation at FORTROLIGT level",
    },
    {
        "name": "AI integration",
        "description": "AI techniques validated, benchmarked, and used in real advisory products",
        "current": 2,
        "y1_target": 3,
        "y2_target": 4,
        "y3_target": 5,
        "closing_action_y1": "Anomaly detection TRL 4 validated; first AI advisory product delivered",
        "closing_action_y2": "Waveform classifier on real data; RL jammer TRL 5 via HIL",
        "closing_action_y3": "AI outputs feeding classified programme decisions",
    },
    {
        "name": "Allied interoperability",
        "description": "Active contribution to Allied M&S standards; bilateral data sharing",
        "current": 1,
        "y1_target": 2,
        "y2_target": 3,
        "y3_target": 4,
        "closing_action_y1": "FFI bilateral initiated; NMSG MSG-186 participation registered",
        "closing_action_y2": "First NMSG working paper submitted; NORDEFCO engagement formalised",
        "closing_action_y3": "Denmark contributing author on NATO M&S standard",
    },
    {
        "name": "Classified M&S",
        "description": "Ability to run simulation with classified threat parameters and system data",
        "current": 0,
        "y1_target": 1,
        "y2_target": 2,
        "y3_target": 4,
        "closing_action_y1": "Define classified enclave requirements; plan with FMI IT security",
        "closing_action_y2": "FORTROLIGT simulation environment operational",
        "closing_action_y3": "HEMMELIGT-capable M&S pipeline for programme-critical analyses",
    },
    {
        "name": "Acquisition advisory",
        "description": "Systematic use of M&S outputs in kravspecifikation and procurement decisions",
        "current": 1,
        "y1_target": 3,
        "y2_target": 4,
        "y3_target": 5,
        "closing_action_y1": "First vendor claim stress-test delivered to programme office",
        "closing_action_y2": "M&S-backed kravspecifikation sections standard practice in 2 programmes",
        "closing_action_y3": "TEW as standing advisory partner for all EW procurement",
    },
]

# ---------------------------------------------------------------------------
# Team composition
# ---------------------------------------------------------------------------

TEAM_ROLES = [
    {
        "year": 1,
        "title": "Team Lead — AI M&S",
        "profile": "Computational physicist + operational naval officer. "
                   "Deep AI/RL/physics background. Bilingual technical-operational.",
        "primary_skills": ["EW physics simulation", "AI/ML (RL, Bayesian, anomaly)",
                           "Acquisition advisory", "Allied coordination"],
        "covers": ["All simulation", "All AI prototypes", "Stakeholder management",
                   "NMSG engagement initiation"],
        "gap_left": ["Classified M&S environment", "Sensor hardware expertise",
                     "Bandwidth for multiple concurrent programmes"],
    },
    {
        "year": 2,
        "title": "M&S Specialist (Hire #2)",
        "profile": "MSc or PhD in physics, electrical engineering, or applied mathematics. "
                   "Experience with simulation environments (OpenGL, MATLAB, or similar). "
                   "Industry or research background preferred.",
        "primary_skills": ["High-fidelity simulation", "Hardware-in-the-loop testing",
                           "Signal processing", "STANAG/DIS/HLA protocols"],
        "covers": ["HIL environment via TERMA MOU", "FORTROLIGT simulation pipeline",
                   "NATO standards compliance", "Second analyst for concurrent programmes"],
        "gap_left": ["HEMMELIGT classification", "AI/ML operational deployment"],
    },
    {
        "year": 3,
        "title": "AI/Data Analyst (Hire #3)",
        "profile": "MSc in computer science, data science, or applied ML. "
                   "Experience with production ML systems. Defence interest preferred.",
        "primary_skills": ["ML model deployment", "Data pipeline engineering",
                           "Real-data model training", "Evaluation frameworks"],
        "covers": ["AI techniques to TRL 5+", "Real-data training pipelines",
                   "DTU academic collaboration management", "Automated advisory products"],
        "gap_left": ["Full classified AI pipeline — Year 4 planning"],
    },
]

COMPETENCY_AREAS = [
    "EW physics",
    "AI/ML",
    "Simulation engineering",
    "Acquisition advisory",
    "Allied coordination",
    "Classified operations",
    "Signal processing",
    "Technical writing",
]

TEAM_COMPETENCY_SCORES = {
    "Year 1 (TL alone)":     [4, 5, 3, 4, 3, 1, 4, 4],
    "Year 2 (TL + M&S spec)": [5, 5, 5, 4, 4, 3, 5, 4],
    "Year 3 (full team)":    [5, 5, 5, 5, 5, 4, 5, 5],
}

# ---------------------------------------------------------------------------
# Procurement examples for cost-of-inaction calculator
# ---------------------------------------------------------------------------

PROCUREMENT_EXAMPLES = [
    {
        "name": "F-35A EW upgrade (notional)",
        "value_mdkk": 800,
        "lifecycle_years": 20,
        "p_underspec_without_ms": 0.25,
        "performance_shortfall_pct": 30,
    },
    {
        "name": "SHORAD sensor system (notional)",
        "value_mdkk": 400,
        "lifecycle_years": 15,
        "p_underspec_without_ms": 0.30,
        "performance_shortfall_pct": 25,
    },
    {
        "name": "Maritime ISR upgrade (notional)",
        "value_mdkk": 250,
        "lifecycle_years": 12,
        "p_underspec_without_ms": 0.20,
        "performance_shortfall_pct": 20,
    },
    {
        "name": "Custom scenario",
        "value_mdkk": 300,
        "lifecycle_years": 15,
        "p_underspec_without_ms": 0.25,
        "performance_shortfall_pct": 25,
    },
]

# Annual cost of M&S function (3 analysts, overheads, tools)
FUNCTION_ANNUAL_COST_MDKK = 2.5  # ~3 analysts × 700k + 400k overheads
