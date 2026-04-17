import streamlit as st
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List

st.set_page_config(page_title="XHealth Chatbot Prototype", layout="centered")

# ============================================================
# XHealth Chatbot Prototype v3 - Minimal UI
# Clean intake -> concise results -> optional technical details
# ============================================================

CONDITIONS_MASTER = {
    "COPD": {"condition_id": 25, "icd10_code": "J44.9", "snomed_code": "13645005", "vector": [6, 0, 9]},
    "COVID-19": {"condition_id": 28, "icd10_code": "U07.1", "snomed_code": "840539006", "vector": [6, 9, 2]},
    "Acute Bronchitis": {"condition_id": 23, "icd10_code": "J20.9", "snomed_code": "10509002", "vector": [5, 6, 2]},
    "Coronary Atherosclerosis (CAD)": {"condition_id": 3, "icd10_code": "I25.10", "snomed_code": "53741008", "vector": [5, 0, 9]},
    "GERD": {"condition_id": 45, "icd10_code": "K21.9", "snomed_code": "235595009", "vector": [4, 0, 9]},
    "Conjunctivitis": {"condition_id": 81, "icd10_code": "H10.9", "snomed_code": "9826008", "vector": [4, 8, 1]},
    "Dry Eye Syndrome": {"condition_id": 82, "icd10_code": "H04.129", "snomed_code": "162290004", "vector": [3, 0, 9]},
}

CHIEF_COMPLAINT_MAP = {
    "cough": ["COPD", "Acute Bronchitis", "COVID-19"],
    "chest pain": ["Coronary Atherosclerosis (CAD)", "GERD"],
    "eye redness": ["Conjunctivitis", "Dry Eye Syndrome"],
}

CONDITION_SYMPTOMS = {
    "COPD": {
        "productive cough": {"ppv": 0.8, "importance": 0.9},
        "chronic cough": {"ppv": 0.85, "importance": 0.95},
        "shortness of breath": {"ppv": 0.7, "importance": 0.9},
        "wheezing": {"ppv": 0.9, "importance": 1.0},
        "cough with exertion": {"ppv": 0.8, "importance": 0.9},
        "fever": {"ppv": 0.1, "importance": 0.2},
    },
    "Acute Bronchitis": {
        "cough": {"ppv": 0.8, "importance": 0.9},
        "productive cough": {"ppv": 0.85, "importance": 0.95},
        "wheezing": {"ppv": 0.5, "importance": 0.6},
        "shortness of breath": {"ppv": 0.5, "importance": 0.6},
        "fever": {"ppv": 0.3, "importance": 0.4},
    },
    "COVID-19": {
        "dry cough": {"ppv": 0.8, "importance": 0.9},
        "shortness of breath": {"ppv": 0.6, "importance": 0.8},
        "fever": {"ppv": 0.8, "importance": 0.8},
        "fatigue": {"ppv": 0.7, "importance": 0.7},
    },
    "Coronary Atherosclerosis (CAD)": {
        "chest pain": {"ppv": 0.9, "importance": 1.0},
        "exertional chest pain": {"ppv": 0.9, "importance": 1.0},
        "radiation to left arm": {"ppv": 0.85, "importance": 0.95},
        "shortness of breath": {"ppv": 0.6, "importance": 0.7},
        "sweating": {"ppv": 0.7, "importance": 0.7},
        "heartburn": {"ppv": 0.05, "importance": 0.1},
    },
    "GERD": {
        "chest pain": {"ppv": 0.4, "importance": 0.5},
        "heartburn": {"ppv": 0.9, "importance": 1.0},
        "shortness of breath": {"ppv": 0.05, "importance": 0.1},
    },
    "Conjunctivitis": {
        "eye redness": {"ppv": 0.9, "importance": 1.0},
        "watery discharge": {"ppv": 0.8, "importance": 0.8},
        "itching": {"ppv": 0.7, "importance": 0.7},
        "eye dryness": {"ppv": 0.1, "importance": 0.1},
    },
    "Dry Eye Syndrome": {
        "eye redness": {"ppv": 0.6, "importance": 0.7},
        "eye dryness": {"ppv": 0.9, "importance": 1.0},
        "gritty sensation": {"ppv": 0.8, "importance": 0.9},
        "itching": {"ppv": 0.2, "importance": 0.3},
    },
}

