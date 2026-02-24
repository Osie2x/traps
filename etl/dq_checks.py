"""Step 4: Data quality checks on transformed data."""

import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import REPORTS_DIR
from etl.transform import transform


def run_dq_checks(tables: dict | None = None) -> dict:
    """Run data quality checks; return summary dict and write reports."""
    if tables is None:
        tables = transform()

    issues = []
    fp = tables["fact_pitch"]
    bridge = tables["bridge_pitch_shark"]

    # 1. Uniqueness
    dup_pitches = fp["pitch_id"].duplicated().sum()
    if dup_pitches > 0:
        issues.append({"check": "uniqueness", "table": "fact_pitch", "detail": f"{dup_pitches} duplicate pitch_ids"})

    # 2. Completeness
    for col in ["asked_amount", "asked_equity"]:
        null_count = fp[col].isna().sum()
        if null_count > 0:
            issues.append({"check": "completeness", "table": "fact_pitch", "detail": f"{null_count} nulls in {col}"})

    # 3. Valid ranges
    bad_equity = ((fp["asked_equity"] < 0) | (fp["asked_equity"] > 1)).sum()
    if bad_equity > 0:
        issues.append({"check": "range", "table": "fact_pitch", "detail": f"{bad_equity} asked_equity outside [0,1]"})

    bad_amount = (fp["asked_amount"] <= 0).sum()
    if bad_amount > 0:
        issues.append({"check": "range", "table": "fact_pitch", "detail": f"{bad_amount} asked_amount <= 0"})

    # 4. Consistency: no deal → null deal terms
    no_deal = fp[fp["deal_made"] == 0]
    inconsistent = no_deal[no_deal["deal_amount"].notna() | no_deal["deal_equity"].notna()]
    if len(inconsistent) > 0:
        issues.append({
            "check": "consistency",
            "table": "fact_pitch",
            "detail": f"{len(inconsistent)} rows have deal_made=0 but non-null deal terms",
        })

    # 5. Outlier report: top 1% valuations
    valuations = fp["valuation_asked"].dropna()
    if len(valuations) > 0:
        p99 = valuations.quantile(0.99)
        outliers = fp[fp["valuation_asked"] > p99]
        if len(outliers) > 0:
            issues.append({
                "check": "outlier",
                "table": "fact_pitch",
                "detail": f"{len(outliers)} valuations above 99th percentile (>{p99:,.0f})",
            })

    # Summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_pitches": len(fp),
        "total_bridge_rows": len(bridge),
        "issues_found": len(issues),
        "issues": issues,
    }

    # Write issue CSV
    if issues:
        pd.DataFrame(issues).to_csv(os.path.join(REPORTS_DIR, "dq_issues.csv"), index=False)

    # Write HTML report
    _write_html_report(summary, tables)

    return summary


def _write_html_report(summary: dict, tables: dict):
    """Write a simple HTML data quality report."""
    fp = tables["fact_pitch"]
    html_parts = [
        "<html><head><title>SharkGraph DQ Report</title>",
        "<style>body{font-family:sans-serif;margin:2em}table{border-collapse:collapse;margin:1em 0}",
        "th,td{border:1px solid #ccc;padding:6px 12px;text-align:left}th{background:#f0f0f0}</style></head>",
        "<body>",
        f"<h1>SharkGraph Data Quality Report</h1>",
        f"<p>Generated: {summary['timestamp']}</p>",
        f"<p>Total pitches: {summary['total_pitches']} | Bridge rows: {summary['total_bridge_rows']}</p>",
        f"<h2>Issues Found: {summary['issues_found']}</h2>",
    ]

    if summary["issues"]:
        html_parts.append("<table><tr><th>Check</th><th>Table</th><th>Detail</th></tr>")
        for issue in summary["issues"]:
            html_parts.append(
                f"<tr><td>{issue['check']}</td><td>{issue['table']}</td><td>{issue['detail']}</td></tr>"
            )
        html_parts.append("</table>")
    else:
        html_parts.append("<p style='color:green'>All checks passed.</p>")

    # Quick stats
    html_parts.append("<h2>Quick Stats</h2><table>")
    html_parts.append(f"<tr><td>Deal rate</td><td>{fp['deal_made'].mean():.1%}</td></tr>")
    html_parts.append(f"<tr><td>Avg asked amount</td><td>${fp['asked_amount'].mean():,.0f}</td></tr>")
    html_parts.append(f"<tr><td>Avg asked equity</td><td>{fp['asked_equity'].mean():.1%}</td></tr>")
    val = fp["valuation_asked"].dropna()
    if len(val) > 0:
        html_parts.append(f"<tr><td>Median valuation asked</td><td>${val.median():,.0f}</td></tr>")
    html_parts.append("</table></body></html>")

    with open(os.path.join(REPORTS_DIR, "data_quality_report.html"), "w") as f:
        f.write("\n".join(html_parts))

    print(f"DQ report written to {REPORTS_DIR}/data_quality_report.html")


if __name__ == "__main__":
    summary = run_dq_checks()
    print(f"Issues found: {summary['issues_found']}")
    for issue in summary["issues"]:
        print(f"  [{issue['check']}] {issue['table']}: {issue['detail']}")
