import joblib
import numpy as np
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ================= LOAD MODEL & ENCODER =================
model_path = os.path.join(BASE_DIR, "best_pancreatic_model.sav")
encoder_path = os.path.join(BASE_DIR, "label_encoder.sav")

model = joblib.load(model_path)
label_encoder = joblib.load(encoder_path)

# ================= BASE SURVIVAL (MONTHS) PER STAGE =================
# This is the average survival for each stage
stage_base_survival_months = {
    "Normal": None,
    "Stage 1": 24,   # 2 years
    "Stage 2": 12,   # 1 year
    "Stage 3": 6     # 6 months
}

# ================= RECOMMENDATIONS (UNCHANGED) =================
recommendation_map = {
    "Normal": (
        "✔ Maintain healthy lifestyle\n"
        "✔ Annual check-up recommended\n"
        "✔ Monitor symptoms like jaundice or abdominal pain\n"
        "✔ Avoid smoking and limit alcohol intake"
    ),
    "Stage 1": (
        "✔ Immediate consultation with oncologist\n"
        "✔ Surgical resection often possible\n"
        "✔ Consider chemotherapy after surgery\n"
        "✔ Maintain nutrition & regular follow-ups"
    ),
    "Stage 2": (
        "✔ Combination therapy recommended (surgery + chemotherapy)\n"
        "✔ Monitor tumor size progression through imaging\n"
        "✔ Modify diet to maintain weight and energy levels\n"
        "✔ Regular oncologist follow-ups required"
    ),
    "Stage 3": (
        "✔ Focus on palliative care and symptom management\n"
        "✔ Pain management & supportive therapy\n"
        "✔ Chemotherapy may help slow progression\n"
        "✔ Psychological and family support crucial"
    )
}

# ================= HELPER FUNCTIONS =================
def normalize(value, min_val, max_val):
    """
    Normalize a value to range [0,1]
    """
    value = float(value)
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))


def compute_risk_score(CA19_9, NLR, Albumin, Age):
    """
    Compute lab-based risk score (0 = low risk, 1 = high risk)
    """

    risk = (
        0.35 * normalize(CA19_9, 0, 1000) +   # Tumor burden
        0.25 * normalize(NLR, 1, 10) +        # Inflammation
        0.20 * normalize(Age, 30, 80) -       # Age factor
        0.20 * normalize(Albumin, 2.0, 5.0)   # Nutrition (protective)
    )

    return max(0.0, min(1.0, risk))


# ================= MAIN PREDICTION FUNCTION =================
def predict_pancreas_stage(CA19_9, Total_Bilirubin, ALP, Albumin, NLR, Age):

    # -------- Prepare input --------
    input_data = pd.DataFrame([[ 
        float(CA19_9),
        float(Total_Bilirubin),
        float(ALP),
        float(Albumin),
        float(NLR),
        int(Age)
    ]], columns=["CA19_9", "Total_Bilirubin", "ALP", "Albumin", "NLR", "Age"])

    # -------- Stage prediction --------
    prediction = model.predict(input_data)[0]
    stage = label_encoder.inverse_transform([prediction])[0]

    # -------- Personalized survival estimation --------
    base_survival = stage_base_survival_months.get(stage, None)

    if base_survival is None:
        survival_time = "No cancer detected — normal condition."
    else:
        risk_score = compute_risk_score(CA19_9, NLR, Albumin, Age)

        # Adjust survival by up to 40% based on risk
        adjusted_months = base_survival * (1 - 0.4 * risk_score)

        if adjusted_months >= 12:
            survival_time = (
                f"Estimated survival: {adjusted_months/12:.1f} years "
                f"(personalized based on lab risk profile)."
            )
        else:
            survival_time = (
                f"Estimated survival: {adjusted_months:.0f} months "
                f"(personalized based on lab risk profile)."
            )

    # -------- Recommendations --------
    recommendations = recommendation_map.get(stage, "No recommendations available")

    return stage, survival_time, recommendations