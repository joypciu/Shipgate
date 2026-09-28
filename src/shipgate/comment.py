from __future__ import annotations

from shipgate.review import Review


def format_comment(review: Review) -> str:
    lines = [f"**{review.verdict}**", "", review.summary.strip() or "No summary.", ""]
    if review.risks:
        for risk in review.risks:
            lines.append(f"- **{risk.severity}** `{risk.file}` — {risk.reason}")
    else:
        lines.append("No file-level risks.")
    lines.append("")
    lines.append(f"Decision Bench run `{review.run_id}`.")
    return "\n".join(lines)
