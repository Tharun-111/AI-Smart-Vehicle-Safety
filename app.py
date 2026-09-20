import time

import streamlit as st

from vehicle_safety.config import DEFAULT_CONFIG
from vehicle_safety.detection import DrowsinessResult
from vehicle_safety.emergency import detect_potential_accident
from vehicle_safety.risk import assess_risk
from vehicle_safety.parking import demo_parking, summarize_parking
from vehicle_safety.routing import recommend_route, route_cost
from vehicle_safety.simulation import DEMO_SCENARIOS, generate_snapshot
from vehicle_safety.streaming import DriverVideoProcessor
from vehicle_safety.traffic import analyze_traffic, demo_roads
from vehicle_safety.vehicle_health import assess_vehicle_health
from vehicle_safety.models import SystemState
from streamlit_webrtc import WebRtcMode, webrtc_streamer

st.set_page_config(page_title="AI Smart Vehicle Safety", page_icon="🚗", layout="wide")
if "drowsiness" not in st.session_state:
    st.session_state.drowsiness = DrowsinessResult("NO FACE", 0.0, 0, 0, "Start the webcam to monitor the driver.")

st.title("🚗 AI Smart Vehicle Safety & Assistance")
st.caption("Software-only prototype • Simulated hardware inputs • No real vehicle controls connected")
with st.sidebar:
    st.header("Demo controls")
    st.markdown("**PROTOTYPE / SIMULATED SENSOR DATA**")
    if "demo_running" not in st.session_state:
        st.session_state.demo_running = True
    demo_cols = st.columns(2)
    if demo_cols[0].button("Start demo", use_container_width=True):
        st.session_state.demo_running = True
    if demo_cols[1].button("Reset to normal", use_container_width=True):
        st.session_state.demo_running = False
        st.session_state.demo_scenario = "NORMAL_DRIVING"
    scenario = st.selectbox("Demo scenario", DEMO_SCENARIOS, key="demo_scenario")
    seed = st.number_input("Simulation seed", min_value=0, value=int(time.time()) % 100000, step=1)
    st.caption("Drowsiness is represented by the live webcam or by the selected demo scenario.")

snapshot = generate_snapshot(int(seed), scenario, DEFAULT_CONFIG)
driver = st.session_state.drowsiness
if scenario in ("DROWSY_DRIVER", "DROWSY_OVERSPEED", "DROWSY_OVERSPEED_LANE_DEVIATION", "CRITICAL_EMERGENCY"):
    driver = DrowsinessResult("DROWSY", 90.0, 1, 0, "Demo scenario: simulated drowsy driver.", "simulation", 0.05, 2.0, scenario == "CRITICAL_EMERGENCY")
assessment = assess_risk(snapshot, driver, DEFAULT_CONFIG)
health = assess_vehicle_health(snapshot.engine_temp_c, snapshot.voltage_v, snapshot.vibration_g, snapshot.current_a, DEFAULT_CONFIG)
emergency = detect_potential_accident(
    min(100, snapshot.impact_g / DEFAULT_CONFIG.emergency_impact_g * 100),
    snapshot.sudden_speed_change_kmh,
    snapshot.vibration_g,
    snapshot.vehicle_stopped_after_event,
    DEFAULT_CONFIG,
)
assessment = assess_risk(snapshot, driver, DEFAULT_CONFIG, health, emergency)

if assessment.emergency:
    st.error("🚨 CRITICAL EMERGENCY: impact/abnormal state detected. Prototype recommends contacting emergency services.")

overview = st.columns(6)
overview[0].metric("Risk score", f"{assessment.score}/100", assessment.level)
overview[1].metric("Driver", driver.status, f"{driver.score:.0%} signal")
overview[2].metric("Speed", f"{snapshot.speed_kmh:.1f} km/h", f"Limit {snapshot.speed_limit_kmh:.0f}")
overview[3].metric("Traffic", snapshot.traffic_level)
overview[4].metric("Camera", "Ready" if driver.backend != "none" else "Waiting")
overview[5].metric("Emergency", "ACTIVE" if assessment.emergency else "Clear")

left, right = st.columns([1, 1])
with left:
    st.subheader("Driver camera monitoring")
    ctx = webrtc_streamer(
        key="driver-monitor",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=DriverVideoProcessor,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )
    if ctx.video_processor:
        driver = ctx.video_processor.latest
    st.info(driver.message)
    st.metric("Live drowsiness score", f"{driver.score:.0f}/100", driver.status)
    st.caption(f"Source: Laptop Camera • Backend: {driver.backend} • Eye opening: {driver.eye_opening:.3f} • Eyes closed: {driver.eyes_closed_seconds:.1f}s • Yawning: {'Yes' if driver.yawning else 'No'}")