RESULT_SUMMARIES = {
    "COPD": "Pattern favors chronic obstructive respiratory disease with strong support from productive or chronic cough, wheezing, and shortness of breath.",
    "Acute Bronchitis": "Pattern suggests an acute bronchial process with cough-centered symptoms and moderate respiratory support.",
    "COVID-19": "Pattern remains compatible with a viral syndrome when dry cough, fever, and fatigue are present.",
    "Coronary Atherosclerosis (CAD)": "Pattern favors ischemic chest pain when exertional symptoms and classic cardiac features are present.",
    "GERD": "Pattern suggests reflux-related chest discomfort when heartburn is prominent and cardiac features are weaker.",
    "Conjunctivitis": "Pattern supports conjunctival inflammation, especially with redness, discharge, and itching.",
    "Dry Eye Syndrome": "Pattern supports ocular surface dryness when dryness and gritty sensation are more prominent than discharge.",
}

@dataclass
class SymptomCapture:
    symptom_name: str
    symptom_present: bool
    severity_current: int
    patient_phrase: str = ""


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: #F8FBFF;
        }
        .title {
            color: #163B7A;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }
        .subtitle {
            color: #5C6B82;
            margin-bottom: 1rem;
        }
        .card {
            background: white;
            border: 1px solid #D9E7FB;
            border-radius: 14px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        .card-title {
            color: #163B7A;
            font-weight: 700;
            margin-bottom: 0.6rem;
            font-size: 1.05rem;
        }
        .dx-card {
            background: white;
            border: 1px solid #D9E7FB;
            border-left: 5px solid #163B7A;
            border-radius: 14px;
            padding: 1rem;
            margin-bottom: 0.8rem;
        }
        .dx-title {
            color: #163B7A;
            font-weight: 700;
            font-size: 1.1rem;
            margin-bottom: 0.25rem;
        }
        .muted {
            color: #5C6B82;
            font-size: 0.9rem;
        }
        .pill {
            display: inline-block;
            padding: 0.2rem 0.5rem;
            border-radius: 999px;
            background: #E8F0FF;
            color: #163B7A;
            font-size: 0.85rem;
            margin-right: 0.35rem;
            margin-bottom: 0.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def score_diagnoses(chief_complaint: str, symptoms: Dict[str, SymptomCapture]) -> List[dict]:
    candidates = CHIEF_COMPLAINT_MAP.get(chief_complaint, [])
    raw_scores = {dx: 0.0 for dx in candidates}
    evidence = {dx: [] for dx in candidates}

    for symptom_name, symptom in symptoms.items():
        if not symptom.symptom_present:
            continue
        severity = symptom.severity_current
        for dx in candidates:
            meta = CONDITION_SYMPTOMS.get(dx, {}).get(symptom_name)
            if meta:
                support = round(severity * meta["ppv"] * meta["importance"], 2)
                raw_scores[dx] += support
                evidence[dx].append({
                    "name": symptom_name,
                    "severity": severity,
                    "support_score": support,
                })

    total = sum(raw_scores.values()) or 1.0
    ranked = []
    for rank, (dx, raw) in enumerate(sorted(raw_scores.items(), key=lambda x: x[1], reverse=True), start=1):
        ranked.append({
            "condition_name": dx,
            "condition_id": CONDITIONS_MASTER[dx]["condition_id"],
            "icd10_code": CONDITIONS_MASTER[dx]["icd10_code"],
            "snomed_code": CONDITIONS_MASTER[dx]["snomed_code"],
            "vector": CONDITIONS_MASTER[dx]["vector"],
            "raw_score": round(raw, 2),
            "precision_metric": round(raw / total, 2),
            "rank": rank,
            "symptoms": sorted(evidence[dx], key=lambda x: x["support_score"], reverse=True),
            "summary": RESULT_SUMMARIES.get(dx, "Clinical pattern generated from intake evidence."),
        })
    return ranked


def build_standard_json(ranked: List[dict], patient_id: str) -> dict:
    if not ranked:
        return {}
    top = ranked[0]
    return {
        "Patient_ID": patient_id,
        "Condition_ID": top["condition_id"],
        "Condition_Name": top["condition_name"],
        "Vector": top["vector"],
        "Timestamp": datetime.utcnow().isoformat() + "Z",
        "Source": "Chatbot_v3",
    }


def render_cough_questions() -> Dict[str, SymptomCapture]:
    symptoms = {}
    cough_type = st.selectbox("Cough type", ["", "dry cough", "productive cough", "chronic cough", "cough with exertion"])
    shortness = st.checkbox("Shortness of breath")
    wheezing = st.checkbox("Wheezing")
    fever = st.checkbox("Fever")
    fatigue = st.checkbox("Fatigue")
    severity = st.slider("Overall symptom severity", 1, 10, 5)

    if cough_type:
        symptoms[cough_type] = SymptomCapture(cough_type, True, severity, cough_type)
    if shortness:
        symptoms["shortness of breath"] = SymptomCapture("shortness of breath", True, severity)
    if wheezing:
        symptoms["wheezing"] = SymptomCapture("wheezing", True, severity)
    if fever:
        symptoms["fever"] = SymptomCapture("fever", True, severity)
    if fatigue:
        symptoms["fatigue"] = SymptomCapture("fatigue", True, severity)
    return symptoms


def render_chest_pain_questions() -> Dict[str, SymptomCapture]:
    symptoms = {}
    severity = st.slider("Overall symptom severity", 1, 10, 6)
    chest_pain = st.checkbox("Chest pain present", value=True)
    exertional = st.checkbox("Worse with exertion")
    radiation = st.checkbox("Radiates to left arm")
    shortness = st.checkbox("Shortness of breath")
    sweating = st.checkbox("Sweating")
    heartburn = st.checkbox("Heartburn")

    if chest_pain:
        symptoms["chest pain"] = SymptomCapture("chest pain", True, severity)
    if exertional:
        symptoms["exertional chest pain"] = SymptomCapture("exertional chest pain", True, severity)
    if radiation:
        symptoms["radiation to left arm"] = SymptomCapture("radiation to left arm", True, severity)
    if shortness:
        symptoms["shortness of breath"] = SymptomCapture("shortness of breath", True, severity)
    if sweating:
        symptoms["sweating"] = SymptomCapture("sweating", True, severity)
    if heartburn:
        symptoms["heartburn"] = SymptomCapture("heartburn", True, severity)
    return symptoms


def render_eye_questions() -> Dict[str, SymptomCapture]:
    symptoms = {}
    severity = st.slider("Overall symptom severity", 1, 10, 4)
    redness = st.checkbox("Eye redness present", value=True)
    discharge = st.checkbox("Watery discharge")
    itching = st.checkbox("Itching")
    dryness = st.checkbox("Eye dryness")
    gritty = st.checkbox("Gritty sensation")

    if redness:
        symptoms["eye redness"] = SymptomCapture("eye redness", True, severity)
    if discharge:
        symptoms["watery discharge"] = SymptomCapture("watery discharge", True, severity)
    if itching:
        symptoms["itching"] = SymptomCapture("itching", True, severity)
    if dryness:
        symptoms["eye dryness"] = SymptomCapture("eye dryness", True, severity)
    if gritty:
        symptoms["gritty sensation"] = SymptomCapture("gritty sensation", True, severity)
    return symptoms


def main() -> None:
    inject_styles()

    if "generated" not in st.session_state:
        st.session_state.generated = False
    if "ranked" not in st.session_state:
        st.session_state.ranked = []
    if "captured" not in st.session_state:
        st.session_state.captured = {}

    st.markdown("<div class='title'>XHealth Chatbot Prototype</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Minimal prototype for structured intake, ranked diagnosis, and dashboard-ready output.</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-title'>Quick Intake</div>", unsafe_allow_html=True)

    patient_id = st.text_input("Patient ID", value="PT-10001")
    chief_complaint = st.selectbox("Chief complaint", ["cough", "chest pain", "eye redness"])
    onset = st.text_input("When did this start?", value="5 days ago")
    trajectory = st.selectbox("Trajectory", ["worsening", "stable", "improving", "fluctuating"])

    if chief_complaint == "cough":
        captured = render_cough_questions()
    elif chief_complaint == "chest pain":
        captured = render_chest_pain_questions()
    else:
        captured = render_eye_questions()

    generate = st.button("Generate Clinical Summary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if generate:
        st.session_state.captured = {k: asdict(v) for k, v in captured.items()}
        st.session_state.ranked = score_diagnoses(chief_complaint, captured)
        st.session_state.generated = True

    if st.session_state.generated and st.session_state.ranked:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>Clinical Results</div>", unsafe_allow_html=True)

        for dx in st.session_state.ranked[:2]:
            st.markdown("<div class='dx-card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='dx-title'>{dx['condition_name']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='muted'>ICD-10: {dx['icd10_code']} · Precision: {dx['precision_metric']} · Vector: {dx['vector']}</div>", unsafe_allow_html=True)
            st.write(dx["summary"])
            if dx["symptoms"]:
                st.markdown("**Top supporting symptoms**")
                pills = "".join([f"<span class='pill'>{s['name']} ({s['support_score']})</span>" for s in dx['symptoms'][:4]])
                st.markdown(pills, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("Technical details"):
            st.markdown("**Captured symptoms**")
            st.code(json.dumps(st.session_state.captured, indent=2), language="json")
            st.markdown("**Ranked differential diagnosis**")
            st.code(json.dumps(st.session_state.ranked, indent=2), language="json")
            st.markdown("**Standardized JSON output**")
            st.code(json.dumps(build_standard_json(st.session_state.ranked, patient_id), indent=2), language="json")


if __name__ == "__main__":
    main()


