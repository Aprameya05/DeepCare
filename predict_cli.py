"""CLI: JSON stdin/file prediction against persisted model."""

from __future__ import annotations

import argparse
import json
import sys

from diabetes_prediction.inference import DiabetesPredictor, validate_medical_ranges


def main():
    parser = argparse.ArgumentParser(description="Diabetes prediction CLI")
    parser.add_argument("--json", dest="json_blob", default=None, help="Inline JSON object")
    parser.add_argument("--file", dest="json_file", default=None, help="Path to JSON file")
    args = parser.parse_args()

    raw = args.json_blob
    if args.json_file:
        raw = open(args.json_file, encoding="utf-8").read()
    if raw is None:
        raw = sys.stdin.read()

    payload = json.loads(raw)
    row, warnings = validate_medical_ranges(payload)
    pred = DiabetesPredictor().predict_row(row)
    print(
        json.dumps(
            {"prediction": pred, "warnings": warnings},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
