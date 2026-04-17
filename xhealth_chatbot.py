import streamlit as st
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple

st.set_page_config(page_title="XHealth Chatbot Prototype v2", layout="centered")

# ============================================================
# XHealth Chatbot Prototype v2
# Upgraded to reflect the real XHealth internship structure:
# - 20-condition aligned condition master
# - symptom synonym normalization
# - baseline intake
# - complaint-specific branching
# - iterative-style scoring support
# - vector output + JSON output
# - dashboard-style diagnosis cards
# ============================================================

# -------------------------------------------------------------------
# CONDITION MASTER (aligned to XHealth shared overview + your role)
# -------------------------------------------------------------------
CONDITIONS_MASTER = {
    "Acute Upper Respiratory Infection": {
        "condition_id": 19,
        "icd10_code": "J06.9",
        "snomed_code": "195798008",
        "vector": [3, 8, 1],
        "category": "Respiratory",
    },
    "Acute Pharyngitis": {
        "condition_id": 20,
        "icd10_code": "J02.9",
        "snomed_code": "363746003",
        "vector": [4, 7, 1],
        "category": "Respiratory",
    },
    "Acute Sinusitis": {
        "condition_id": 21,
        "icd10_code": "J01.90",
        "snomed_code": "36971009",
        "vector": [5, 3, 2],
        "category": "Respiratory",
    },
    "Allergic Rhinitis": {
        "condition_id": 22,
        "icd10_code": "J30.9",
        "snomed_code": "61582004",
        "vector": [3, 0, 8],
        "category": "Respiratory",
    },
    "Acute Bronchitis": {
        "condition_id": 23,
        "icd10_code": "J20.9",
        "snomed_code": "10509002",
        "vector": [5, 6, 2],
        "category": "Respiratory",
    },
    "Asthma": {
        "condition_id": 24,
        "icd10_code": "J45.909",
        "snomed_code": "195967001",
        "vector": [6, 0, 9],
        "category": "Respiratory",
    },
    "COPD": {
        "condition_id": 25,
        "icd10_code": "J44.9",
        "snomed_code": "13645005",
        "vector": [6, 0, 9],
        "category": "Respiratory",
    },
    "Influenza": {
        "condition_id": 26,
        "icd10_code": "J11.1",
        "snomed_code": "6142004",
        "vector": [6, 9, 1],
        "category": "Respiratory",
    },
    "Pneumonia": {
        "condition_id": 27,
        "icd10_code": "J18.9",
        "snomed_code": "233604007",
        "vector": [8, 6, 2],
        "category": "Respiratory",
    },
    "COVID-19": {
        "condition_id": 28,
        "icd10_code": "U07.1",
        "snomed_code": "840539006",
        "vector": [6, 9, 2],
        "category": "Respiratory",
    },
    "Coronary Atherosclerosis (CAD)": {
        "condition_id": 3,
        "icd10_code": "I25.10",
        "snomed_code": "53741008",
        "vector": [5, 0, 9],
        "category": "Cardiovascular",
    },
    "GERD": {
        "condition_id": 45,
        "icd10_code": "K21.9",
        "snomed_code": "235595009",
        "vector": [4, 0, 9],
        "category": "Gastrointestinal",
    },
    "Constipation": {
        "condition_id": 47,
        "icd10_code": "K59.00",
        "snomed_code": "14760008",
        "vector": [3, 0, 3],
        "category": "Gastrointestinal",
    },
    "Abdominal Pain": {
        "condition_id": 49,
        "icd10_code": "R10.9",
        "snomed_code": "21522001",
        "vector": [5, 0, 2],
        "category": "Gastrointestinal",
    },
    "Nausea and Vomiting": {
        "condition_id": 50,
        "icd10_code": "R11.2",
        "snomed_code": "16932000",
        "vector": [5, 4, 1],
        "category": "Gastrointestinal",
    },
    "Cervicalgia": {
        "condition_id": 36,
        "icd10_code": "M54.2",
        "snomed_code": "301313002",
        "vector": [5, 0, 5],
        "category": "Musculoskeletal",
    },
    "Conjunctivitis": {
        "condition_id": 81,
        "icd10_code": "H10.9",
        "snomed_code": "9826008",
        "vector": [4, 8, 1],
        "category": "Ophthalmology",
    },
    "Dry Eye Syndrome": {
        "condition_id": 82,
        "icd10_code": "H04.129",
        "snomed_code": "162290004",
        "vector": [3, 0, 9],
        "category": "Ophthalmology",
    },
    "Essential Hypertension": {
        "condition_id": 1,
        "icd10_code": "I10",
        "snomed_code": "38341003",
        "vector": [1, 0, 9],
        "category": "Cardiovascular",
    },
    "Fatigue": {
        "condition_id": 87,
        "icd10_code": "R53.83",
        "snomed_code": "84229001",
        "vector": [4, 0, 5],
        "category": "General",
    },
}

