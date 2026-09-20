# AI Smart Vehicle Safety & Assistance System

Software-only prototype for an AI-assisted driver and vehicle safety dashboard.
The system is explicitly labeled **PROTOTYPE / SIMULATED SENSOR DATA** and does
not control a real vehicle.

## Architecture

`app.py` builds one typed `SystemState` snapshot from:

- `detection.py` and `streaming.py` for driver landmarks and drowsiness
- `simulation.py` for coherent scenario sensor data
- `vehicle_health.py` for normalized health assessment
- `emergency.py` for corroborated abnormal-event detection
- `parking.py`, `traffic.py`, and `routing.py` for road assistance
- `risk.py` as the central explainable decision layer

The risk engine produces the score, level, top factors, human explanation,
recommended action, and emergency status. Modules exchange dataclasses rather
than untyped dictionaries.

## Features

- Continuous webcam drowsiness estimation using MediaPipe Face Landmarker (Tasks API), normalized eye opening, prolonged-closure timing, and yawning.
- Simulated GPS, speed, traffic, lane deviation, temperature, vibration, voltage, and impact data.
- Overspeed, vehicle-health, emergency, and lane/traffic detection.
- Explainable weighted multi-condition risk score from 0 to 100.
- Central normalized risk engine with combination escalation, top factors, explanations, actions, and emergency status.
- Streamlit live dashboard and SAFE/DROWSY/OVERSPEED/VEHICLE FAULT/CRITICAL demo scenarios.
- Simulated smart parking availability and nearest-slot recommendation.
- Simulated traffic scoring and transparent route-cost recommendation.
- Dedicated vehicle health assessment for temperature, voltage, vibration, and optional current.
- Dedicated potential-accident assessment requiring impact plus a corroborating abnormal condition.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py --server.address 0.0.0.0
```

Open the displayed local URL in a browser. The webcam control requests
permission and streams frames to the Streamlit process for local inference;
frames are not sent to a vehicle-control system.

When deployed to Render or another hosted HTTPS service, the dashboard supplies a
public Google STUN server to WebRTC so the browser can negotiate the laptop
camera connection across networks. Some restrictive corporate or campus
networks may still require a TURN relay; this prototype does not include a
private TURN server or credentials.

The Face Landmarker asset is stored at `models/face_landmarker.task`. It is downloaded from
Google's official MediaPipe model hosting URL:
`https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task`.
The browser camera is streamed to the local Streamlit process with `streamlit-webrtc`; frames are not sent to a vehicle or external service.

Run the core tests with:

```powershell
python -m pytest -q
```

This prototype is not safety-certified, drowsiness thresholds are configurable heuristics, and it does not connect to or control vehicle hardware.

The unified demo scenarios are `NORMAL_DRIVING`, `DROWSY_DRIVER`, `OVERSPEED`,
`HEAVY_TRAFFIC`, `VEHICLE_HEALTH_WARNING`, `DROWSY_OVERSPEED`,
`DROWSY_OVERSPEED_LANE_DEVIATION`, `POTENTIAL_ACCIDENT`, and
`CRITICAL_EMERGENCY`. The risk engine is decision support only: it never controls
braking, steering, throttle, or other physical vehicle systems.

Parking, traffic, and route data are simulated. Route cost combines distance,
estimated time, and congestion; it is not real-time navigation.

Vehicle health and emergency signals are also simulated. The emergency detector
is a prototype abnormal-event heuristic, not a reliable real-world crash detector.
It requires a high impact signal plus sudden speed change, abnormal vibration, or
a stopped vehicle after the event. No physical vehicle controls are implemented.

## Technology stack

Python 3.13, Streamlit, Streamlit-WebRTC, MediaPipe Tasks Face Landmarker,
OpenCV, NumPy, and Pytest.

## Folder structure

```text
app.py
models/face_landmarker.task
vehicle_safety/
  config.py models.py simulation.py risk.py
  detection.py streaming.py vehicle_health.py emergency.py
  parking.py traffic.py routing.py
tests/test_core.py
```

## Future hardware integration

A future read-only gateway could provide signed CAN/OBD-II or external sensor
data to the typed state model. Physical vehicle controls must remain outside
this prototype and require separate safety certification and validation.
