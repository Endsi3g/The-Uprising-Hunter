from __future__ import annotations

import pytest

from scripts.utilities.ingest_compagnie_docs import (
    _has_suspicious_truncated_tail,
    _request_json_with_retries,
)


def test_has_suspicious_truncated_tail_detects_usage_marker() -> None:
    text = "IDENTITÉ VISUELLE\n• Usage: 50"
    assert _has_suspicious_truncated_tail(text) is True


def test_has_suspicious_truncated_tail_ignores_complete_line() -> None:
    text = "IDENTITÉ VISUELLE\n• Usage: 50% (backgrounds, textes sur clair)"
    assert _has_suspicious_truncated_tail(text) is False


def test_request_json_with_retries_retries_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, str]:
            return {"ok": "yes"}

    def fake_get(*args, **kwargs):  # type: ignore[no-untyped-def]
        calls["count"] += 1
        if calls["count"] < 3:
            raise RuntimeError("transient error")
        return FakeResponse()

    monkeypatch.setattr("scripts.utilities.ingest_compagnie_docs.requests.get", fake_get)
    monkeypatch.setattr("scripts.utilities.ingest_compagnie_docs.time.sleep", lambda *_: None)

    payload = _request_json_with_retries(
        url="https://example.com",
        headers={"X-Test": "1"},
        timeout=1,
        attempts=3,
        initial_delay_seconds=0.01,
    )

    assert payload == {"ok": "yes"}
    assert calls["count"] == 3

