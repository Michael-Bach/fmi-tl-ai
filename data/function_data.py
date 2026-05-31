import datetime

# ---------------------------------------------------------------------------
# Capability gap register
# ---------------------------------------------------------------------------

CAPABILITY_GAPS = [
    {
        "id": "GAP-001",
        "capability_area": "Self-protection jammer ERP sizing — F-35A context",
        "description": (
            "No unclassified simulation exists to validate vendor ERP claims for "
            "self-protection jammers against the projected Baltic air-defence threat. "
            "Kravspecifikationen for F-35A EW upgrades are written against stated ERP "
            "figures with no independent burn-through range verification."
        ),
        "acquisition_relevance": "F-35A EW upgrade programme (FMI air office)",
        "urgency": "High",
        "allied_coverage": "FFI: partial (ALERT suite, not cleared to DK)",
        "simulation_evidence": "Simulation tab — J/S Simulator, Spot mode, RCS −15 dBsm",
        "status": "Open",
        "last_reviewed": "2026-05-30",
        "linked_programme": "F-35A EW / AN/ASQ-239 compatibility",
    },
    {
        "id": "GAP-002",
        "capability_area": "SHORAD sensor performance validation under jamming",
        "description": (
            "Short-range air defence (SHORAD) gap remains open. No analytical baseline "
            "exists for evaluating candidate sensors under EW conditions. "
            "Procurement evaluations are conducted against manufacturer-supplied datasheets "
            "without independent stress-testing."
        ),
        "acquisition_relevance": "SHORAD urgent operational requirement (cross-service)",
        "urgency": "High",
        "allied_coverage": "None identified — potential first-mover for Denmark",
        "simulation_evidence": "Simulation tab — scan frequency bands 1–18 GHz",
        "status": "Open",
        "last_reviewed": "2026-05-30",
        "linked_programme": "SHORAD / C-UAS urgent operational requirement",
    },
    {
        "id": "GAP-003",
        "capability_area": "Maritime ISR anomaly detection — AI vs threshold methods",
        "description": (
            "Baltic and Arctic maritime ISR sensors generate continuous radar/AIS data. "
            "Emerging requirement for AI-assisted target classification. "
            "No analytical comparison of ML classification vs. threshold-based methods "
            "exists at FMI. DDRE has campaign-level models but not signal-level ML benchmarks."
        ),
        "acquisition_relevance": "Maritime ISR next-generation sensors (FMI maritime office)",
        "urgency": "Medium",
        "allied_coverage": "FOI: active research programme (NORDEFCO channel)",
        "simulation_evidence": "Bayesian Estimator — ERP inference under noise",
        "status": "Open",
        "last_reviewed": "2026-05-30",
        "linked_programme": "Søværnet ISR modernisation",
    },
    {
        "id": "GAP-004",
        "capability_area": "EMCON compliance verification tooling",
        "description": (
            "JEMSO planning is becoming a core staff skill but no unclassified tool exists "
            "to model which friendly emitters are detectable under different EMCON states. "
            "Currently handled ad-hoc by J6 staff without systematic ESM sensitivity modelling."
        ),
        "acquisition_relevance": "Cross-service operational planning (J6 / TEW advisory)",
        "urgency": "Medium",
        "allied_coverage": "No Allied open-source equivalent identified",
        "simulation_evidence": "Simulation tab — ESM detection range model",
        "status": "Open",
        "last_reviewed": "2026-05-30",
        "linked_programme": "JEMSO / spectrum management (J6 initiative)",
    },
    {
        "id": "GAP-005",
        "capability_area": "Escort vs. self-screening jammer task organisation trade-space",
        "description": (
            "No analytical basis exists for Danish Air Force decisions on escort vs. "
            "self-screening jammer task organisation for SEAD packages. "
            "Allied nations have studied this; Denmark has no independent capability to "
            "validate Allied conclusions against Danish-specific threat environments."
        ),
        "acquisition_relevance": "F-35A EW / SEAD doctrine (Flyvevåbnet operational requirements)",
        "urgency": "Medium",
        "allied_coverage": "US/USAF: classified; NATO: classified; no open-source equivalent",
        "simulation_evidence": "SEAD Scenario tab — escort geometry, R_J vs R_T trade",
        "status": "Open",
        "last_reviewed": "2026-05-30",
        "linked_programme": "SEAD capability concept (Flyvevåbnet)",
    },
]

# ---------------------------------------------------------------------------
# Allied and industry coordination tracker
# ---------------------------------------------------------------------------

