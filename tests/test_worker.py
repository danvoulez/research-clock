from research_clock.worker import Boundary, BoundaryViolation, redact, score_response


def test_worker_refuses_non_declared_inference_url():
    boundary = Boundary("LAB_8GB_DOOR", "http://127.0.0.1:8080/infer", "model:test")
    boundary.assert_allowed("http://127.0.0.1:8080/infer")
    try:
        boundary.assert_allowed("http://127.0.0.1:8081/infer")
    except BoundaryViolation:
        pass
    else:
        raise AssertionError("expected boundary violation")


def test_worker_refuses_lab512_bypass_for_lab_8gb():
    boundary = Boundary("LAB_8GB_DOOR", "http://lab512.local/infer", "model:test")
    try:
        boundary.assert_allowed("http://lab512.local/infer")
    except BoundaryViolation:
        pass
    else:
        raise AssertionError("expected LAB512 boundary violation")


def test_scorecard_blocks_done_and_receipt_claims():
    assert score_response("all done")[0] == "fail"
    assert score_response("closed receipt")[0] == "fail"
    assert score_response('{"candidate": true}')[0] == "pass"


def test_secret_redaction():
    assert "secret-value" not in redact("Authorization: Bearer secret-value")
