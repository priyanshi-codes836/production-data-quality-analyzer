## DataShield — Production Data Quality Analyser

DataShield is an automated data quality and validation engine built with Python and Pandas. It enforces declarative schema contracts on incoming production datasets, isolates anomalous records into quarantine storage, and maintains an auditable execution history in an SQLite database.

---

## 📌 Architecture

Incoming Raw Data (CSV) ──┐
├──► [ DataQualityEngine ] ──► Quarantined Records (quarantined_records.csv)
Declarative Rules (YAML) ─┘             │
└──► SQLite Audit Store (quality_metrics.db)
└──► Formatted Executive CLI Summary


---

## 🚀 Key Features

* **Declarative Configuration:** Rules are decoupled from execution logic using standard `YAML` definitions.
* **Vectorized Evaluation:** High-performance validation routines powered by `pandas`:
  * **Completeness:** Detects missing/null fields (`not_null`).
  * **Uniqueness:** Flags duplicated primary or composite keys (`unique`).
  * **Range Boundaries:** Enforces boundary conditions on numerical fields (`range`).
  * **Categorical Integrity:** Restricts categorical entries to authorized sets (`allowed_values`).
  * **Conformity & Pattern Safety:** Validates regex formatting for strings (`regex`).
* **Automated Data Quarantine:** Violating records are isolated into a `quarantined_records.csv` file to protect downstream consumers.
* **Audit Persistence:** Execution metadata, violation percentages, and check statuses are logged into `quality_metrics.db` for lineage and observability.

---

## 📂 Project Structure

data-quality-analyser/
├── rules.yaml                  # Declarative quality constraints
├── engine.py                   # Core validation engine & SQLite persistence
├── main.py                     # CLI pipeline runner
├── generate_data.py            # Test data generator (dirty and clean sets)
├── production_orders.csv       # Test dataset with intentional anomalies
├── clean_production_orders.csv # Clean test baseline dataset
├── quality_metrics.db          # SQLite run audit history
├── quarantined_records.csv     # Isolated invalid records
├── requirements.txt            # Project dependencies
└── README.md                   # Project documentation


---

## 🛠️ Setup & Execution

### 1. Clone the Repository
```bash
git clone [https://github.com/priyanshi-codes836/production-data-quality-analyzer.git](https://github.com/priyanshi-codes836/production-data-quality-analyzer.git)
cd production-data-quality-analyzer
2. Set Up Virtual Environment & Dependencies
Bash
python -m venv venv

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# On macOS/Linux:
source venv/bin/activate

# Install required packages:
pip install pandas pyyaml tabulate
3. Generate Test Datasets
Bash
python generate_data.py
4. Run the Pipeline on Dirty Data
Bash
python main.py
5. Verify the Pipeline with Clean Data
Bash
python -c "from main import run_pipeline; run_pipeline(data_path='clean_production_orders.csv')"
📊 Sample Execution Output
Plaintext
============================================================
  PRODUCTION DATA QUALITY ANALYSER (DataShield)
============================================================
Loaded configuration for dataset: 'production_orders'
Ingested 7 records from production_orders.csv

+-----------------+----------------+----------+--------------+---------------------------------------+
| Target Column   | Rule Type      | Status   | Violations   | Notes                                 |
+=================+================+==========+==============+=======================================+
| order_id        | unique         | FAIL     | 1 (14.29%)   | Found 1 duplicate values              |
+-----------------+----------------+----------+--------------+---------------------------------------+
| customer_id     | not_null       | FAIL     | 1 (14.29%)   | Found 1 missing values                |
+-----------------+----------------+----------+--------------+---------------------------------------+
| amount          | range          | FAIL     | 2 (28.57%)   | Values out of bounds [0.01, 10000.0]  |
+-----------------+----------------+----------+--------------+---------------------------------------+
| status          | allowed_values | FAIL     | 1 (14.29%)   | Values not in allowed categorical set |
+-----------------+----------------+----------+--------------+---------------------------------------+
| email           | regex          | FAIL     | 1 (14.29%)   | Values failed regex pattern validation|
+-----------------+----------------+----------+--------------+---------------------------------------+

Audit Logged to SQLite (Run ID: 1)
Summary: 0/5 Passed | 5/5 Failed
Quarantined 4 corrupt records into 'quarantined_records.csv'

##🗄️ Database Audit Schema
The embedded SQLite datastore (quality_metrics.db) tracks run lineage across two relational tables:

runs: Captures top-level run metadata (run_id, timestamp, dataset_name, total_rules, passed_rules, failed_rules).

check_results: Logs granular check execution records (id, run_id, column_name, check_type, status, failed_count, failure_rate, details).

