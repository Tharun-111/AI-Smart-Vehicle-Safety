"""Typed aggregate used to connect all prototype modules."""

from dataclasses import dataclass

from .emergency import EmergencyAssessment
from .parking import ParkingSummary
from .risk import RiskAssessment
from .traffic import TrafficSummary
from .routing import RouteRecommendation
from .vehicle_health import VehicleHealthAssessment
from .detection import DrowsinessResult
from .simulation import SensorSnapshot


@dataclass(frozen=True)
class SystemState:
    """One immutable snapshot consumed by the dashboard and decision layer."""

    sensors: SensorSnapshot
    driver: DrowsinessResult
    health: VehicleHealthAssessment
    emergency: EmergencyAssessment
    traffic: TrafficSummary
    route: RouteRecommendation | None
    parking: ParkingSummary
    risk: RiskAssessment | None = None
