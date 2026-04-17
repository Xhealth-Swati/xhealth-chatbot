import streamlit as st
import json
from datetime import datetime

st.set_page_config(page_title="XHealth Chatbot Prototype", layout="centered")

# ------------------------------------------------------------
# XHealth Chatbot Prototype
# Simple, screenshot-friendly, desktop-first Streamlit app
# ------------------------------------------------------------

CONDITIONS_MASTER = {
    "COPD": {"icd10": "J44.9", "snomed": "13645005", "vector": [6, 0, 9]},
    "COVID-19": {"icd10": "U07.1", "snomed": "840539006", "vector": [6, 9, 2]},
    "Acute Bronchitis": {"icd10": "J20.9", "snomed": "10509002", "vector": [5, 6, 2]},
    "Coronary Atherosclerosis (CAD)": {"icd10": "I25.10", "snomed": "53741008", "vector": [5, 0, 9]},
    "GERD": {"icd10": "K21.9", "snomed": "235595009", "vector": [4, 0, 9]},
    "Conjunctivitis": {"icd10": "H10.9", "snomed": "9826008", "vector": [4, 8, 1]},
    "Dry Eye Syndrome": {"icd10": "H04.129", "snomed": "162290004", "vector": [3, 0, 9]},
}

CHIEF_COMPLAINT_MAP = {
    "cough": ["COPD", "COVID-19", "Acute Bronchitis"],
    "chest pain": ["Coronary Atherosclerosis (CAD)", "GERD"],
    "eye redness": ["Conjunctivitis", "Dry Eye Syndrome"],
}

SYMPTOM_WEIGHTS = {
    "COPD": {
        "productive cough": 2.0,
        "chronic cough": 2.2,
        "shortness of breath": 2.0,
        "wheezing": 2.4,
        "cough with exertion": 1.8,
        "smoker": 1.5,
        "no fever": 0.6,
    },
    "COVID-19": {
        "dry cough": 1.7,
        "fever": 2.2,
        "fatigue": 1.6,
        "sore throat": 1.3,
        "shortness of breath": 1.8,
        "recent exposure": 2.5,
        "body aches": 1.6,
    },
    "Acute Bronchitis": {
        "productive cough": 2.0,
        "fever": 1.2,
        "fatigue": 1.1,
        "wheezing": 1.5,
        "chest discomfort": 1.2,
        "recent cold": 1.8,
    },
    "Coronary Atherosclerosis (CAD)": {
        "pressure-like chest pain": 2.6,
        "exertional chest pain": 2.6,
        "shortness of breath": 1.6,
        "radiates to arm": 2.0,
        "nausea": 1.0,
        "diabetes": 1.2,
        "hypertension": 1.2,
    },
    "GERD": {
        "burning chest pain": 2.2,
        "after meals": 1.8,
        "worse when lying down": 1.8,
        "acid taste": 2.0,
        "belching": 1.2,
        "relieved by antacids": 1.8,
    },
    "Conjunctivitis": {
        "itching": 1.8,
        "discharge": 2.1,
        "watery eyes": 1.7,
        "redness in one or both eyes": 2.0,
        "recent sick contact": 1.3,
    },
    "Dry Eye Syndrome": {
        "burning": 1.8,
        "gritty sensation": 2.2,
        "worse with screen use": 2.0,
        "mild redness": 1.2,
        "blurred vision": 1.3,
    },
}

SCREEN_OPTIONS = [
    "1. Quick Intake",
    "2. Ranked Differential",
    "3. Dashboard Summary",
    "4. JSON Output",
]


