from dataclasses import dataclass


@dataclass(frozen=True)
class Road:
    road_name: str
    distance_km: float
    traffic_level: str
    estimated_time_min: float


@dataclass(frozen=True)
class TrafficSummary:
    score: int
    level: str


def traffic_score(level: str) -> int:
    return {"LOW": 15, "MEDIUM": 55, "HIGH": 90}.get(level.upper(), 100)


def analyze_traffic(roads: list[Road]) -> TrafficSummary:
    if not roads:
        return TrafficSummary(0, "LOW")
    score = round(sum(traffic_score(road.traffic_level) for road in roads) / len(roads))
    level = "HIGH" if score >= 70 else "MEDIUM" if score >= 35 else "LOW"
    return TrafficSummary(score, level)


def demo_roads(mode: str) -> list[Road]:
    if mode == "LOW TRAFFIC":
        return [
            Road("Lake View Road", 5.2, "LOW", 10.0),
            Road("Market Street", 6.1, "LOW", 12.0),
        ]
    if mode == "HEAVY TRAFFIC ON SHORTEST ROUTE":
        return [
            Road("Central Avenue", 4.0, "HIGH", 24.0),
            Road("Ring Road", 6.5, "LOW", 13.0),
        ]
    if mode == "ALTERNATIVE LOWER CONGESTION":
        return [
            Road("Main Highway", 5.0, "HIGH", 25.0),
            Road("East Bypass", 7.2, "LOW", 14.0),
        ]
    return [
        Road("Central Avenue", 4.0, "HIGH", 24.0),
        Road("Ring Road", 6.5, "LOW", 13.0),
    ]