BILATERAL_ENGAGEMENTS = [
    {
        "partner": "FFI (Norway)",
        "type": "Bilateral technical",
        "topic": "ALERT suite — access and joint scenario development",
        "dk_contribution": "Danish threat environment data, Baltic Sea sensor scenarios",
        "dk_benefit": "ALERT methodology, threat modelling access, EW simulation precedent",
        "status": "Q3 target",
        "next_action": "Formal engagement via FMI international office — initiate contact Q1",
        "owner": "Team Lead",
        "priority": "High",
    },
    {
        "partner": "FOI (Sweden)",
        "type": "NORDEFCO",
        "topic": "Radar signature and EA modelling — joint Baltic threat baseline",
        "dk_contribution": "Participation in NORDEFCO EW working group, Danish acquisition priorities",
        "dk_benefit": "Radar signature database access, joint publication opportunity",
        "status": "Q2 target",
        "next_action": "Contact via NORDEFCO channel — J5 introduction letter",
        "owner": "Team Lead",
        "priority": "High",
    },
    {
        "partner": "NMSG (NATO)",
        "type": "Standards body",
        "topic": "MSG-186 AI in M&S — Danish contribution to working group",
        "dk_contribution": "Case study: AI anomaly detection in EW simulation (unclassified)",
        "dk_benefit": "Access to Allied M&S developments, Danish input to STANAG drafts",
        "status": "Q3 target",
        "next_action": "Register participation intent via Danish NATO delegation",
        "owner": "Team Lead",
        "priority": "High",
    },
    {
        "partner": "TERMA",
        "type": "Industry MOU",
        "topic": "Hardware-in-the-loop test environment access — ALQ-213 characterisation",
        "dk_contribution": "Simulation methodology, academic research linkages",
        "dk_benefit": "HIL test access, real hardware performance data (unclassified threshold)",
        "status": "Q4 target",
        "next_action": "Draft MOU scope with FMI legal — Q3",
        "owner": "Team Lead",
        "priority": "Medium",
    },
    {
        "partner": "Systematic",
        "type": "Industry MOU",
        "topic": "SitaWare integration potential — EW overlay in C2 picture",
        "dk_contribution": "EW simulation outputs as C2 data feeds (format TBD)",
        "dk_benefit": "C2 integration pathway, SitaWare API access",
        "status": "Q4 target",
        "next_action": "Initial scoping meeting — Q3",
        "owner": "Team Lead",
        "priority": "Low",
    },
    {
        "partner": "DTU",
        "type": "Academic MOU",
        "topic": "Signal processing and ML research pipeline — unclassified layer",
        "dk_contribution": "Problem statements, simulation environments for research",
        "dk_benefit": "MSc/PhD thesis resources, ML research access",
        "status": "Q4 target",
        "next_action": "Contact DTU Electrical Engineering department — Q2",
        "owner": "Team Lead",
        "priority": "Medium",
    },
]

# ---------------------------------------------------------------------------
# Scope boundary — who owns which questions
# ---------------------------------------------------------------------------

SCOPE_QUESTIONS = [
    {
        "question": "What is the burn-through range of threat radar X against our F-35A self-protection suite?",
        "primary": "FMI TEW",
        "secondary": "FFI",
        "not": "DDRE",
        "rationale": "Signal-level physics. TEW owns the simulation; DDRE operates at campaign level.",
        "domain": "Signal physics",
    },
    {
        "question": "What is the campaign outcome if Denmark fields System X vs System Y?",
        "primary": "DDRE",
        "secondary": "FMI TEW",
        "not": "FMI TEW alone",
        "rationale": "Campaign analysis is DDRE's function. TEW provides signal-level performance data that feeds the DDRE model.",
        "domain": "Campaign analysis",
    },
    {
        "question": "Is the vendor's claimed J/S figure credible against the Baltic threat environment?",
        "primary": "FMI TEW",
        "secondary": "FE",
        "not": "FMI procurement office",
        "rationale": "Independent technical verification of vendor claims is TEW's core function.",
        "domain": "Acquisition advisory",
    },
    {
        "question": "What are Norway's conclusions on this specific emitter type?",
        "primary": "FMI TEW",
        "secondary": "FMI international office",
        "not": "Direct FFI contact",
        "rationale": "TEW is the technical interface to Allied EW M&S partners. Uncoordinated contacts create duplicated asks.",
        "domain": "Allied coordination",
    },
    {
        "question": "Does System X meet Danish NATO capability target requirements?",
        "primary": "FMI acquisition office",
        "secondary": "FMI TEW",
        "not": "FMI TEW alone",
        "rationale": "Capability target compliance is an acquisition decision. TEW provides technical evidence; the programme office owns the decision.",
        "domain": "Acquisition decision",
    },
    {
        "question": "What are the ITAR implications of integrating US-origin EW with EU-origin datalinks?",
        "primary": "FMI legal",
        "secondary": "FMI TEW",
        "not": "FMI TEW",
        "rationale": "Legal compliance is not TEW's function. TEW flags ITAR exposure in assessments and escalates to the correct authority.",
        "domain": "Compliance",
    },
    {
        "question": "What should the kravspecifikation say about minimum jammer ERP?",
        "primary": "FMI TEW",
        "secondary": "FMI acquisition office",
        "not": "Vendor",
        "rationale": "Setting the technical requirement is TEW's output. The programme office approves it; TEW derives it from simulation.",
        "domain": "Requirements",
    },
    {
        "question": "What does classified threat intelligence say about this radar's parameters?",
        "primary": "FE",
        "secondary": "FMI TEW",
        "not": "FMI TEW",
        "rationale": "Intelligence production is FE's function. TEW translates FE threat parameters into simulation inputs.",
        "domain": "Intelligence",
    },
]