def inject_css():
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(180deg, #08111f 0%, #0b1728 100%);
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 850px;
        }
        h1, h2, h3 {
            color: #e8f1ff;
        }
        p, div, span, li {
            color: #d7e3f7;
        }
        .stCaption {
            color: #9fb3d1 !important;
        }
        .stTextInput label,
        .stSelectbox label,
        .stMultiSelect label,
        .stRadio label,
        .stTextArea label,
        .stNumberInput label {
            color: #f3f7ff !important;
            font-weight: 600 !important;
            opacity: 1 !important;
        }
        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div {
            background-color: #13233a !important;
            color: #f5f9ff !important;
            border: 1px solid #29496f !important;
            border-radius: 12px !important;
            box-shadow: none !important;
        }
        div[data-baseweb="select"] * {
            color: #f5f9ff !important;
        }
        input {
            color: #f5f9ff !important;
        }
        .stMultiSelect [data-baseweb="tag"] {
            background-color: #203754 !important;
            color: #eef5ff !important;
        }
        .stButton > button,
        .stDownloadButton > button {
            background: #2b5c97 !important;
            color: white !important;
            border: 1px solid #3a6aa5 !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
        }
        .stButton > button:hover,
        .stDownloadButton > button:hover {
            background: #356ba9 !important;
            border-color: #4d82be !important;
        }
        .stCodeBlock, pre {
            background-color: #0d1b2c !important;
            color: #eaf2ff !important;
            border-radius: 12px !important;
            border: 1px solid #26415f !important;
        }
        .x-card {
            background: rgba(18, 33, 53, 0.95);
            border: 1px solid #274565;
            border-radius: 16px;
            padding: 18px 20px;
            margin-bottom: 16px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.22);
        }
        .x-small {
            color: #9fb3d1;
            font-size: 0.92rem;
        }
        .x-rank {
            background: rgba(22, 40, 64, 0.96);
            border-left: 5px solid #5fa0ff;
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 12px;
            border-top: 1px solid #274565;
            border-right: 1px solid #274565;
            border-bottom: 1px solid #274565;
        }
        .x-tag {
            display: inline-block;
            background: #1e3551;
            color: #eaf2ff;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 0.84rem;
            margin-right: 6px;
            margin-bottom: 6px;
            border: 1px solid #31557d;
        }
        div[data-testid="stAlert"] {
            background-color: #122238 !important;
            color: #edf4ff !important;
            border: 1px solid #29496f !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state():
    if "patient_id" not in st.session_state:
        st.session_state.patient_id = "PT-10001"
    if "chief_complaint" not in st.session_state:
        st.session_state.chief_complaint = "cough"
    if "symptom_duration" not in st.session_state:
        st.session_state.symptom_duration = "5 days"
    if "progression" not in st.session_state:
        st.session_state.progression = "worsening"
    if "selected_symptoms" not in st.session_state:
        st.session_state.selected_symptoms = ["productive cough", "shortness of breath", "wheezing"]
    if "risk_factors" not in st.session_state:
        st.session_state.risk_factors = ["smoker"]
    if "results" not in st.session_state:
        st.session_state.results = []


def get_symptom_options(chief_complaint: str):
    if chief_complaint == "cough":
        return [
            "dry cough", "productive cough", "chronic cough", "shortness of breath",
            "wheezing", "fever", "fatigue", "sore throat", "body aches",
            "chest discomfort", "cough with exertion", "recent exposure", "recent cold", "no fever"
        ]
    if chief_complaint == "chest pain":
        return [
            "pressure-like chest pain", "burning chest pain", "exertional chest pain",
            "shortness of breath", "radiates to arm", "nausea", "after meals",
            "worse when lying down", "acid taste", "belching", "relieved by antacids"
        ]
    if chief_complaint == "eye redness":
        return [
            "itching", "discharge", "watery eyes", "redness in one or both eyes",
            "burning", "gritty sensation", "worse with screen use", "mild redness",
            "blurred vision", "recent sick contact"
        ]
    return []


def get_risk_factor_options(chief_complaint: str):
    if chief_complaint == "cough":
        return ["smoker"]
    if chief_complaint == "chest pain":
        return ["diabetes", "hypertension"]
    return []


def calculate_ranked_differential(chief_complaint: str, selected_symptoms: list, risk_factors: list, progression: str):
    candidate_conditions = CHIEF_COMPLAINT_MAP.get(chief_complaint, [])
    results = []

    for condition in candidate_conditions:
        score = 0.0
        evidence = []
        weights = SYMPTOM_WEIGHTS.get(condition, {})

        for item in selected_symptoms + risk_factors:
            if item in weights:
                score += weights[item]
                evidence.append(item)

        if progression == "worsening":
            score += 0.3
        elif progression == "improving":
            score -= 0.2

        results.append({
            "condition": condition,
            "score": round(score, 2),
            "evidence": evidence,
            "icd10": CONDITIONS_MASTER[condition]["icd10"],
            "snomed": CONDITIONS_MASTER[condition]["snomed"],
            "vector": CONDITIONS_MASTER[condition]["vector"],
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def severity_label(score: float):
    if score >= 5:
        return "Higher concern"
    if score >= 3:
        return "Moderate concern"
    return "Lower concern"


def make_output_payload():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "patient_id": st.session_state.patient_id,
        "timestamp": timestamp,
        "chief_complaint": st.session_state.chief_complaint,
        "symptom_duration": st.session_state.symptom_duration,
        "progression": st.session_state.progression,
        "selected_symptoms": st.session_state.selected_symptoms,
        "risk_factors": st.session_state.risk_factors,
        "ranked_differential": st.session_state.results,
    }
    return payload


def render_header():
    st.title("XHealth Clinical Intake Chatbot")
    st.caption("Minimal prototype for structured intake, ranked diagnosis, and dashboard-ready output.")


def render_screen_picker():
    return st.radio("Prototype screen", SCREEN_OPTIONS, horizontal=True)


def render_quick_intake():
    st.markdown('<div class="x-card">', unsafe_allow_html=True)
    st.subheader("Quick Intake")
    st.markdown('<div class="x-small"></div>', unsafe_allow_html=True)

    st.session_state.patient_id = st.text_input("Patient ID", value=st.session_state.patient_id)

    chief = st.selectbox(
        "Chief Complaint",
        ["cough", "chest pain", "eye redness"],
        index=["cough", "chest pain", "eye redness"].index(st.session_state.chief_complaint),
    )
    st.session_state.chief_complaint = chief

    st.session_state.symptom_duration = st.text_input("Symptom Duration / Onset", value=st.session_state.symptom_duration)
    st.session_state.progression = st.selectbox(
        "Progression",
        ["improving", "stable", "worsening"],
        index=["improving", "stable", "worsening"].index(st.session_state.progression),
    )

    symptom_options = get_symptom_options(st.session_state.chief_complaint)
    valid_selected = [s for s in st.session_state.selected_symptoms if s in symptom_options]
    if not valid_selected:
        valid_selected = symptom_options[:3]

    st.session_state.selected_symptoms = st.multiselect(
        "Associated Symptoms",
        options=symptom_options,
        default=valid_selected,
    )

    risk_options = get_risk_factor_options(st.session_state.chief_complaint)
    valid_risks = [r for r in st.session_state.risk_factors if r in risk_options]
    st.session_state.risk_factors = st.multiselect(
        "Risk Factors",
        options=risk_options,
        default=valid_risks,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Run Intake Analysis", use_container_width=True):
            st.session_state.results = calculate_ranked_differential(
                st.session_state.chief_complaint,
                st.session_state.selected_symptoms,
                st.session_state.risk_factors,
                st.session_state.progression,
            )
            st.success("Analysis complete. Move to the Ranked Differential screen.")
    with col2:
        if st.button("Load Screenshot Example", use_container_width=True):
            st.session_state.patient_id = "PT-10001"
            st.session_state.chief_complaint = "cough"
            st.session_state.symptom_duration = "5 days"
            st.session_state.progression = "worsening"
            st.session_state.selected_symptoms = ["productive cough", "shortness of breath", "wheezing"]
            st.session_state.risk_factors = ["smoker"]
            st.session_state.results = calculate_ranked_differential(
                st.session_state.chief_complaint,
                st.session_state.selected_symptoms,
                st.session_state.risk_factors,
                st.session_state.progression,
            )
            st.success("Example case loaded.")

    st.markdown('</div>', unsafe_allow_html=True)


def render_ranked_differential():
    st.subheader("Ranked Differential Diagnosis")
    st.markdown('<div class="x-small"></div>', unsafe_allow_html=True)

    if not st.session_state.results:
        st.info("No analysis available yet. Complete the Quick Intake screen first.")
        return

    for i, item in enumerate(st.session_state.results, start=1):
        st.markdown(
            f'''<div class="x-rank">
            <strong>{i}. {item['condition']}</strong><br>
            Likelihood Score: <strong>{item['score']}</strong> &nbsp; | &nbsp; Clinical Priority: <strong>{severity_label(item['score'])}</strong><br>
            ICD-10: {item['icd10']} &nbsp; | &nbsp; SNOMED CT: {item['snomed']}<br>
            Vector: {item['vector']}
            </div>''',
            unsafe_allow_html=True,
        )
        if item["evidence"]:
            st.write("Matched evidence:")
            st.markdown(" ".join([f'<span class="x-tag">{e}</span>' for e in item["evidence"]]), unsafe_allow_html=True)
        else:
            st.write("Matched evidence: none captured yet")


def render_dashboard_summary():
    st.subheader("Dashboard-Ready Summary")
    st.markdown('<div class="x-small"></div>', unsafe_allow_html=True)

    if not st.session_state.results:
        st.info("No summary available yet. Complete the Quick Intake screen first.")
        return

    top = st.session_state.results[0]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="x-card">', unsafe_allow_html=True)
        st.markdown(f"**Patient ID:** {st.session_state.patient_id}")
        st.markdown(f"**Chief Complaint:** {st.session_state.chief_complaint}")
        st.markdown(f"**Duration:** {st.session_state.symptom_duration}")
        st.markdown(f"**Progression:** {st.session_state.progression}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="x-card">', unsafe_allow_html=True)
        st.markdown(f"**Top Ranked Condition:** {top['condition']}")
        st.markdown(f"**Likelihood Score:** {top['score']}")
        st.markdown(f"**ICD-10:** {top['icd10']}")
        st.markdown(f"**SNOMED CT:** {top['snomed']}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="x-card">', unsafe_allow_html=True)
    st.markdown("**Structured Symptoms Captured**")
    st.markdown(" ".join([f'<span class="x-tag">{s}</span>' for s in st.session_state.selected_symptoms]), unsafe_allow_html=True)
    if st.session_state.risk_factors:
        st.markdown("**Risk Factors**")
        st.markdown(" ".join([f'<span class="x-tag">{r}</span>' for r in st.session_state.risk_factors]), unsafe_allow_html=True)
    st.markdown("**Clinical Vector for Top Condition**")
    st.code(str(top["vector"]))
    st.markdown('</div>', unsafe_allow_html=True)


def render_json_output():
    st.subheader("Structured JSON Output")
    st.markdown('<div class="x-small"></div>', unsafe_allow_html=True)

    if not st.session_state.results:
        st.info("No JSON output available yet. Complete the Quick Intake screen first.")
        return

    payload = make_output_payload()
    st.code(json.dumps(payload, indent=2), language="json")
    st.download_button(
        "Download JSON Output",
        data=json.dumps(payload, indent=2),
        file_name="xhealth_chatbot_output.json",
        mime="application/json",
        use_container_width=True,
    )


def main():
    inject_css()
    init_state()
    render_header()
    screen = render_screen_picker()

    if screen == "1. Quick Intake":
        render_quick_intake()
    elif screen == "2. Ranked Differential":
        render_ranked_differential()
    elif screen == "3. Dashboard Summary":
        render_dashboard_summary()
    elif screen == "4. JSON Output":
        render_json_output()


if __name__ == "__main__":
    main()

