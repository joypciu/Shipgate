from pathlib import Path

from fastapi.testclient import TestClient

from shipgate.app import SAMPLE_DIFF, create_app


def test_home_page_reviews_a_pasted_diff(monkeypatch, tmp_path):
    monkeypatch.setenv("DECISION_BENCH_ROOT", str(Path(__file__).resolve().parents[2] / "decision-bench"))
    monkeypatch.setenv("SHIPGATE_DATA", str(tmp_path))
    monkeypatch.delenv("GITHUB_APP_ID", raising=False)
    app = create_app()
    client = TestClient(app)
    home = client.get("/")
    assert home.status_code == 200
    assert "Paste a diff" in home.text
    assert "GitHub app not set" in home.text
    result = client.post("/reviews", data={"diff": SAMPLE_DIFF})
    assert result.status_code == 200
    assert "block" in result.text
    assert "auth.py" in result.text
    assert "Comment on line" in result.text
    empty = client.post("/reviews", data={"diff": "   "})
    assert empty.status_code == 400
