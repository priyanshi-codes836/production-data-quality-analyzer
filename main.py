import yaml
import pandas as pd
from tabulate import tabulate
from engine import DataQualityEngine

def run_pipeline(data_path="production_orders.csv", config_path="rules.yaml"):
    print("\n" + "="*60)
    print("  PRODUCTION DATA QUALITY ANALYSER (DataShield)")
    print("="*60)

    # 1. Load Config
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    print(f"Loaded configuration for dataset: '{config['dataset_name']}'")

    # 2. Ingest Data
    df = pd.read_csv(data_path)
    print(f"Ingested {len(df)} records from {data_path}")

    # 3. Execute Engine
    engine = DataQualityEngine()
    run_id, results, quarantined_count = engine.execute_suite(df, config)

    # 4. Render Table
    table_data = []
    for r in results:
        table_data.append([
            r["column"],
            r["check_type"],
            r["status"],
            f"{r['failed_count']} ({r['failure_rate']}%)",
            r["details"]
        ])

    headers = ["Target Column", "Rule Type", "Status", "Violations", "Notes"]
    print("\n" + tabulate(table_data, headers=headers, tablefmt="fancy_grid"))

    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = total - passed
    print(f"\nAudit Logged to SQLite (Run ID: {run_id})")
    print(f"Summary: {passed}/{total} Passed | {failed}/{total} Failed\n")
    if quarantined_count > 0:
        print(f"Quarantined {quarantined_count} records into 'quarantined_records.csv'")

if __name__ == "__main__":
    run_pipeline()