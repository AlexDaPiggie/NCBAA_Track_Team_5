"""Build the checked-in deterministic demo CSV files."""

from pathlib import Path

from data_generation.synthetic import write_demo_dataset


if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / "data" / "processed"
    write_demo_dataset(target)
    print(f"Wrote demo dataset to {target}")
