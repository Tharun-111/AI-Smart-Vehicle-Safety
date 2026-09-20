from dataclasses import dataclass

from .config import DEFAULT_CONFIG, SafetyConfig


@dataclass(frozen=True)
class EmergencyAssessment:
    emergency_status: str
    accident_score: int
    detected_conditions: list[str]
    recommended_action: str


def detect_potential_accident(
    impact_score: float,
    sudden_speed_change_kmh: float,
    vibration_g: float,
    vehicle_stopped_after_event: bool,
    config: SafetyConfig = DEFAULT_CONFIG,
) -> EmergencyAssessment:
    """Prototype abnormal-event detector; it is not a reliable crash detector."""
    conditions: list[str] = []
    if impact_score >= config.accident_impact_score:
        conditions.append("High impact/acceleration signal")
    if sudden_speed_change_kmh >= config.accident_speed_change_kmh:
        conditions.append("Sudden speed change")
    if vibration_g >= config.accident_vibration_g:
        conditions.append("Abnormal vibration")
    if vehicle_stopped_after_event:
        conditions.append("Vehicle stopped after abnormal event")
    score = round(min(100, impact_score * 0.5 + min(100, sudden_speed_change_kmh / 60 * 100) * 0.25 + min(100, vibration_g / 3 * 100) * 0.15 + (10 if vehicle_stopped_after_event else 0)))
    # Require an impact plus a corroborating abnormal condition, avoiding false
    # emergency states from a single noisy simulated sensor.
    potential = impact_score >= config.accident_impact_score and (
        sudden_speed_change_kmh >= config.accident_speed_change_kmh
        or vibration_g >= config.accident_vibration_g
        or vehicle_stopped_after_event
    )
    if potential:
        return EmergencyAssessment("POTENTIAL ACCIDENT", score, conditions, "Stop safely if possible and contact emergency services. This prototype does not control the vehicle.")
    if conditions:
        return EmergencyAssessment("ABNORMAL EVENT", score, conditions, "Reduce speed, keep control of the vehicle, and monitor the next readings.")
    return EmergencyAssessment("CLEAR", score, ["No corroborated accident conditions"], "Continue attentive driving and keep monitoring.")
