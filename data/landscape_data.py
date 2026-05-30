ORGANISATIONS = [
    {
        "Organisation": "DDRE",
        "Country": "Denmark",
        "Domain": "Multi-domain",
        "M&S capability": "Wargaming, campaign analysis",
        "Relationship to FMI TEW": "Sister org — coordinate, not duplicate",
    },
    {
        "Organisation": "FFI",
        "Country": "Norway",
        "Domain": "EW, sensors",
        "M&S capability": "ALERT suite, threat modelling",
        "Relationship to FMI TEW": "Key bilateral partner",
    },
    {
        "Organisation": "FOI",
        "Country": "Sweden",
        "Domain": "EW, radar",
        "M&S capability": "Radar signature, electronic attack",
        "Relationship to FMI TEW": "Nordic partner via NORDEFCO",
    },
    {
        "Organisation": "TERMA",
        "Country": "Denmark",
        "Domain": "EW systems",
        "M&S capability": "Hardware-in-the-loop, system integration",
        "Relationship to FMI TEW": "Industry partner",
    },
    {
        "Organisation": "Systematic",
        "Country": "Denmark",
        "Domain": "C2, ISR",
        "M&S capability": "Software simulation environments",
        "Relationship to FMI TEW": "Integration potential",
    },
    {
        "Organisation": "DTU",
        "Country": "Denmark",
        "Domain": "Signal processing, ML",
        "M&S capability": "Academic research, no classified access",
        "Relationship to FMI TEW": "Academic pipeline",
    },
    {
        "Organisation": "KU",
        "Country": "Denmark",
        "Domain": "AI/ML",
        "M&S capability": "Theory-heavy, limited defence exposure",
        "Relationship to FMI TEW": "Academic pipeline",
    },
    {
        "Organisation": "NMSG (NATO)",
        "Country": "NATO",
        "Domain": "M&S standards",
        "M&S capability": "MSG working groups, STANAG development",
        "Relationship to FMI TEW": "Standards body — FMI should contribute",
    },
]

CAPABILITY_AREAS = [
    "EW simulation",
    "Sensor modelling",
    "AI/ML integration",
    "Classified M&S",
    "Acquisition advisory",
    "NATO standards contribution",
]

# Rows: capability areas, Columns: organisations (same order as ORGANISATIONS)
# Values: 0 = none, 1 = partial, 2 = strong
CAPABILITY_MATRIX = [
    # DDRE  FFI  FOI  TERMA  Systematic  DTU  KU  NMSG
    [1,     2,   2,   2,     1,          0,   0,  1],   # EW simulation
    [1,     2,   2,   2,     0,          1,   0,  1],   # Sensor modelling
    [1,     1,   1,   1,     1,          2,   2,  0],   # AI/ML integration
    [2,     2,   2,   1,     0,          0,   0,  1],   # Classified M&S
    [2,     1,   1,   1,     1,          0,   0,  0],   # Acquisition advisory
    [1,     2,   1,   1,     0,          0,   0,  2],   # NATO standards contribution
]

ORG_NAMES = [o["Organisation"] for o in ORGANISATIONS]