# ---------------------------------------------------------------------------
# Decision impact log (illustrative Year 1 entries)
# ---------------------------------------------------------------------------

DECISIONS = [
    {
        "date": "2026-09-15",
        "project": "F-35A EW upgrade — vendor evaluation",
        "analysis_provided": "Independent J/S simulation at stated ERP — found 8 dB discrepancy vs vendor claim at 80 km",
        "recommendation": "Request vendor clarification on test geometry before accepting claimed J/S figure",
        "decision_made": "FMI halted kravspecifikation sign-off pending vendor clarification",
        "outcome": "Vendor revised claim by 6 dB — kravspecifikation ERP requirement adjusted upward",
        "impact": "Estimated: avoided procurement of under-spec system",
        "confidence": "High",
    },
    {
        "date": "2026-10-20",
        "project": "SHORAD sensor selection — initial screening",
        "analysis_provided": "Signal environment simulation across candidate frequency bands; ESM detection exposure analysis",
        "recommendation": "Candidate A: lower ESM exposure at cost of 15 km detection range reduction — acceptable trade in Baltic threat environment",
        "decision_made": "Programme office included ESM exposure criterion in formal evaluation",
        "outcome": "Pending — evaluation ongoing",
        "impact": "ESM criterion added to kravspecifikation for first time in Danish SHORAD procurement",
        "confidence": "Medium",
    },
    {
        "date": "2027-01-10",
        "project": "FFI bilateral — joint Baltic threat baseline",
        "analysis_provided": "Danish threat environment parameters shared with FFI; FFI ALERT results reviewed",
        "recommendation": "FFI conclusions applicable to Danish context with Baltic-specific RCS adjustments",
        "decision_made": "FMI adopted FFI Baltic threat baseline as reference — avoided duplicating threat modelling",
        "outcome": "Baseline shared; reduces FMI M&S effort by estimated 20 person-days in Y2",
        "impact": "Resource efficiency — TEW can focus on Danish-specific gaps rather than duplicating Allied work",
        "confidence": "High",
    },
]

# ---------------------------------------------------------------------------
# Three-year capability roadmap milestones (for Gantt chart)
# ---------------------------------------------------------------------------

MILESTONES_3YR = [
    # Year 1
    {"task": "Q1: Landscape report", "start": "2026-08-01", "end": "2026-10-31",
     "category": "Deliverable", "year": 1},
    {"task": "Q2: Signal environment prototype", "start": "2026-11-01", "end": "2027-01-31",
     "category": "Deliverable", "year": 1},
    {"task": "Q3: AI prototype + NMSG contribution", "start": "2027-02-01", "end": "2027-04-30",
     "category": "Deliverable", "year": 1},
    {"task": "Q4: 3-yr roadmap + first MOU", "start": "2027-05-01", "end": "2027-07-31",
     "category": "Deliverable", "year": 1},
    {"task": "FFI bilateral initiated", "start": "2026-10-01", "end": "2027-02-28",
     "category": "Bilateral", "year": 1},
    {"task": "NMSG participation registered", "start": "2027-01-01", "end": "2027-04-30",
     "category": "Bilateral", "year": 1},

    # Year 2
    {"task": "Analyst hire #2", "start": "2027-08-01", "end": "2027-10-31",
     "category": "Staffing", "year": 2},
    {"task": "Classified M&S environment (FORTROLIGT)", "start": "2027-08-01", "end": "2028-01-31",
     "category": "Infrastructure", "year": 2},
    {"task": "NMSG working group contribution (paper)", "start": "2027-09-01", "end": "2028-01-31",
     "category": "Bilateral", "year": 2},
    {"task": "FFI joint exercise support (BALTOPS)", "start": "2028-04-01", "end": "2028-06-30",
     "category": "Bilateral", "year": 2},
    {"task": "Repeatable simulation pipeline (programme teams self-serve)", "start": "2028-01-01", "end": "2028-04-30",
     "category": "Capability", "year": 2},
    {"task": "TERMA HIL access (MOU active)", "start": "2027-08-01", "end": "2028-07-31",
     "category": "Bilateral", "year": 2},

    # Year 3
    {"task": "Analyst hire #3", "start": "2028-08-01", "end": "2028-10-31",
     "category": "Staffing", "year": 3},
    {"task": "Classified M&S environment (HEMMELIGT)", "start": "2028-08-01", "end": "2029-01-31",
     "category": "Infrastructure", "year": 3},
    {"task": "Regular programme support model (standing advisory)", "start": "2028-10-01", "end": "2029-07-31",
     "category": "Capability", "year": 3},
    {"task": "NMSG working group lead role", "start": "2029-01-01", "end": "2029-07-31",
     "category": "Bilateral", "year": 3},
    {"task": "Full operational capability declaration", "start": "2029-05-01", "end": "2029-07-31",
     "category": "Deliverable", "year": 3},
]

