from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.db import ensure_core_tables, get_connection  # noqa: E402

RuleRow = tuple[str, str, int, str, str]


def _build_rules() -> list[RuleRow]:
    return [
        # Diabetes (ADA)
        ("diabetes", "HbA1c", 1, "Confirms chronic hyperglycemia and supports diagnosis/monitoring.", "ADA Standards of Care"),
        ("diabetes", "Fasting Plasma Glucose", 1, "Establishes fasting glycemic control and diagnostic threshold.", "ADA Standards of Care"),
        ("diabetes", "Lipid Panel", 2, "Assesses cardiovascular risk profile commonly coexisting with diabetes.", "ADA Standards of Care"),
        ("diabetes", "Urine Albumin-Creatinine Ratio", 2, "Screens for early diabetic kidney disease.", "ADA Standards of Care"),
        ("diabetes", "C-Peptide", 3, "Clarifies endogenous insulin reserve when phenotype is atypical.", "ADA Standards of Care"),
        # Cardiac (AHA)
        ("cardiac", "12-Lead ECG", 1, "Rapidly detects ischemia, arrhythmia, and acute conduction abnormalities.", "AHA Chest Pain Guideline"),
        ("cardiac", "High-Sensitivity Troponin", 1, "Identifies myocardial injury and stratifies acute coronary syndrome risk.", "AHA Chest Pain Guideline"),
        ("cardiac", "Echocardiogram", 2, "Evaluates ventricular function and structural abnormalities.", "AHA/ACC Heart Failure Guideline"),
        ("cardiac", "BNP/NT-proBNP", 2, "Supports differentiation of cardiac vs non-cardiac dyspnea.", "AHA/ACC Heart Failure Guideline"),
        ("cardiac", "Cardiac Stress Test", 3, "Assesses inducible ischemia after initial stabilization.", "AHA Chronic Coronary Disease Guideline"),
        # Lung cancer (NCCN/USPSTF)
        ("lung_cancer", "Chest X-ray", 1, "Provides immediate baseline thoracic imaging for suspicious respiratory symptoms.", "NCCN Non-Small Cell Lung Cancer Guidelines"),
        ("lung_cancer", "Low-Dose CT Chest", 2, "Improves sensitivity for pulmonary nodules and early-stage lesions.", "USPSTF Lung Cancer Screening Recommendation"),
        ("lung_cancer", "Sputum Cytology", 2, "May reveal malignant cells in centrally located tumors.", "NCCN Non-Small Cell Lung Cancer Guidelines"),
        ("lung_cancer", "Bronchoscopy", 3, "Obtains tissue diagnosis and airway assessment when advanced workup is needed.", "NCCN Non-Small Cell Lung Cancer Guidelines"),
        # Thyroid (NICE)
        ("thyroid", "TSH", 1, "Primary screening marker for thyroid dysfunction.", "NICE Thyroid Disease Guidance"),
        ("thyroid", "Free T4", 1, "Characterizes severity and direction of thyroid hormone imbalance.", "NICE Thyroid Disease Guidance"),
        ("thyroid", "Anti-TPO Antibody", 2, "Supports autoimmune thyroiditis assessment.", "NICE Thyroid Disease Guidance"),
        ("thyroid", "Thyroid Ultrasound", 2, "Characterizes nodules and structural gland changes.", "NICE Thyroid Disease Guidance"),
        ("thyroid", "Radioiodine Uptake Scan", 3, "Differentiates hyperthyroid etiologies in selected cases.", "NICE Thyroid Disease Guidance"),
        # COVID (NICE)
        ("covid", "SARS-CoV-2 PCR", 1, "Confirms active viral infection with high analytic sensitivity.", "NICE COVID-19 Rapid Guideline"),
        ("covid", "Pulse Oximetry", 1, "Rapidly identifies hypoxemia and triage severity.", "NICE COVID-19 Rapid Guideline"),
        ("covid", "CRP", 2, "Tracks inflammatory burden associated with disease progression.", "NICE COVID-19 Rapid Guideline"),
        ("covid", "Chest Imaging", 2, "Evaluates pulmonary involvement when respiratory compromise is suspected.", "NICE COVID-19 Rapid Guideline"),
        ("covid", "D-Dimer", 3, "Supports thrombotic risk stratification in advanced disease.", "NICE COVID-19 Rapid Guideline"),
        # Pneumonia (NICE)
        ("pneumonia", "Chest X-ray", 1, "Confirms pulmonary infiltrates consistent with lower respiratory infection.", "NICE Pneumonia Guideline"),
        ("pneumonia", "Complete Blood Count", 1, "Evaluates leukocytosis and systemic inflammatory response.", "NICE Pneumonia Guideline"),
        ("pneumonia", "C-Reactive Protein", 2, "Supports severity assessment and treatment response monitoring.", "NICE Pneumonia Guideline"),
        ("pneumonia", "Blood Culture", 2, "Identifies bacteremia in moderate to severe infection.", "NICE Pneumonia Guideline"),
        ("pneumonia", "Procalcitonin", 3, "Adjunctive marker for bacterial etiology in selected cases.", "NICE Pneumonia Guideline"),
        # Breast cancer (NCCN)
        ("breast_cancer", "Diagnostic Mammogram", 1, "Primary imaging to evaluate suspicious breast findings.", "NCCN Breast Cancer Guidelines"),
        ("breast_cancer", "Breast Ultrasound", 1, "Characterizes masses and complements mammography.", "NCCN Breast Cancer Guidelines"),
        ("breast_cancer", "Core Needle Biopsy", 2, "Provides tissue confirmation for definitive diagnosis.", "NCCN Breast Cancer Guidelines"),
        ("breast_cancer", "Hormone Receptor Testing", 2, "Guides subtype-specific treatment planning.", "NCCN Breast Cancer Guidelines"),
        ("breast_cancer", "Breast MRI", 3, "Used for problem-solving or high-risk staging scenarios.", "NCCN Breast Cancer Guidelines"),
        # Hepatitis C (AASLD/IDSA)
        ("hepatitis_c", "HCV Antibody", 1, "Initial screening test for prior or current HCV exposure.", "AASLD/IDSA HCV Guidance"),
        ("hepatitis_c", "HCV RNA PCR", 1, "Confirms active viremia and quantifies viral burden.", "AASLD/IDSA HCV Guidance"),
        ("hepatitis_c", "Liver Function Panel", 2, "Assesses hepatic injury pattern and synthetic capacity.", "AASLD/IDSA HCV Guidance"),
        ("hepatitis_c", "Fibrosis Assessment (FIB-4/Elastography)", 2, "Stages disease to direct treatment urgency.", "AASLD/IDSA HCV Guidance"),
        ("hepatitis_c", "Genotype Test", 3, "Optional with modern pangenotypic regimens but useful in selected contexts.", "AASLD/IDSA HCV Guidance"),
    ]


def main() -> None:
    rules = _build_rules()
    with get_connection() as conn:
        ensure_core_tables(conn)
        conn.executemany(
            """
            INSERT OR REPLACE INTO disease_test_rules (
                disease_name,
                test_name,
                priority,
                clinical_reason,
                guideline_reference
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            rules,
        )
        conn.commit()
        total = conn.execute("SELECT COUNT(*) AS count FROM disease_test_rules").fetchone()["count"]
    print(f"Seeded disease_test_rules successfully. Total rows: {total}")


if __name__ == "__main__":
    main()