# -------------------------------------------------------------------
# CHIEF COMPLAINT -> INITIAL DIFFERENTIAL MAP
# -------------------------------------------------------------------
CHIEF_COMPLAINT_MAP = {
    "cough": [
        "Acute Upper Respiratory Infection",
        "Acute Bronchitis",
        "Asthma",
        "COPD",
        "Influenza",
        "Pneumonia",
        "COVID-19",
    ],
    "chest pain": [
        "Coronary Atherosclerosis (CAD)",
        "GERD",
    ],
    "eye redness": [
        "Conjunctivitis",
        "Dry Eye Syndrome",
    ],
    "constipation": [
        "Constipation",
        "Abdominal Pain",
        "GERD",
    ],
    "neck pain": [
        "Cervicalgia",
    ],
    "fatigue": [
        "Fatigue",
        "Essential Hypertension",
        "COVID-19",
    ],
}

# -------------------------------------------------------------------
# PATIENT LANGUAGE NORMALIZATION
# -------------------------------------------------------------------
SYNONYMS = {
    "cough": "cough",
    "dry cough": "dry cough",
    "productive cough": "productive cough",
    "chronic cough": "chronic cough",
    "breathlessness": "shortness of breath",
    "dyspnea": "shortness of breath",
    "can t breathe properly": "shortness of breath",
    "shortness of breath": "shortness of breath",
    "wheezing": "wheezing",
    "fever": "fever",
    "feverish": "fever",
    "chest pressure": "chest pain",
    "chest tightness": "chest pain",
    "chest pain": "chest pain",
    "red eye": "eye redness",
    "pink eye": "eye redness",
    "eye redness": "eye redness",
    "dry eyes": "eye dryness",
    "gritty eyes": "gritty sensation",
    "itchy eyes": "itching",
    "constipation": "constipation",
    "hard stools": "constipation",
    "stomach pain": "abdominal pain",
    "neck stiffness": "neck pain",
    "tiredness": "fatigue",
}

