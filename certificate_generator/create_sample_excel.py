"""
Helper script to generate a sample Excel file for testing.
Run from the project root:  python -m certificate_generator.create_sample_excel
"""
from pathlib import Path

import pandas as pd

data = {
    "Name": ["Rahul Sharma", "Priya Patel", "Arun Kumar", "Sneha Reddy", "Vikram Singh"],
    "Email": [
        "rahul@example.com",
        "priya@example.com",
        "arun@example.com",
        "sneha@example.com",
        "vikram@example.com",
    ],
    "Send": ["Yes", "Yes", "No", "Yes", "No"],
    "Duration": [
        "22–24 July 2026",
        "22–24 July 2026",
        "22–24 July 2026",
        "22–24 July 2026",
        "22–24 July 2026",
    ],
}

df = pd.DataFrame(data)
output_path = Path(__file__).resolve().parent.parent / "inputs" / "sample_students.xlsx"
output_path.parent.mkdir(parents=True, exist_ok=True)
df.to_excel(output_path, index=False)
print(f"Sample workbook created: {output_path}")
