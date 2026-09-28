from pathlib import Path

from shipgate.review import Reviewer


AUTH = """diff --git a/auth.py b/auth.py
--- a/auth.py
+++ b/auth.py
@@ -4,7 +4,7 @@ def allow(user):
-    if user.is_authenticated:
+    if True:  # bypass auth
         return True
     return False
"""


def test_demo_change_lead_blocks_an_auth_bypass(tmp_path: Path):
    reviewer = Reviewer.open(
        bench_root=Path(r"E:\decision-bench"),
        database=tmp_path / "decision_bench.sqlite",
    )
    review = reviewer.review(AUTH)
    assert review.status == "succeeded"
    assert review.verdict == "block"
    assert review.risks[0].file == "auth.py"
    assert review.risks[0].severity == "high"
