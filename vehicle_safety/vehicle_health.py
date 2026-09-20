from dataclasses import dataclass

from .config import DEFAULT_CONFIG, SafetyConfig


@dataclass(frozen=True)
class VehicleHealthAssessment:
    temperature: float
    voltage: float
    vibration: float
    current: float | None
    health_score: int
    health_status: str
    detected_issues: list[str]


def _scale(value: float, normal: float, critical: float, inverse: bool = False) -> float:
    if inverse:
        return max(0.0, min(100.0, (normal - value) / (normal - critical) * 100))
    return max(0.0, min(100.0, (value - normal) / (critical - normal) * 100))


def assess_vehicle_health(
    temperature: float,
    voltage: float,
    vibration: float,
    current: float | None = None,
    config: SafetyConfig = DEFAULT_CONFIG,
) -> VehicleHealthAssessment:
    """Convert simulated sensor values into explainable health risk."""
    temperature_risk = _scale(temperature, config.engine_temp_warning_c, config.critical_temperature_c)
    vibration_risk = _scale(vibration, config.vibration_warning_g, config.critical_vibration_g)
    voltage_risk = _scale(voltage, config.low_voltage_warning_v, config.critical_voltage_v, inverse=True)
    current_risk = _scale(current, config.high_current_warning_a, config.high_current_warning_a * 1.5) if current is not None else 0
    risks = [temperature_risk, vibration_risk, voltage_risk, current_risk]
    issues: list[str] = []
    if temperature >= config.engine_temp_warning_c:
        issues.append("High temperature")
    if vibration >= config.vibration_warning_g:
        issues.append("Abnormal vibration")
    if voltage <= config.low_voltage_warning_v:
        issues.append("Low battery voltage")
    if current is not None and current >= config.high_current_warning_a:
        issues.append("High current draw")
    health_score = round(max(risks))
    status = "CRITICAL" if health_score >= 70 or any(
        (temperature >= config.critical_temperature_c, vibration >= config.critical_vibration_g, voltage <= config.critical_voltage_v)
    ) else "WARNING" if issues else "NORMAL"
    return VehicleHealthAssessment(
        round(temperature, 2), round(voltage, 2), round(vibration, 2),
        None if current is None else round(current, 2), health_score, status, issues or ["No abnormal health signals"],
    )
