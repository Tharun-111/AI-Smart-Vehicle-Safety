"""Centralized prototype thresholds and scoring weights."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyConfig:
    speed_limit_kmh: float = 80.0
    overspeed_grace_kmh: float = 5.0
    emergency_impact_g: float = 4.0
    engine_temp_warning_c: float = 105.0
    vibration_warning_g: float = 1.2
    low_voltage_warning_v: float = 12.4
    high_current_warning_a: float = 80.0
    critical_temperature_c: float = 120.0
    critical_vibration_g: float = 2.0
    critical_voltage_v: float = 11.8
    accident_impact_score: float = 70.0
    accident_speed_change_kmh: float = 25.0
    accident_vibration_g: float = 1.5
    lane_deviation_warning_m: float = 0.45
    drowsiness_weight: int = 25
    eye_closure_weight: int = 10
    yawning_weight: int = 5
    overspeed_weight: int = 20
    traffic_weight: int = 10
    lane_weight: int = 10
    health_weight: int = 10
    impact_weight: int = 10
    status_weight: int = 0
    eye_closure_ratio: float = 0.18
    drowsiness_closure_seconds: float = 1.5
    yawn_ratio: float = 0.65
    yawn_score: float = 70.0


DEFAULT_CONFIG = SafetyConfig()