# ---------------------------------------------------------------------------
# Intake workflow steps
# ---------------------------------------------------------------------------

INTAKE_STEPS = [
    {
        "step": "Request received",
        "owner": "Programme office",
        "duration_days": 1,
        "description": "Acquisition team submits question via standard TEW intake form. "
                        "Includes: acquisition project, question type, required-by date, classification.",
        "output": "Intake form",
    },
    {
        "step": "Scope defined",
        "owner": "Team Lead",
        "duration_days": 2,
        "description": "Team Lead reviews request, classifies question type "
                        "(simulation / intelligence / landscape / advisory), "
                        "confirms scope against TEW mandate, identifies Allied resources needed.",
        "output": "Scope statement + effort estimate",
    },
    {
        "step": "Analysis run",
        "owner": "TEW analyst",
        "duration_days": 5,
        "description": "Simulation or intelligence analysis conducted. "
                        "Confidence level assigned. Peer-reviewed by Team Lead.",
        "output": "Technical analysis with confidence tier",
    },
    {
        "step": "Brief produced",
        "owner": "Team Lead",
        "duration_days": 1,
        "description": "Decision brief formatted for programme manager audience. "
                        "Technical detail in annex; operational conclusions on front page. "
                        "Adversarial Q&A prepared for likely follow-up questions.",
        "output": "One-page decision brief + annex",
    },
    {
        "step": "Decision informed",
        "owner": "Programme office",
        "duration_days": 1,
        "description": "Brief delivered. TEW available for questions. "
                        "Outcome logged in decision impact register for accountability.",
        "output": "Logged decision entry",
    },
]

# ---------------------------------------------------------------------------
# Capacity model
# ---------------------------------------------------------------------------

CAPACITY_ACTIVITIES = [
    {"activity": "Active analysis (simulation / intelligence)", "pct_y1": 35, "pct_y2": 45, "pct_y3": 40},
    {"activity": "Stakeholder management (programme offices, leadership)", "pct_y1": 20, "pct_y2": 15, "pct_y3": 12},
    {"activity": "Allied coordination (FFI, FOI, NMSG)", "pct_y1": 15, "pct_y2": 15, "pct_y3": 15},
    {"activity": "Landscape monitoring and gap register maintenance", "pct_y1": 15, "pct_y2": 10, "pct_y3": 8},
    {"activity": "Tool development and methodology", "pct_y1": 10, "pct_y2": 10, "pct_y3": 10},
    {"activity": "Administration, reporting, training", "pct_y1": 5, "pct_y2": 5, "pct_y3": 5},
    # Y2+ has additional capacity from hire #2
    {"activity": "Analyst #2 — dedicated programme support", "pct_y1": 0, "pct_y2": 0, "pct_y3": 10},
]

CAPACITY_PROJECTS = [
    {"project": "F-35A EW upgrade", "complexity": "High", "days_est": 10, "urgency": "High"},
    {"project": "SHORAD sensor screening", "complexity": "Medium", "days_est": 5, "urgency": "High"},
    {"project": "Maritime ISR AI baseline", "complexity": "High", "days_est": 15, "urgency": "Medium"},
    {"project": "FFI bilateral initiation", "complexity": "Low", "days_est": 3, "urgency": "High"},
    {"project": "NMSG contribution draft", "complexity": "Medium", "days_est": 8, "urgency": "Medium"},
]
