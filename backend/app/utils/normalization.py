"""
Test name normalization.

Maps common aliases/abbreviations to a canonical normalized name.
Original extracted terminology is always preserved separately for traceability.
"""
from typing import Optional

# Canonical name → list of aliases (lower-cased for matching)
NORMALIZATION_MAP: dict[str, list[str]] = {
    "Hemoglobin": ["hb", "hgb", "haemoglobin", "hemoglobin", "hb level", "hgb level"],
    "Hematocrit": ["hct", "packed cell volume", "pcv", "haematocrit"],
    "WBC": ["wbc", "white blood cells", "white blood count", "leukocytes", "total leukocyte count", "tlc"],
    "RBC": ["rbc", "red blood cells", "red blood count", "erythrocytes"],
    "Platelets": ["platelet count", "plt", "thrombocytes", "thrombocyte count"],
    "MCV": ["mcv", "mean corpuscular volume", "mean cell volume"],
    "MCH": ["mch", "mean corpuscular hemoglobin"],
    "MCHC": ["mchc", "mean corpuscular hemoglobin concentration"],
    "Neutrophils": ["neutrophil", "neutrophils", "neuts", "polymorphonuclear cells", "pmn", "segs"],
    "Lymphocytes": ["lymphocyte", "lymphocytes", "lymphs"],
    "Monocytes": ["monocyte", "monocytes", "monos"],
    "Eosinophils": ["eosinophil", "eosinophils", "eos"],
    "Basophils": ["basophil", "basophils", "basos"],
    "Glucose (Fasting)": ["fasting glucose", "fbs", "fasting blood sugar", "fasting blood glucose", "f. glucose"],
    "Glucose (Random)": ["rbs", "random blood sugar", "random glucose", "random blood glucose"],
    "HbA1c": ["hba1c", "a1c", "glycated hemoglobin", "glycosylated hemoglobin", "hemoglobin a1c"],
    "Total Cholesterol": ["cholesterol", "total cholesterol", "tc"],
    "LDL Cholesterol": ["ldl", "ldl-c", "low density lipoprotein", "ldl cholesterol"],
    "HDL Cholesterol": ["hdl", "hdl-c", "high density lipoprotein", "hdl cholesterol"],
    "Triglycerides": ["triglyceride", "tg", "triacylglycerol"],
    "Sodium": ["na", "sodium", "na+"],
    "Potassium": ["k", "potassium", "k+"],
    "Chloride": ["cl", "chloride", "cl-"],
    "Bicarbonate": ["hco3", "bicarbonate", "co2"],
    "Creatinine": ["creatinine", "serum creatinine", "s. creatinine"],
    "BUN": ["bun", "blood urea nitrogen", "urea nitrogen"],
    "Urea": ["urea", "blood urea", "serum urea"],
    "eGFR": ["egfr", "estimated gfr", "estimated glomerular filtration rate"],
    "Uric Acid": ["uric acid", "serum uric acid", "ua"],
    "Bilirubin (Total)": ["total bilirubin", "t. bilirubin", "bilirubin total", "tbil"],
    "Bilirubin (Direct)": ["direct bilirubin", "d. bilirubin", "conjugated bilirubin", "dbil"],
    "Bilirubin (Indirect)": ["indirect bilirubin", "i. bilirubin", "unconjugated bilirubin"],
    "ALT": ["alt", "alanine aminotransferase", "sgpt", "alanine transaminase"],
    "AST": ["ast", "aspartate aminotransferase", "sgot", "aspartate transaminase"],
    "ALP": ["alp", "alkaline phosphatase"],
    "GGT": ["ggt", "gamma-glutamyl transferase", "gamma gt"],
    "Albumin": ["albumin", "serum albumin"],
    "Total Protein": ["total protein", "serum protein"],
    "TSH": ["tsh", "thyroid stimulating hormone", "thyroid-stimulating hormone"],
    "T3": ["t3", "triiodothyronine", "tri-iodothyronine"],
    "T4": ["t4", "thyroxine", "tetraiodothyronine"],
    "Free T4": ["free t4", "ft4", "free thyroxine"],
    "Free T3": ["free t3", "ft3", "free triiodothyronine"],
    "ESR": ["esr", "erythrocyte sedimentation rate", "sedimentation rate"],
    "CRP": ["crp", "c-reactive protein", "c reactive protein"],
    "Iron": ["iron", "serum iron", "fe"],
    "Ferritin": ["ferritin", "serum ferritin"],
    "TIBC": ["tibc", "total iron binding capacity"],
    "Vitamin B12": ["vitamin b12", "vit b12", "cobalamin", "b12"],
    "Vitamin D": ["vitamin d", "vit d", "25-oh vitamin d", "25-hydroxyvitamin d", "d3"],
    "Folate": ["folate", "folic acid", "vitamin b9"],
    "PSA": ["psa", "prostate specific antigen"],
    "INR": ["inr", "international normalized ratio", "pt/inr"],
    "PT": ["pt", "prothrombin time"],
    "APTT": ["aptt", "activated partial thromboplastin time", "ptt"],
}

# Build reverse lookup: alias → canonical
_REVERSE: dict[str, str] = {}
for canonical, aliases in NORMALIZATION_MAP.items():
    for alias in aliases:
        _REVERSE[alias.lower().strip()] = canonical


def normalize_test_name(raw_name: Optional[str]) -> Optional[str]:
    """
    Return the canonical name for a raw test name, or None if unrecognized.
    Never modifies the original; caller stores both.
    """
    if not raw_name:
        return None
    key = raw_name.lower().strip()
    return _REVERSE.get(key, None)
