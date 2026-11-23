"""Unit tests for crop-aware post-processing of raw model detections."""
from app.core.crops import get_crop
from app.services.detection_rules import RawDetection, evaluate_detections


def _det(label: str, conf: float) -> RawDetection:
    return RawDetection(label=label, confidence=conf, x1=1, y1=2, x2=30, y2=40)


def test_no_detections_means_healthy():
    outcome = evaluate_detections([], get_crop("tea"))
    assert outcome.status == "no_detection"
    assert outcome.detections == ()
    assert outcome.healthy_confidence is None


def test_disease_above_threshold_is_reported_with_mapped_label():
    durian = get_crop("durian")
    outcome = evaluate_detections([_det("Leaf_Phytophthora", 0.9)], durian)
    assert outcome.status == "detected"
    assert len(outcome.detections) == 1
    assert outcome.detections[0]["class_name"] == durian.map_label("Leaf_Phytophthora")
    assert outcome.detections[0]["confidence"] == 0.9


def test_disease_below_threshold_is_dropped():
    tea = get_crop("tea")
    outcome = evaluate_detections([_det("Helopeltis", 0.01)], tea)
    assert outcome.status == "no_detection"
    assert outcome.detections == ()


def test_healthy_only_reports_healthy_confidence():
    outcome = evaluate_detections([_det("Healthy", 0.8)], get_crop("tea"))
    assert outcome.status == "no_detection"
    assert outcome.healthy_confidence == 0.8
    assert outcome.unclear_disease_suppressed is False


def test_healthy_below_its_threshold_is_ignored():
    outcome = evaluate_detections([_det("Healthy", 0.1)], get_crop("tea"))
    assert outcome.healthy_confidence is None


def test_dominant_healthy_suppresses_faint_disease():
    outcome = evaluate_detections(
        [_det("Healthy", 0.7), _det("Brown Blight", 0.4)], get_crop("tea")
    )
    assert outcome.status == "no_detection"
    assert outcome.unclear_disease_suppressed is True


def test_strong_disease_wins_over_weaker_healthy():
    outcome = evaluate_detections(
        [_det("Healthy", 0.4), _det("Brown Blight", 0.9)], get_crop("tea")
    )
    assert outcome.status == "detected"
    assert outcome.healthy_confidence == 0.4


def test_coordinates_are_rounded():
    raw = RawDetection(label="Brown Blight", confidence=0.876543, x1=1.234567, y1=2.0, x2=3.0, y2=4.0)
    outcome = evaluate_detections([raw], get_crop("tea"))
    det = outcome.detections[0]
    assert det["x1"] == 1.23
    assert det["confidence"] == 0.8765
