from dataclasses import dataclass

from .config import DEFAULT_CONFIG, SafetyConfig
from .detection import DrowsinessResult
from .emergency import EmergencyAssessment, detect_potential_accident
from .simulation import SensorSnapshot
from .vehicle_health import VehicleHealthAssessment, assess_vehicle_health


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def _scale(value: float, low: float, high: float) -> float:
    return _clamp((value - low) / (high - low) * 100)


@dataclass(frozen=True)
class RiskAssessment:
    risk_score: int
    risk_level: str
    contributing_factors: list[str]
    recommended_action: str
    emergency_status: str
    component_scores: dict[str, int]
    explanation: str

    @property
    def score(self) -> int:
        return self.risk_score

    @property
    def level(self) -> str:
        return self.risk_level

    @property
    def factors(self) -> list[str]:
        return self.contributing_factors

    @property
    def emergency(self) -> bool:
        return self.emergency_status == "EMERGENCY"


def assess_risk(
    sensor: SensorSnapshot,
    drowsiness: DrowsinessResult,
    config: SafetyConfig = DEFAULT_CONFIG,
    health: VehicleHealthAssessment | None = None,
    emergency: EmergencyAssessment | None = None,
) -> RiskAssessment:
    """Combine driver, vehicle and emergency signals with explainable escalation."""
    health = health or assess_vehicle_health(
        sensor.engine_temp_c, sensor.voltage_v, sensor.vibration_g, sensor.current_a, config
    )
    emergency = emergency or detect_potential_accident(
        _scale(sensor.impact_g, 0, config.emergency_impact_g),
        sensor.sudden_speed_change_kmh,
        sensor.vibration_g,
        sensor.vehicle_stopped_after_event,
        config,
    )
    drowsy_score = _clamp(drowsiness.score * 100 if drowsiness.score <= 1 else drowsiness.score)
    if drowsiness.status not in {"DROWSY", "ATTENTION"}:
        drowsy_score = 0
    closure_score = _scale(drowsiness.eyes_closed_seconds, 0, max(config.drowsiness_closure_seconds, 0.1))
    speed_score = _scale(sensor.speed_kmh - sensor.speed_limit_kmh, 0, 60)
    traffic_score = {"LIGHT": 0, "MODERATE": 50, "HEAVY": 100}.get(sensor.traffic_level.upper(), 0)
    lane_score = _scale(sensor.lane_deviation_m, config.lane_deviation_warning_m, 1.5)
    potential_impact = emergency.emergency_status in {"POTENTIAL ACCIDENT", "ABNORMAL EVENT"}
    components = {
        "Drowsiness": round(drowsy_score * config.drowsiness_weight / 100),
        "Eye closure": round(closure_score * config.eye_closure_weight / 100),
        "Yawning": config.yawning_weight if drowsiness.yawning else 0,
        "Overspeed": round(speed_score * config.overspeed_weight / 100),
        "Traffic": round(traffic_score * config.traffic_weight / 100),
        "Lane deviation": round(lane_score * config.lane_weight / 100),
        "Vehicle health": round(health.health_score * config.health_weight / 100),
        "Impact/emergency": round(emergency.accident_score * config.impact_weight / 100) if potential_impact else 0,
    }
    labels = {
        "Drowsiness": "Drowsiness detected", "Eye closure": "Prolonged eye closure",
        "Yawning": "Yawning detected", "Overspeed": "Overspeed detected",
        "Traffic": "Heavy traffic conditions", "Lane deviation": "Lane deviation detected",
        "Vehicle health": "Vehicle health warning", "Impact/emergency": "Potential accident signal",
    }
    active = [(labels[name], value) for name, value in components.items() if value > 0]
    overspeed = speed_score >= 1
    drowsy = drowsy_score >= 40 or drowsiness.status == "DROWSY"
    lane = lane_score >= 1
    abnormal_health = health.health_status != "NORMAL"
    escalation = 0
    if drowsy and overspeed:
        escalation += 15
        active.append(("Drowsiness + overspeed combination", 15))
    if drowsy and overspeed and lane:
        escalation += 20
        active.append(("Drowsiness + overspeed + lane deviation", 20))
    if potential_impact and abnormal_health:
        escalation += 25
        active.append(("Potential accident + abnormal vehicle health", 25))
    emergency_state = emergency.emergency_status == "POTENTIAL ACCIDENT" and (abnormal_health or drowsy)
    score = min(100, sum(value for _, value in active) + escalation)
    if emergency_state:
        score = max(score, 90)
    level = "CRITICAL" if score >= 80 else "HIGH" if score >= 55 else "WARNING" if score >= 25 else "SAFE"
    if emergency_state:
        action, status = emergency.recommended_action, "EMERGENCY"
    elif level == "CRITICAL":
        action, status = "Reduce speed, maintain lane, and stop safely as soon as possible.", "MONITOR"
    elif level == "HIGH":
        action, status = "Reduce speed, increase following distance, and take a safe break.", "MONITOR"
    elif level == "WARNING":
        action, status = "Stay alert, reduce risk factors, and monitor the next readings.", "MONITOR"
    else:
        action, status = "Continue attentive driving and keep monitoring.", "CLEAR"
    factors = [name for name, _ in sorted(active, key=lambda item: item[1], reverse=True)[:3]] or ["No active risk factors"]
    if drowsy and overspeed:
        explanation = "High risk because drowsiness and overspeed were detected simultaneously."
    elif emergency_state:
        explanation = "Emergency because a potential accident coincides with driver or vehicle risk."
    elif health.health_status != "NORMAL":
        explanation = f"Vehicle health {health.health_status.lower()} because {', '.join(health.detected_issues[:2]).lower()}."
    elif factors == ["No active risk factors"]:
        explanation = "Safe because no significant driver, route, vehicle, or impact risks are active."
    else:
        explanation = f"{level.title()} risk driven mainly by {', '.join(factors[:2]).lower()}."
    return RiskAssessment(round(score), level, factors, action, status, components, explanation)
