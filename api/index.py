from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import math
from pathlib import Path

app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# Load telemetry data
DATA_PATH = Path(__file__).parent.parent / "telemetry.json"

with open(DATA_PATH, "r") as f:
    telemetry = json.load(f)


class RequestBody(BaseModel):
    regions: List[str]
    threshold_ms: float


def percentile(values, p):
    """Calculate percentile using linear interpolation."""
    if not values:
        return None

    values = sorted(values)

    if len(values) == 1:
        return values[0]

    position = (len(values) - 1) * p
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return values[lower]

    return (
        values[lower]
        + (values[upper] - values[lower]) * (position - lower)
    )


@app.post("/")
def calculate_metrics(request: RequestBody):

    result = {}

    for region in request.regions:

        records = [
            row for row in telemetry
            if row["region"].lower() == region.lower()
        ]

        if not records:
            result[region] = {
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime": None,
                "breaches": 0
            }
            continue

        latencies = [row["latency_ms"] for row in records]
        uptimes = [row["uptime_pct"] for row in records]

        result[region] = {
            "avg_latency": sum(latencies) / len(latencies),
            "p95_latency": percentile(latencies, 0.95),
            "avg_uptime": sum(uptimes) / len(uptimes),
            "breaches": sum(
                1 for latency in latencies
                if latency > request.threshold_ms
            )
        }

    return result