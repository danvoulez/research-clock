from pathlib import Path


def test_dispatcher_module_does_not_import_inference_or_worker():
    source = Path("research_clock/dispatcher.py").read_text(encoding="utf-8")
    forbidden = ["urlopen", "Request", "worker", "mistral", "lab512"]
    lowered = source.lower()
    assert not any(term in lowered for term in forbidden)
