"""Delete the stale pending recommendations so they can be re-generated with fixed scorer code."""
import sqlite3
from pathlib import Path

DB = Path(__file__).parents[1] / "enterprise_ai_companion.db"
conn = sqlite3.connect(DB)
cur = conn.execute(
    "DELETE FROM file_placement_recommendations "
    "WHERE status = 'pending' AND source_path LIKE '%OneDrive_1_14-8-2026%'"
)
conn.commit()
print(f"Deleted {cur.rowcount} pending record(s).")
conn.close()
