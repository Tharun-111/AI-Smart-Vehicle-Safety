from dataclasses import dataclass


@dataclass(frozen=True)
class ParkingSlot:
    slot_id: str
    occupied: bool
    distance_m: float
    confidence: float


@dataclass(frozen=True)
class ParkingSummary:
    total_slots: int
    available_slots: int
    occupied_slots: int
    nearest_available: ParkingSlot | None


def summarize_parking(slots: list[ParkingSlot]) -> ParkingSummary:
    available = [slot for slot in slots if not slot.occupied]
    nearest = min(available, key=lambda slot: slot.distance_m, default=None)
    return ParkingSummary(len(slots), len(available), len(slots) - len(available), nearest)


def demo_parking(mode: str = "LOW TRAFFIC") -> list[ParkingSlot]:
    if mode == "NO PARKING AVAILABLE":
        return [
            ParkingSlot("A", True, 12.0, 0.98),
            ParkingSlot("B", True, 24.0, 0.97),
            ParkingSlot("C", True, 38.0, 0.96),
        ]
    return [
        ParkingSlot("A", True, 12.0, 0.98),
        ParkingSlot("B", False, 35.0, 0.94),
        ParkingSlot("C", False, 18.0, 0.96),
        ParkingSlot("D", False, 52.0, 0.91),
    ]
