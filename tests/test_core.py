from vehicle_safety.detection import DrowsinessAnalyzer, DrowsinessResult
from vehicle_safety.risk import assess_risk
from vehicle_safety.parking import ParkingSlot, summarize_parking
from vehicle_safety.routing import recommend_route, route_cost
from vehicle_safety.simulation import DEMO_SCENARIOS, SCENARIOS, generate_snapshot
from vehicle_safety.traffic import Road, analyze_traffic, traffic_score
from vehicle_safety.vehicle_health import assess_vehicle_health
from vehicle_safety.emergency import detect_potential_accident


def test_overspeed_increases_risk():
    sensor = generate_snapshot(seed=1, scenario="OVERSPEED")
    result = assess_risk(sensor, DrowsinessResult("ALERT", 0.1, 1, 2, ""))
    assert sensor.speed_kmh > sensor.speed_limit_kmh
    assert result.score > 0
    assert "Overspeed detected" in result.factors


def test_impact_is_critical():
    sensor = generate_snapshot(seed=1, scenario="CRITICAL_COMBINATION")
    result = assess_risk(sensor, DrowsinessResult("ALERT", 0.1, 1, 2, ""))
    assert result.emergency is True
    assert result.level == "CRITICAL"
    assert result.score >= 90


def test_health_warning_has_health_factors():
    sensor = generate_snapshot(seed=1, scenario="VEHICLE_HEALTH_WARNING")
    result = assess_risk(sensor, DrowsinessResult("ALERT", 0.1, 1, 2, ""))
    assert "Vehicle health warning" in result.factors


def test_all_demo_scenarios_are_supported():
    assert set(SCENARIOS) == {
        "SAFE_DRIVING", "DROWSY_DRIVER", "OVERSPEED", "DROWSY_AND_OVERSPEED",
        "VEHICLE_HEALTH_WARNING", "POTENTIAL_ACCIDENT", "CRITICAL_COMBINATION",
    }
    for scenario in SCENARIOS:
        snapshot = generate_snapshot(seed=5, scenario=scenario)
        assert 0 <= snapshot.impact_g < 10


def _demo_driver(scenario):
    return DrowsinessResult(
        "DROWSY" if scenario in {"DROWSY_DRIVER", "DROWSY_AND_OVERSPEED", "CRITICAL_COMBINATION"} else "ALERT",
        90.0 if scenario in {"DROWSY_DRIVER", "DROWSY_AND_OVERSPEED", "CRITICAL_COMBINATION"} else 0.0,
        1, 0, "",
    )


def test_combination_rules_and_result_contract():
    safe = assess_risk(generate_snapshot(3, "SAFE_DRIVING"), _demo_driver("SAFE_DRIVING"))
    combined = assess_risk(generate_snapshot(3, "DROWSY_AND_OVERSPEED"), _demo_driver("DROWSY_AND_OVERSPEED"))
    critical = assess_risk(generate_snapshot(3, "CRITICAL_COMBINATION"), _demo_driver("CRITICAL_COMBINATION"))
    assert safe.risk_level == "SAFE"
    assert combined.risk_score > 50
    assert "Drowsiness + overspeed combination" in combined.contributing_factors
    assert critical.risk_level == "CRITICAL"
    assert critical.emergency_status == "EMERGENCY"
    assert critical.recommended_action
    assert "drowsiness and overspeed" in combined.explanation.lower()


def test_drowsiness_requires_prolonged_closure():
    analyzer = DrowsinessAnalyzer()

    class Point:
        def __init__(self, x, y):
            self.x, self.y = x, y

    class FakeLandmarker:
        def __init__(self):
            self.closed = False

        def detect_for_video(self, _image, _timestamp):
            points = [Point(0.5, 0.5) for _ in range(478)]
            for index in (33, 133, 362, 263):
                points[index] = Point(0.0, 0.0) if index in (33, 362) else Point(1.0, 0.0)
            eye_gap = 0.01 if self.closed else 0.05
            for index in (159, 386):
                points[index] = Point(0.5, 0.5 - eye_gap / 2)
            for index in (145, 374):
                points[index] = Point(0.5, 0.5 + eye_gap / 2)
            points[13], points[14] = Point(0.5, 0.5), Point(0.5, 0.55)
            points[61], points[291] = Point(0.0, 0.5), Point(1.0, 0.5)
            return type("Result", (), {"face_landmarks": [points]})()

    fake = FakeLandmarker()
    analyzer._landmarker = fake
    frame = __import__("numpy").zeros((20, 20, 3), dtype="uint8")
    assert analyzer.process(frame, 0).status == "ALERT"
    fake.closed = True
    assert analyzer.process(frame, 500).status == "ALERT"  # blink/short closure
    assert analyzer.process(frame, 2100).status == "DROWSY"
    analyzer.close()


