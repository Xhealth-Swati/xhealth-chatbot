import streamlit as st

st.title("XHealth Chatbot Prototype")

st.write("This is your working chatbot prototype.")

# Chief complaint
complaint = st.selectbox(
    "What brings you in today?",
    ["cough", "chest pain", "eye redness"]
)

st.write(f"Chief Complaint: {complaint}")

# Baseline questions
st.subheader("Basic Questions")

duration = st.text_input("When did this start?")
severity = st.slider("How severe is it (1-10)?", 1, 10)
progress = st.selectbox("Is it getting better or worse?", ["better", "worse", "same"])

# Complaint-specific logic
st.subheader("Symptom Questions")

if complaint == "cough":
    cough_type = st.selectbox("Type of cough?", ["dry", "productive"])
    sob = st.checkbox("Shortness of breath?")
    fever = st.checkbox("Fever?")

elif complaint == "chest pain":
    exertion = st.checkbox("Pain with exertion?")
    radiation = st.checkbox("Pain radiates to arm?")
    sweating = st.checkbox("Sweating?")

elif complaint == "eye redness":
    discharge = st.checkbox("Discharge?")
    itching = st.checkbox("Itching?")
    dryness = st.checkbox("Dryness?")

# Simple diagnosis logic
st.subheader("Result")

if complaint == "cough":
    if cough_type == "productive" and sob:
        st.success("Likely: COPD")
    elif cough_type == "dry" and fever:
        st.success("Likely: COVID-19")
    else:
        st.info("Further evaluation needed")

elif complaint == "chest pain":
    if exertion and radiation:
        st.success("Likely: CAD")
    else:
        st.info("Further evaluation needed")

elif complaint == "eye redness":
    if discharge:
        st.success("Likely: Conjunctivitis")
    elif dryness:
        st.success("Likely: Dry Eye Syndrome")
    else:
        st.info("Further evaluation needed")
