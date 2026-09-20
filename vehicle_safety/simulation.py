from dataclasses import dataclass
import random

from .config import DEFAULT_CONFIG, SafetyConfig


SCENARIOS = (
    "SAFE_DRIVING", "DROWSY_DRIVER", "OVERSPEED", "DROWSY_AND_OVERSPEED",
    "VEHICLE_HEALTH_WARNING", "POTENTIAL_ACCIDENT", "CRITICAL_COMBINATION",
)
DEMO_SCENARIOS = (
    "NORMAL_DRIVING", "DROWSY_DRIVER", "OVERSPEED", "HEAVY_TRAFFIC",
    "VEHICLE_HEALTH_WARNING", "DROWSY_OVERSPEED",
    "DROWSY_OVERSPEED_LANE_DEVIATION", "POTENTIAL_ACCIDENT", "CRITICAL_EMERGENCY",
)


@dataclass(frozen=True)
class SensorSnapshot:
    speed_kmh: float
    speed_limit_kmh: float
    traffic_level: str
    lane_deviation_m: float
    latitude: float
    longitude: float
    engine_temp_c: float
    vibration_g: float
    voltage_v: float
    impact_g: float
    driver_vehicle_status: str = "NORMAL"
    current_a: float | None = None
    sudden_speed_change_kmh: float = 0.0
    vehicle_stopped_after_event: bool = False


def generate_snapshot(seed: int | None = None, scenario: str = "SAFE", config: SafetyConfig = DEFAULT_CONFIG) -> SensorSnapshot:
    rng = random.Random(seed)
    scenario = scenario.upper()
    if scenario in ("OVERSPEED", "OVERSPEED DETECTED", "DROWSY_OVERSPEED", "DROWSY_AND_OVERSPEED", "DROWSY_OVERSPEED_LANE_DEVIATION"):
        values = (rng.uniform(105, 140), "HEAVY", rng.uniform(0.5, 1.0), rng.uniform(82, 101), rng.uniform(0.1, 0.5), rng.uniform(13.3, 14.5))
    elif scenario == "HEAVY_TRAFFIC":
        values = (rng.uniform(35, 75), "HEAVY", rng.uniform(0.1, 0.4), rng.uniform(82, 101), rng.uniform(0.1, 0.5), rng.uniform(13.3, 14.5))
    elif scenario in ("VEHICLE_FAULT", "VEHICLE_HEALTH_WARNING", "VEHICLE HEALTH WARNING"):
        values = (rng.uniform(35, 75), "MODERATE", rng.uniform(0.1, 0.5), rng.uniform(108, 125), rng.uniform(1.4, 2.2), rng.uniform(11.3, 12.2))
    elif scenario in ("POTENTIAL_ACCIDENT",):
        values = (rng.uniform(45, 85), "MODERATE", rng.uniform(0.1, 0.4), rng.uniform(82, 101), rng.uniform(1.4, 2.2), rng.uniform(11.3, 12.2))
    elif scenario in ("CRITICAL", "EMERGENCY IMPACT", "CRITICAL_COMBINATION", "CRITICAL_EMERGENCY", "DROWSY_OVERSPEED_LANE_DEVIATION"):
        values = (rng.uniform(105, 140), "HEAVY", rng.uniform(0.7, 1.5), rng.uniform(110, 130), rng.uniform(1.5, 2.5), rng.uniform(11.2, 12.0))
    else:
        values = (rng.uniform(35, 75), "LIGHT", rng.uniform(0.02, 0.25), rng.uniform(82, 101), rng.uniform(0.1, 0.5), rng.uniform(13.3, 14.5))
    speed, traffic, lane, temp, vibration, voltage = values
    impact = rng.uniform(4.5, 8.0) if scenario in ("CRITICAL", "EMERGENCY IMPACT", "CRITICAL_COMBINATION", "CRITICAL_EMERGENCY") else (rng.uniform(2.2, 3.2) if scenario == "POTENTIAL_ACCIDENT" else rng.uniform(0.0, 0.5))
    accident = scenario in ("POTENTIAL_ACCIDENT", "CRITICAL_COMBINATION", "CRITICAL_EMERGENCY")
    status = "ABNORMAL" if scenario in ("VEHICLE_HEALTH_WARNING", "POTENTIAL_ACCIDENT", "CRITICAL_COMBINATION", "CRITICAL_EMERGENCY") else "NORMAL"
    return SensorSnapshot(
        round(speed, 1), config.speed_limit_kmh, traffic, round(lane, 2),
        round(17.3850 + rng.uniform(-0.01, 0.01), 5), round(78.4867 + rng.uniform(-0.01, 0.01), 5),
        round(temp, 1), round(vibration, 2), round(voltage, 2), round(impact, 2),
        status,
        round(rng.uniform(85, 110) if status == "ABNORMAL" else rng.uniform(20, 55), 2),
        round(rng.uniform(35, 70) if accident else rng.uniform(0, 8), 2),
        accident,
    )