with right:
    st.subheader("Transparent multi-condition risk")
    st.metric("Recommended action", assessment.recommended_action)
    st.metric("Emergency status", assessment.emergency_status)
    st.info(assessment.explanation)
    st.progress(assessment.score / 100, text=f"{assessment.level} risk")
    st.caption("Top contributing factors")
    for factor in assessment.factors[:3]:
        st.write(f"• {factor}")
    st.caption("Component contributions")
    st.json(assessment.component_scores)

st.subheader("Vehicle and route telemetry")
telemetry = st.columns(6)
telemetry[0].metric("GPS", f"{snapshot.latitude:.4f}, {snapshot.longitude:.4f}")
telemetry[1].metric("Lane deviation", f"{snapshot.lane_deviation_m:.2f} m")
telemetry[2].metric("Temperature", f"{snapshot.engine_temp_c:.1f} °C")
telemetry[3].metric("Vibration", f"{snapshot.vibration_g:.2f} g")
telemetry[4].metric("Voltage", f"{snapshot.voltage_v:.2f} V")
telemetry[5].metric("Impact", f"{snapshot.impact_g:.2f} g")

st.divider()
st.header("VEHICLE HEALTH")
st.caption("PROTOTYPE / SIMULATED SENSOR DATA")
health_cols = st.columns(5)
health_cols[0].metric("Health status", health.health_status)
health_cols[1].metric("Health risk", f"{health.health_score}/100")
health_cols[2].metric("Temperature", f"{health.temperature:.1f} °C")
health_cols[3].metric("Battery voltage", f"{health.voltage:.2f} V")
health_cols[4].metric("Vibration", f"{health.vibration:.2f} g")
st.write("Detected issues: " + ", ".join(health.detected_issues))

st.header("EMERGENCY DETECTION")
emergency_cols = st.columns(4)
emergency_cols[0].metric("Status", emergency.emergency_status)
emergency_cols[1].metric("Accident score", f"{emergency.accident_score}/100")
emergency_cols[2].metric("Speed change", f"{snapshot.sudden_speed_change_kmh:.1f} km/h")
emergency_cols[3].metric("Stopped after event", "Yes" if snapshot.vehicle_stopped_after_event else "No")
st.write("Conditions: " + ", ".join(emergency.detected_conditions))
st.caption(emergency.recommended_action)

mobility_demo = "HEAVY TRAFFIC ON SHORTEST ROUTE" if snapshot.traffic_level == "HEAVY" else "LOW TRAFFIC"
parking_mode = "NO PARKING AVAILABLE" if scenario == "CRITICAL_EMERGENCY" else mobility_demo
parking = summarize_parking(demo_parking(parking_mode))
roads = demo_roads(mobility_demo)
traffic = analyze_traffic(roads)
recommended_route = recommend_route(roads)
system_state = SystemState(snapshot, driver, health, emergency, traffic, recommended_route, parking, assessment)

st.divider()
st.header("SMART PARKING")
parking_cols = st.columns(4)
parking_cols[0].metric("Total slots", parking.total_slots)
parking_cols[1].metric("Available slots", parking.available_slots)
parking_cols[2].metric("Occupied slots", parking.occupied_slots)
parking_cols[3].metric("Nearest slot", parking.nearest_available.slot_id if parking.nearest_available else "None")
for slot in demo_parking(mobility_demo):
    state = "OCCUPIED" if slot.occupied else f"AVAILABLE • {slot.distance_m:.0f} m"
    st.write(f"Slot {slot.slot_id} → {state} • confidence {slot.confidence:.0%}")
if parking.nearest_available:
    st.success(f"Recommendation → Slot {parking.nearest_available.slot_id}")
else:
    st.warning("No parking available in the simulated search area.")

st.header("TRAFFIC & ROUTES")
traffic_cols = st.columns(2)
traffic_cols[0].metric("Current traffic level", traffic.level)
traffic_cols[1].metric("Traffic score", f"{traffic.score}/100")
for road in roads:
    st.write(
        f"**{road.road_name}** — {road.distance_km:.1f} km • "
        f"{road.estimated_time_min:.0f} min • {road.traffic_level} traffic • "
        f"route cost {route_cost(road):.1f}"
    )
if recommended_route:
    st.success(
        f"Recommended route → {recommended_route.road.road_name}. "
        f"{recommended_route.reason}"
    )
st.caption("Traffic and route recommendations are simulated decision support, not real-time navigation.")

st.divider()
st.caption("Prototype only: this system observes simulated/read-only inputs and never actuates braking, steering, throttle, or other vehicle controls.")
