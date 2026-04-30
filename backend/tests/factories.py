from __future__ import annotations

import factory


class PatientFactory(factory.Factory):
    class Meta:
        model = dict

    name = factory.Sequence(lambda n: f"Test Patient {n}")
    age = 52
    gender = "female"
    phone = "555-0100"
    medical_history = "hypertension"


class VisitFactory(factory.Factory):
    class Meta:
        model = dict

    patient_id = "1"
    chief_complaint = "fatigue, polyuria, polydipsia"


class VitalsFactory(factory.Factory):
    class Meta:
        model = dict

    visit_id = "1"
    heart_rate = 92
    respiratory_rate = 18
    temperature = 37.0
    oxygen_saturation = 98
    systolic_bp = 118
    diastolic_bp = 76


class SymptomsFactory(factory.Factory):
    class Meta:
        model = dict

    fatigue = True
    polyuria = True
    polydipsia = True
    chest_pain = False
    shortness_of_breath = False
    cough = False
    fever = False
    pain_score = 3
    notes = "No acute distress."
