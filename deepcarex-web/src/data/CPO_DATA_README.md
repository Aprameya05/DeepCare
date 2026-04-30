# CPO Data Files

- `cpoQuestionnaire.json` defines the patient-facing intake questionnaire for the CPO test recommendation flow.
- `cpoClinicalCases.json` defines rule-like condition patterns and mapped diagnostic test suggestions.
- These files are data-only configuration artifacts for constrained-scope clinical decision support.
- All case logic and test mappings are placeholders for prototyping and require formal clinician validation.
- **Disclaimer:** no entry here is suitable for production clinical use without medical governance review.
- Keep `feature_key` values synchronized across both files at all times.
- If a questionnaire `feature_key` changes, update every matching case rule immediately.
- If a new condition is added, ensure required/supporting features reference existing questionnaire keys only.
- Maintain conservative confidence thresholds and keep rationale lines short and clinically interpretable.
