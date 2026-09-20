from dataclasses import dataclass

from .traffic import Road, traffic_score


@dataclass(frozen=True)
class RouteRecommendation:
    road: Road
    cost: float
    reason: str


def route_cost(
    road: Road,
    distance_weight: float = 0.35,
    time_weight: float = 0.40,
    traffic_weight: float = 0.25,
) -> float:
    """Transparent route cost; lower is better and traffic is explicitly penalized."""
    return (
        road.distance_km * distance_weight
        + road.estimated_time_min * time_weight
        + traffic_score(road.traffic_level) * traffic_weight
    )


def recommend_route(roads: list[Road]) -> RouteRecommendation | None:
    if not roads:
        return None
    ranked = sorted(roads, key=route_cost)
    selected = ranked[0]
    reasons = [f"{selected.distance_km:.1f} km", f"{selected.estimated_time_min:.0f} min"]
    if selected.traffic_level.upper() != "HIGH":
        reasons.append(f"{selected.traffic_level.lower()} congestion")
    return RouteRecommendation(selected, route_cost(selected), "Lowest transparent route cost: " + ", ".join(reasons) + ".")
