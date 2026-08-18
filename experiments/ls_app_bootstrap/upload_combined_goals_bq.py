#!/usr/bin/env python3
"""Load combined_goals.csv to a BigQuery *draft* table.

Does not touch analytics.stg_* / Looker production.
Default: analytics_team.combined_goals_draft (replace).

  python experiments/ls_app_bootstrap/upload_combined_goals_bq.py
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pandas_gbq

HERE = Path(__file__).resolve().parent
MG_ROOT = HERE.parents[1]
PROJECT_ROOT = MG_ROOT.parent
CREDS = PROJECT_ROOT / "oceanic-citadel-454608-d2-e116e15558ce.json"

CSV = (
    MG_ROOT
    / "runs"
    / "2026-08-03_rp_ls_winsor_esc_ls_app_110733"
    / "combined_goals.csv"
)
PROJECT = "oceanic-citadel-454608-d2"
DATASET = "analytics_team"
TABLE = "combined_goals_draft"
AS_OF = "2026-08-03"
RUN_TAG = "2026-08-03_rp_ls_winsor_esc_ls_app_110733"
ENGINE = "v2 winsor_esc + lonestar/App native_early_rp_tail"
MAIN_COLS = [
    "brand",
    "population",
    "goal_horizon",
    "day",
    "raw_goal_ratio",
    "organic_share",
    "adjusted_goal_ratio",
]


def main() -> int:
    if CREDS.is_file():
        os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", str(CREDS))
    if not CSV.is_file():
        raise FileNotFoundError(CSV)

    df = pd.read_csv(CSV)
    missing = [c for c in MAIN_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"combined_goals missing columns: {missing}")

    out = df[MAIN_COLS].copy()
    out["goal_horizon"] = out["goal_horizon"].astype("int64")
    out["day"] = out["day"].astype("int64")
    out["as_of_date"] = pd.Timestamp(AS_OF).date()
    out["run_tag"] = RUN_TAG
    out["engine"] = ENGINE
    out["provisional"] = True
    out["loaded_at"] = datetime.now(timezone.utc)

    dest = f"{DATASET}.{TABLE}"
    pandas_gbq.to_gbq(
        out,
        dest,
        project_id=PROJECT,
        if_exists="replace",
        progress_bar=False,
    )
    print(f"wrote {len(out):,} rows → {PROJECT}.{dest}")
    print("draft only — not analytics.stg_* production")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