# -------------------------------------------------------------------
# CONDITION -> SYMPTOM SUPPORT MAP
# These are prototype values. Replace later with your exact workbook values.
# -------------------------------------------------------------------
CONDITION_SYMPTOMS = {
    "Acute Upper Respiratory Infection": {
        "cough": {"ppv": 0.5, "importance": 0.6},
        "fever": {"ppv": 0.4, "importance": 0.5},
        "sore throat": {"ppv": 0.6, "importance": 0.7},
    },
    "Acute Bronchitis": {
        "cough": {"ppv": 0.8, "importance": 0.9},
        "productive cough": {"ppv": 0.85, "importance": 0.95},
        "wheezing": {"ppv": 0.5, "importance": 0.6},
        "shortness of breath": {"ppv": 0.5, "importance": 0.6},
    },
    "Asthma": {
        "cough": {"ppv": 0.5, "importance": 0.5},
        "shortness of breath": {"ppv": 0.8, "importance": 0.9},
        "wheezing": {"ppv": 0.9, "importance": 1.0},
        "cough with exertion": {"ppv": 0.8, "importance": 0.9},
    },
    "COPD": {
        "productive cough": {"ppv": 0.8, "importance": 0.9},
        "chronic cough": {"ppv": 0.85, "importance": 0.95},
        "shortness of breath": {"ppv": 0.7, "importance": 0.9},
        "wheezing": {"ppv": 0.9, "importance": 1.0},
        "cough with exertion": {"ppv": 0.8, "importance": 0.9},
    },
    "Influenza": {
        "dry cough": {"ppv": 0.7, "importance": 0.8},
        "fever": {"ppv": 0.9, "importance": 1.0},
        "fatigue": {"ppv": 0.7, "importance": 0.7},
    },
    "Pneumonia": {
        "cough": {"ppv": 0.7, "importance": 0.8},
        "fever": {"ppv": 0.8, "importance": 0.9},
        "shortness of breath": {"ppv": 0.7, "importance": 0.9},
    },
    "COVID-19": {
        "dry cough": {"ppv": 0.8, "importance": 0.9},
        "fever": {"ppv": 0.8, "importance": 0.8},
        "shortness of breath": {"ppv": 0.6, "importance": 0.8},
        "fatigue": {"ppv": 0.7, "importance": 0.7},
    },
    "Coronary Atherosclerosis (CAD)": {
        "chest pain": {"ppv": 0.9, "importance": 1.0},
        "exertional chest pain": {"ppv": 0.9, "importance": 1.0},
        "radiation to left arm": {"ppv": 0.85, "importance": 0.95},
        "shortness of breath": {"ppv": 0.6, "importance": 0.7},
        "sweating": {"ppv": 0.7, "importance": 0.7},
    },
    "GERD": {
        "chest pain": {"ppv": 0.4, "importance": 0.5},
        "heartburn": {"ppv": 0.9, "importance": 1.0},
        "abdominal pain": {"ppv": 0.5, "importance": 0.5},
    },
    "Constipation": {
        "constipation": {"ppv": 0.95, "importance": 1.0},
        "abdominal pain": {"ppv": 0.4, "importance": 0.5},
    },
    "Abdominal Pain": {
        "abdominal pain": {"ppv": 0.9, "importance": 1.0},
        "nausea": {"ppv": 0.5, "importance": 0.5},
    },
    "Nausea and Vomiting": {
        "nausea": {"ppv": 0.9, "importance": 1.0},
        "vomiting": {"ppv": 0.9, "importance": 1.0},
        "abdominal pain": {"ppv": 0.4, "importance": 0.5},
    },
    "Cervicalgia": {
        "neck pain": {"ppv": 0.95, "importance": 1.0},
        "neck stiffness": {"ppv": 0.7, "importance": 0.8},
    },
    "Conjunctivitis": {
        "eye redness": {"ppv": 0.9, "importance": 1.0},
        "watery discharge": {"ppv": 0.8, "importance": 0.8},
        "itching": {"ppv": 0.7, "importance": 0.7},
    },
    "Dry Eye Syndrome": {
        "eye redness": {"ppv": 0.6, "importance": 0.7},
        "eye dryness": {"ppv": 0.9, "importance": 1.0},
        "gritty sensation": {"ppv": 0.8, "importance": 0.9},
    },
    "Essential Hypertension": {
        "fatigue": {"ppv": 0.1, "importance": 0.2},
        "headache": {"ppv": 0.2, "importance": 0.3},
    },
    "Fatigue": {
        "fatigue": {"ppv": 0.95, "importance": 1.0},
    },
}

