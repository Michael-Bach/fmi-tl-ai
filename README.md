# EW M&S Foundation — FMI TEW

**Role:** Team Lead, AI Modellering og Simulering · FMI — TEW

This repo is a working reference for the role: the landscape, the Year 1 plan, and a
live signal-environment simulator. Run the app to explore interactively.

```
streamlit run app.py
```

---

## The case for this function

Danish EW acquisition currently happens without analytical grounding at the signal
level. Vendor performance claims go unchallenged. Kravspecifikationer are written
without simulation to stress-test the assumptions behind them. Procurement officers
have no internal technical counterpart who speaks both physics and acquisition language.

Allied partners are building this capacity now. FFI (Norway) has the ALERT suite.
FOI (Sweden) has radar signature and electronic attack modelling. Both are active
contributors to NATO NMSG working groups. Denmark does not have a comparable node.
The window to establish one — and to do it on Danish terms, with Danish acquisition
priorities — is a short one.

TEW's AI M&S function is not a research unit. It is an acquisition advisory function
that uses simulation and AI to do three things the current setup cannot:

1. **Stress-test vendor claims** before a kravspecifikation is signed.
2. **Model threat evolution** so that sensor procurement decisions remain valid five
   years out, not just at point of signature.
3. **Establish FMI as a contributing node** in Allied M&S networks — which means
   Denmark shapes standards rather than adopting them after the fact.

---

## What this role is not

**Not a duplication of DDRE.** DDRE does wargaming and campaign-level analysis across
domains. TEW works at the signal level — jammer vs radar vs ESM receiver physics,
sensor performance modelling, electronic attack and protection in specific acquisition
contexts. These are complementary functions. The landscape tab maps exactly who has
what so that TEW's scope is defined by genuine gaps, not ambition.

**Not AI for AI's sake.** The simulation comes first. AI enters where classical methods
fail: anomaly detection on novel threat signatures, adaptive jamming response in
simulation, Bayesian updating in scenarios where fixed decision rules break. The
roadmap sequences this deliberately — credibility before capability, M&S before ML.

---

## Year 1 — four quarters, four deliverables

| Quarter | Period | Deliverable |
|---------|--------|-------------|
| Q1 | Aug–Oct | Internal landscape report — who has what, where TEW adds unique value |
| Q2 | Nov–Jan | Working signal-environment prototype + one-pager in decision-brief format |
| Q3 | Feb–Apr | AI prototype with benchmark vs classical baseline + NMSG working group draft |
| Q4 | May–Jul | 3-year capability roadmap + signed MOU with one industry or academic partner |

Q1 costs nothing but time and produces a document that prevents duplicating Allied
work for the next three years. Q2 produces a tool that acquisition project teams can
use immediately. Q3 establishes the international footprint. Q4 institutionalises the
function so it survives beyond the first hire.

---

## What I bring to this

**Domain fluency.** Eight years Royal Danish Navy, Lieutenant Commander. I understand
how EW decisions are made operationally — what a sensor procurement officer needs to
know, what a programme manager will ask, where the gap between a vendor datasheet
and a real threat environment actually is.

**Technical depth.** MSc Computational Physics. MSc thesis: multi-agent reinforcement
learning for naval tactical decision-making using synthetic simulation data. I know
where AI genuinely beats classical methods and where it introduces risk without
benefit. I will not oversell AI to FMI leadership.

**Translation ability.** The simulation tab in this app produces numbers. The value is
in translating those numbers into acquisition language — which is what the Q2
decision-brief deliverable is about. Technical credibility with leadership accessibility
is the combination this role requires.

**Honest scope.** This is a Year 1 foundation-building role, not a production ML
engineering role. The plan reflects that. Q1 and Q2 deliver real value before a single
model is trained.

---

## Stakeholder map

The landscape tab covers the full Nordic/NATO picture. The one-line version:

- **DDRE** — coordinate, do not duplicate (campaign analysis, not signal physics)
- **FFI / FOI** — bilateral technical partners, already running M&S that TEW should
  connect to, not rebuild
- **TERMA / Systematic** — industry partners for hardware-in-the-loop and software
  environments; MOUs in Q4
- **DTU / KU** — academic pipeline for AI/ML research; no classified access, so
  collaboration is at the unclassified layer
- **NMSG** — the standards body; FMI should be a contributing member, not a passive
  adopter

---

## Talking points for the room

**On why now:**
> "Allied partners have been building this for five years. We are not ahead of the
> curve — we are catching up. The question is whether we catch up on our own terms,
> with a function designed around Danish acquisition priorities, or whether we wait
> and adopt what others built for their priorities."

**On the AI angle:**
> "AI is not the headline. Simulation is the headline. AI enters in Q3, once we have
> a credible simulation baseline to benchmark against. That sequencing is deliberate —
> a model without a physics baseline is an opinion, not an analysis."

**On resource risk:**
> "Q1 requires one person and a laptop. The deliverable is a document that prevents
> duplicating work Allied partners have already done. The cost of not doing Q1 is
> writing a kravspecifikation that DDRE or FFI could have told us was already covered."

**On the DDRE question (they will ask):**
> "DDRE operates at the campaign level. TEW works at the signal level. These are
> different abstraction layers. A campaign model needs a signal model to feed it
> realistic sensor performance — that is the interface, not the competition."
