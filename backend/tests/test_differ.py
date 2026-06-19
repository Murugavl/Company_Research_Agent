from agent.nodes import diff_plans

def test_diff_detects_change():
    old = {"overview": "old text", "risks": "none"}
    new = {"overview": "new text", "risks": "none"}
    diff = diff_plans(old, new)
    assert "overview" in diff
    assert diff["overview"]["old"] == "old text"
    assert diff["overview"]["new"] == "new text"
    assert "risks" not in diff

def test_diff_ignores_unchanged():
    old = {"overview": "same"}
    new = {"overview": "same"}
    diff = diff_plans(old, new)
    assert diff == {}

def test_diff_partial_change():
    old = {"overview": "o", "risks": "r"}
    new = {"overview": "o", "risks": "changed"}
    diff = diff_plans(old, new)
    assert len(diff) == 1
    assert "risks" in diff
    assert "overview" not in diff
