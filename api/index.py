from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from pathlib import Path
import json
import math

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

DATA_PATH = Path(__file__).resolve().parent.parent / "telemetry.json"

with open(DATA_PATH, "r", encoding="utf-8") as f:
    telemetry = json.load(f)


class MetricsRequest(BaseModel):
    regions: List[str]
    threshold_ms: float = 180


def percentile(values, p):
    values = sorted(values)

    if not values:
        return None

    position = (len(values) - 1) * p
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return values[lower]

    return (
        values[lower] * (upper - position)
        + values[upper] * (position - lower)
    )


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/")
def calculate_metrics(request: MetricsRequest):
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
                "breaches": 0,
            }
            continue

        latencies = [float(row["latency_ms"]) for row in records]
        uptimes = [float(row["uptime_pct"]) for row in records]

        result[region] = {
            "avg_latency": sum(latencies) / len(latencies),
            "p95_latency": percentile(latencies, 0.95),
            "avg_uptime": sum(uptimes) / len(uptimes),
            "breaches": sum(
                latency > request.threshold_ms
                for latency in latencies
            ),
        }

    return result
