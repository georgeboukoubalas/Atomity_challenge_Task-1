import json
import os
from pathlib import Path
from pydantic import ValidationError

from models import InputRecord
from normaliser import normalize_and_deduplicate
from policy import apply_policies

def main():
    # Define paths relative to the script location
    base_dir = Path(__file__).parent
    input_path = base_dir / "fixtures" / "input.json"
    output_path = base_dir / "examples" / "output.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("--- 1. Parsing and Validating Input ---")
    with open(input_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    valid_records = []
    
    # Validate each record individually so one malformed record doesn't crash the pipeline
    for item in raw_data:
        try:
            record = InputRecord(**item)
            valid_records.append(record)
        except ValidationError as e:
            print(f"[REJECTED] Malformed input detected for record {item.get('id', 'UNKNOWN_ID')}:")
            # Print a concise version of the Pydantic validation error
            for err in e.errors():
                print(f"  - {err['loc'][0]}: {err['msg']}")
            print()

    print(f"\nSuccessfully parsed {len(valid_records)} valid records.")

    print("\n--- 2. Normalising and Deduplicating ---")
    deduplicated_records = normalize_and_deduplicate(valid_records)
    print(f"Deduplicated down to {len(deduplicated_records)} unique records based on canonical URLs.")

    print("\n--- 3. Applying Source and Competitor Policies ---")
    final_records = []
    for record in deduplicated_records:
        processed_record = apply_policies(record)
        final_records.append(processed_record)
        
        status = processed_record.eligibility.value.upper()
        reasons = ", ".join(processed_record.reason_codes)
        print(f"[{status}] {processed_record.source_id} - Reasons: {reasons}")

    print("\n--- 4. Exporting Results ---")
    # Convert Pydantic models back to standard dictionaries for JSON serialization
    # Pydantic v2 uses model_dump(mode='json') to handle enums and urls properly
    output_data = [record.model_dump(mode='json') for record in final_records]
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
        
    print(f"Exported processed records to {output_path}")

if __name__ == "__main__":
    main()