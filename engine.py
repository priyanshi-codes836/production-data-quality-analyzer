import sqlite3
import re
from datetime import datetime
import pandas as pd

class DataQualityEngine:
    def __init__(self, db_path="quality_metrics.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Creates the audit logging tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    dataset_name TEXT,
                    total_rules INTEGER,
                    passed_rules INTEGER,
                    failed_rules INTEGER
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS check_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    column_name TEXT,
                    check_type TEXT,
                    status TEXT,
                    failed_count INTEGER,
                    failure_rate REAL,
                    details TEXT
                )
            """)
            conn.commit()

    def run_check(self, df: pd.DataFrame, rule: dict) -> dict:
        col = rule["column"]
        check_type = rule["type"]
        total_rows = len(df)

        if col not in df.columns:
            return {
                "column": col,
                "check_type": check_type,
                "status": "FAIL",
                "failed_count": total_rows,
                "failure_rate": 100.0,
                "details": f"Column '{col}' not found in dataset"
            }

        series = df[col]
        failed_count = 0
        details = "Passed"

        if check_type == "not_null":
            failed_count = int(series.isnull().sum())
            if failed_count > 0:
                details = f"Found {failed_count} missing values"

        elif check_type == "unique":
            failed_count = int(series.duplicated().sum())
            if failed_count > 0:
                details = f"Found {failed_count} duplicate values"

        elif check_type == "range":
            min_val = rule.get("min", float("-inf"))
            max_val = rule.get("max", float("inf"))
            invalid_mask = (series < min_val) | (series > max_val) | series.isnull()
            failed_count = int(invalid_mask.sum())
            if failed_count > 0:
                details = f"Values out of bounds [{min_val}, {max_val}]"

        elif check_type == "allowed_values":
            allowed = set(rule.get("allowed", []))
            invalid_mask = ~series.isin(allowed)
            failed_count = int(invalid_mask.sum())
            if failed_count > 0:
                details = f"Values not in allowed categorical set"

        elif check_type == "regex":
            pattern = re.compile(rule.get("pattern", ".*"))
            invalid_mask = ~series.astype(str).str.match(pattern)
            failed_count = int(invalid_mask.sum())
            if failed_count > 0:
                details = f"Values failed regex pattern validation"

        status = "FAIL" if failed_count > 0 else "PASS"
        failure_rate = round((failed_count / total_rows) * 100, 2)

        return {
            "column": col,
            "check_type": check_type,
            "status": status,
            "failed_count": failed_count,
            "failure_rate": failure_rate,
            "details": details
        }

    def execute_suite(self, df: pd.DataFrame, config: dict):
        dataset_name = config.get("dataset_name", "unnamed_dataset")
        rules = config.get("rules", [])
        
        results = []
        quarantine_indices = set()

        for rule in rules:
            col = rule["column"]
            check_type = rule["type"]
            total_rows = len(df)

            if col not in df.columns:
                results.append({
                    "column": col, "check_type": check_type, "status": "FAIL",
                    "failed_count": total_rows, "failure_rate": 100.0,
                    "details": f"Column '{col}' not found"
                })
                continue

            series = df[col]
            failed_mask = pd.Series(False, index=df.index)

            if check_type == "not_null":
                failed_mask = series.isnull()
            elif check_type == "unique":
                failed_mask = series.duplicated(keep=False)
            elif check_type == "range":
                min_v = rule.get("min", float("-inf"))
                max_v = rule.get("max", float("inf"))
                failed_mask = (series < min_v) | (series > max_v) | series.isnull()
            elif check_type == "allowed_values":
                allowed = set(rule.get("allowed", []))
                failed_mask = ~series.isin(allowed)
            elif check_type == "regex":
                pat = re.compile(rule.get("pattern", ".*"))
                failed_mask = ~series.astype(str).str.match(pat)

            failed_count = int(failed_mask.sum())
            if failed_count > 0:
                quarantine_indices.update(df[failed_mask].index.tolist())

            status = "FAIL" if failed_count > 0 else "PASS"
            failure_rate = round((failed_count / total_rows) * 100, 2)
            results.append({
                "column": col,
                "check_type": check_type,
                "status": status,
                "failed_count": failed_count,
                "failure_rate": failure_rate,
                "details": f"Violations: {failed_count}" if failed_count > 0 else "Passed"
            })

        # Save quarantined records
        if quarantine_indices:
            quarantined_df = df.loc[list(quarantine_indices)]
            quarantined_df.to_csv("quarantined_records.csv", index=False)

        passed = sum(1 for r in results if r["status"] == "PASS")
        failed = sum(1 for r in results if r["status"] == "FAIL")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO runs (timestamp, dataset_name, total_rules, passed_rules, failed_rules)
                VALUES (?, ?, ?, ?, ?)
            """, (datetime.utcnow().isoformat(), dataset_name, len(rules), passed, failed))
            run_id = cursor.lastrowid

            for r in results:
                cursor.execute("""
                    INSERT INTO check_results (run_id, column_name, check_type, status, failed_count, failure_rate, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (run_id, r["column"], r["check_type"], r["status"], r["failed_count"], r["failure_rate"], r["details"]))
            conn.commit()

        return run_id, results, len(quarantine_indices)