# -------------------------------------------------------------------
# CHIEF COMPLAINT QUESTION SETS
# -------------------------------------------------------------------
BRANCHING_QUESTIONS = {
    "cough": [
        ("What kind of cough is it?", ["dry cough", "productive cough", "chronic cough", "cough with exertion"]),
        ("Do you feel short of breath?", ["shortness of breath"]),
        ("Do you have wheezing?", ["wheezing"]),
        ("Do you have fever?", ["fever"]),
        ("Do you feel unusually tired?", ["fatigue"]),
    ],
    "chest pain": [
        ("Does it happen with exertion?", ["exertional chest pain"]),
        ("Does it radiate to the left arm?", ["radiation to left arm"]),
        ("Do you feel short of breath?", ["shortness of breath"]),
        ("Are you sweating?", ["sweating"]),
        ("Do you have heartburn?", ["heartburn"]),
    ],
    "eye redness": [
        ("Do you have watery discharge?", ["watery discharge"]),
        ("Do you have itching?", ["itching"]),
        ("Do your eyes feel dry?", ["eye dryness"]),
        ("Do they feel gritty?", ["gritty sensation"]),
    ],
    "constipation": [
        ("Are you having abdominal pain?", ["abdominal pain"]),
        ("Do you feel nauseated?", ["nausea"]),
    ],
    "neck pain": [
        ("Do you feel neck stiffness?", ["neck stiffness"]),
    ],
    "fatigue": [
        ("Do you also have fever?", ["fever"]),
        ("Do you also have cough?", ["cough"]),
        ("Do you have headache?", ["headache"]),
    ],
}

BASELINE_FIELDS = [
    ("onset", "When did this start?"),
    ("trajectory", "Is it improving, worsening, stable, or fluctuating?"),
    ("severity_current", "How severe is it now (1-10)?"),
    ("severity_worst", "How severe was it at its worst (1-10)?"),
    ("pattern", "Is it constant or intermittent?"),
    ("attempted_therapy", "Have you tried anything for it?"),
    ("therapy_response", "Did it help?"),
    ("precipitating_factors", "What makes it worse or brings it on?"),
    ("relieving_factors", "What makes it better?"),
]

XHEALTH_COLORS = {
    "primary": "#1E3A8A",   # dark blue
    "light": "#EFF6FF",     # very light blue background
    "border": "#DBEAFE",
    "text": "#1E293B",
    "muted": "#64748B",
    "white": "#FFFFFF",
}


@dataclass
class SymptomCapture:
    symptom_name: str
    symptom_present: bool
    patient_phrase: str = ""
    onset: str = ""
    trajectory: str = ""
    severity_current: int = 0
    severity_worst: int = 0
    pattern: str = ""
    attempted_therapy: str = ""
    therapy_response: str = ""
    precipitating_factors: str = ""
    relieving_factors: str = ""
    data_source: str = "patient-reported"
    privacy_flag: bool = False