def test_parking_availability_and_nearest_slot():
    slots = [
        ParkingSlot("A", True, 10, 0.9),
        ParkingSlot("B", False, 35, 0.9),
        ParkingSlot("C", False, 18, 0.9),
    ]
    summary = summarize_parking(slots)
    assert summary.available_slots == 2
    assert summary.occupied_slots == 1
    assert summary.nearest_available.slot_id == "C"


def test_traffic_classification():
    assert traffic_score("LOW") < traffic_score("MEDIUM") < traffic_score("HIGH")
    assert analyze_traffic([Road("A", 3, "HIGH", 20)]).level == "HIGH"
    assert analyze_traffic([Road("A", 3, "LOW", 8)]).level == "LOW"


def test_route_cost_and_recommendation():
    short_busy = Road("Short busy", 4, "HIGH", 24)
    longer_clear = Road("Long clear", 6.5, "LOW", 13)
    assert route_cost(longer_clear) < route_cost(short_busy)
    recommendation = recommend_route([short_busy, longer_clear])
    assert recommendation.road.road_name == "Long clear"
    assert "Lowest transparent route cost" in recommendation.reason


def test_vehicle_health_normal_warning_and_critical():
    normal = assess_vehicle_health(90, 13.8, 0.3, 30)
    warning = assess_vehicle_health(110, 12.1, 1.5, 90)
    critical = assess_vehicle_health(125, 11.5, 2.2, 100)
    assert normal.health_status == "NORMAL"
    assert warning.health_status == "WARNING"
    assert "High temperature" in warning.detected_issues
    assert critical.health_status == "CRITICAL"
    assert 0 <= critical.health_score <= 100


def test_accident_requires_impact_and_corrobation():
    clear = detect_potential_accident(20, 50, 0.2, False)
    accident = detect_potential_accident(85, 45, 1.8, True)
    assert clear.emergency_status != "POTENTIAL ACCIDENT"
    assert accident.emergency_status == "POTENTIAL ACCIDENT"
    assert accident.recommended_action


def test_health_and_emergency_integrate_into_risk():
    snapshot = generate_snapshot(4, "POTENTIAL_ACCIDENT")
    health = assess_vehicle_health(snapshot.engine_temp_c, snapshot.voltage_v, snapshot.vibration_g, snapshot.current_a)
    emergency = detect_potential_accident(90, 45, 1.8, True)
    result = assess_risk(snapshot, DrowsinessResult("DROWSY", 90, 1, 0, ""), health=health, emergency=emergency)
    assert result.emergency_status == "EMERGENCY"
    assert result.risk_score >= 90


def test_unified_demo_scenarios_are_coherent():
    assert len(DEMO_SCENARIOS) == 9
    normal = generate_snapshot(10, "NORMAL_DRIVING")
    heavy = generate_snapshot(10, "HEAVY_TRAFFIC")
    health = generate_snapshot(10, "VEHICLE_HEALTH_WARNING")
    accident = generate_snapshot(10, "POTENTIAL_ACCIDENT")
    assert normal.traffic_level == "LIGHT"
    assert heavy.traffic_level == "HEAVY"
    assert health.driver_vehicle_status == "ABNORMAL"
    assert accident.sudden_speed_change_kmh > 0 and accident.vehicle_stopped_after_event


def test_risk_progression_and_single_input_change():
    normal_sensor = generate_snapshot(20, "NORMAL_DRIVING")
    driver = DrowsinessResult("ALERT", 0, 1, 2, "")
    normal = assess_risk(normal_sensor, driver)
    warning = assess_risk(generate_snapshot(20, "HEAVY_TRAFFIC"), driver)
    high = assess_risk(generate_snapshot(20, "DROWSY_OVERSPEED"), DrowsinessResult("DROWSY", 90, 1, 0, ""))
    critical = assess_risk(generate_snapshot(20, "DROWSY_OVERSPEED_LANE_DEVIATION"), DrowsinessResult("DROWSY", 90, 1, 0, ""))
    emergency = assess_risk(generate_snapshot(20, "CRITICAL_EMERGENCY"), DrowsinessResult("DROWSY", 90, 1, 0, ""))
    assert normal.risk_level == "SAFE"
    assert warning.risk_score >= normal.risk_score
    assert high.risk_score >= warning.risk_score
    assert critical.risk_score >= high.risk_score
    assert emergency.emergency_status == "EMERGENCY"
    assert emergency.risk_score >= critical.risk_score


def test_invalid_health_inputs_are_clamped_without_crashing():
    result = assess_vehicle_health(-50, 100, 0, -10)
    assert result.health_status == "NORMAL"
    assert 0 <= result.health_score <= 100