def init_state() -> None:
    defaults = {
        "patient_id": "PT-10001",
        "chief_complaint": "cough",
        "baseline": {},
        "symptoms": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def normalize_term(term: str) -> str:
    term = (term or "").strip().lower()
    return SYNONYMS.get(term, term)


def get_candidate_conditions(chief_complaint: str) -> List[str]:
    return CHIEF_COMPLAINT_MAP.get(chief_complaint, [])


def symptom_support_for_condition(condition: str, symptom: str, severity: int) -> float:
    support = CONDITION_SYMPTOMS.get(condition, {}).get(symptom)
    if not support:
        return 0.0
    return round(severity * support["ppv"] * support["importance"], 2)


def score_diagnoses(chief_complaint: str, captured_symptoms: Dict[str, SymptomCapture]) -> List[dict]:
    candidates = get_candidate_conditions(chief_complaint)
    raw_scores: Dict[str, float] = {c: 0.0 for c in candidates}
    symptom_rows: Dict[str, List[dict]] = {c: [] for c in candidates}

    for symptom_name, obj in captured_symptoms.items():
        if not obj.symptom_present:
            continue
        severity = obj.severity_current or st.session_state.baseline.get("severity_current", 1) or 1
        for condition in candidates:
            score = symptom_support_for_condition(condition, symptom_name, severity)
            if score > 0:
                meta = CONDITION_SYMPTOMS[condition][symptom_name]
                raw_scores[condition] += score
                symptom_rows[condition].append(
                    {
                        "name": symptom_name,
                        "severity": severity,
                        "ppv": meta["ppv"],
                        "importance": meta["importance"],
                        "support_score": score,
                    }
                )

    total = sum(raw_scores.values()) or 1.0
    ranked = []
    sorted_scores = sorted(raw_scores.items(), key=lambda x: x[1], reverse=True)
    for rank, (condition, raw_score) in enumerate(sorted_scores, start=1):
        master = CONDITIONS_MASTER[condition]
        likelihood = round(raw_score / total, 2)
        ranked.append(
            {
                "condition_name": condition,
                "condition_id": master["condition_id"],
                "icd10_code": master["icd10_code"],
                "snomed_code": master["snomed_code"],
                "vector": master["vector"],
                "category": master["category"],
                "raw_score": round(raw_score, 2),
                "likelihood_score": likelihood,
                "precision_metric": likelihood,
                "rank": rank,
                "symptoms": sorted(symptom_rows[condition], key=lambda x: x["support_score"], reverse=True),
            }
        )
    return ranked


def build_standard_json(ranked: List[dict]) -> dict:
    if not ranked:
        return {}
    top = ranked[0]
    return {
        "Patient_ID": st.session_state.patient_id,
        "Condition_ID": top["condition_id"],
        "Condition_Name": top["condition_name"],
        "Vector": top["vector"],
        "Timestamp": datetime.utcnow().isoformat() + "Z",
        "Source": "Chatbot_v2",
    }


def inject_styles() -> None:
    st.markdown(
        f"""
        <style>
            .stApp {{
                background-color: {XHEALTH_COLORS['light']};
            }}

            .main-title {{
                color: {XHEALTH_COLORS['primary']};
                font-weight: 700;
                margin-bottom: 0.3rem;
            }}

            .subtitle {{
                color: {XHEALTH_COLORS['muted']};
                font-size: 0.95rem;
                margin-bottom: 1.2rem;
            }}

            .section-card {{
                background: {XHEALTH_COLORS['white']};
                border: 1px solid {XHEALTH_COLORS['border']};
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 1rem;
            }}

            .section-title {{
                color: {XHEALTH_COLORS['primary']};
                font-size: 1.05rem;
                font-weight: 600;
                margin-bottom: 0.6rem;
            }}

            .dx-card {{
                background: {XHEALTH_COLORS['white']};
                border-left: 4px solid {XHEALTH_COLORS['primary']};
                border-radius: 10px;
                padding: 0.8rem;
                margin-bottom: 0.6rem;
            }}

            .small-note {{
                color: {XHEALTH_COLORS['muted']};
                font-size: 0.9rem;
            }}

            div[data-testid="stMetric"] {{
                background: {XHEALTH_COLORS['light']};
                border: 1px solid {XHEALTH_COLORS['border']};
                border-radius: 10px;
                padding: 0.4rem;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### Setup")
        st.session_state.patient_id = st.text_input("Patient ID", value=st.session_state.patient_id)
        st.session_state.chief_complaint = st.selectbox(
            "Chief Complaint",
            list(CHIEF_COMPLAINT_MAP.keys()),
            index=list(CHIEF_COMPLAINT_MAP.keys()).index(st.session_state.chief_complaint),
        )
        with st.expander("Initial candidate conditions", expanded=False):
            for dx in get_candidate_conditions(st.session_state.chief_complaint):
                st.write(f"• {dx}")
        if st.button("Reset session", use_container_width=True):
            st.session_state.baseline = {}
            st.session_state.symptoms = {}
            st.rerun()


def render_baseline() -> None:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>1. Baseline Intake</div>", unsafe_allow_html=True)
    for key, label in BASELINE_FIELDS:
        if "severity" in key:
            st.session_state.baseline[key] = st.slider(label, 0, 10, st.session_state.baseline.get(key, 0), key=f"base_{key}")
        elif key == "trajectory":
            st.session_state.baseline[key] = st.selectbox(label, ["", "improving", "worsening", "stable", "fluctuating"], key=f"base_{key}")
        elif key == "pattern":
            st.session_state.baseline[key] = st.selectbox(label, ["", "constant", "intermittent"], key=f"base_{key}")
        else:
            st.session_state.baseline[key] = st.text_input(label, value=st.session_state.baseline.get(key, ""), key=f"base_{key}")
    st.markdown("</div>", unsafe_allow_html=True)


def add_symptom(symptom_name: str, patient_phrase: str = "") -> None:
    st.session_state.symptoms[symptom_name] = SymptomCapture(
        symptom_name=symptom_name,
        symptom_present=True,
        patient_phrase=patient_phrase or symptom_name,
        onset=st.session_state.baseline.get("onset", ""),
        trajectory=st.session_state.baseline.get("trajectory", ""),
        severity_current=st.session_state.baseline.get("severity_current", 0),
        severity_worst=st.session_state.baseline.get("severity_worst", 0),
        pattern=st.session_state.baseline.get("pattern", ""),
        attempted_therapy=st.session_state.baseline.get("attempted_therapy", ""),
        therapy_response=st.session_state.baseline.get("therapy_response", ""),
        precipitating_factors=st.session_state.baseline.get("precipitating_factors", ""),
        relieving_factors=st.session_state.baseline.get("relieving_factors", ""),
    )


def render_branching(chief_complaint: str) -> None:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>2. Symptom Questions</div>", unsafe_allow_html=True)
    for prompt, options in BRANCHING_QUESTIONS.get(chief_complaint, []):
        if len(options) == 1:
            symptom = options[0]
            present = st.checkbox(prompt, key=f"chk_{chief_complaint}_{symptom}")
            if present:
                add_symptom(symptom, symptom)
            else:
                st.session_state.symptoms.pop(symptom, None)
        else:
            selected = st.selectbox(prompt, [""] + options, key=f"sel_{chief_complaint}_{prompt}")
            if selected:
                add_symptom(selected, selected)
    st.markdown("</div>", unsafe_allow_html=True)


def render_dashboard(ranked: List[dict]) -> None:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>3. Ranked Differential</div>", unsafe_allow_html=True)
    if not ranked:
        st.info("Complete the intake to generate ranked diagnoses.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    for dx in ranked[:3]:
        st.markdown("<div class='dx-card'>", unsafe_allow_html=True)
        a, b, c = st.columns([3, 1.4, 1.4])
        a.markdown(f"**{dx['condition_name']}**")
        b.metric("ICD-10", dx["icd10_code"])
        c.metric("Score", dx["precision_metric"])
        st.caption(f"Rank #{dx['rank']} · Vector: {dx['vector']}")
        if dx["symptoms"]:
            concise_rows = [
                {"Symptom": s["name"], "Severity": s["severity"], "Contribution": s["support_score"]}
                for s in dx["symptoms"][:5]
            ]
            st.dataframe(concise_rows, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_json_and_appendix(ranked: List[dict]) -> None:
    with st.expander("Standardized JSON Output", expanded=False):
        st.code(json.dumps(build_standard_json(ranked), indent=2), language="json")

    with st.expander("Appendix-Ready Evidence", expanded=False):
        tab1, tab2 = st.tabs(["Captured Symptoms", "Ranked Differential"])
        with tab1:
            st.code(json.dumps({k: asdict(v) for k, v in st.session_state.symptoms.items()}, indent=2), language="json")
        with tab2:
            st.code(json.dumps(ranked, indent=2), language="json")


def main() -> None:
    init_state()
    inject_styles()
    render_sidebar()

    st.markdown("<h1 class='main-title'>XHealth Chatbot Prototype</h1>", unsafe_allow_html=True)
    st.markdown(
        "<div class='subtitle'>A simple prototype for structured intake, diagnosis ranking, and dashboard-ready output.</div>",
        unsafe_allow_html=True,
    )

    render_baseline()
    render_branching(st.session_state.chief_complaint)
    ranked = score_diagnoses(st.session_state.chief_complaint, st.session_state.symptoms)
    render_dashboard(ranked)
    render_json_and_appendix(ranked)


if __name__ == "__main__":
    main()


