from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# (region, latency_ms, uptime_pct)
ROWS = [
    ("apac", 108.42, 97.705), ("apac", 139.75, 99.1), ("apac", 236.28, 98.64),
    ("apac", 138.1, 97.559), ("apac", 114.11, 97.85), ("apac", 220.9, 97.129),
    ("apac", 194.51, 97.346), ("apac", 171.28, 97.505), ("apac", 205.35, 98.032),
    ("apac", 178.14, 97.623), ("apac", 187.33, 97.665), ("apac", 185.24, 97.62),
    ("emea", 164.8, 97.77), ("emea", 134.9, 97.463), ("emea", 228.76, 97.382),
    ("emea", 142.28, 97.981), ("emea", 235.05, 99.14), ("emea", 135.95, 97.523),
    ("emea", 213.83, 98.216), ("emea", 157.21, 97.755), ("emea", 131.89, 98.338),
    ("emea", 227.91, 98.423), ("emea", 196.68, 99.106), ("emea", 99.73, 99.437),
    ("amer", 208.84, 97.579), ("amer", 115.17, 98.923), ("amer", 189.52, 99.243),
    ("amer", 120.68, 99.056), ("amer", 155.2, 98.003), ("amer", 146.67, 98.584),
    ("amer", 129.6, 98.126), ("amer", 144.53, 97.977), ("amer", 124.63, 97.465),
    ("amer", 163.01, 99.146), ("amer", 108.62, 97.626), ("amer", 127.37, 98.325),
]


class Query(BaseModel):
    regions: list[str]
    threshold_ms: float


def percentile(values, p):
    s = sorted(values)
    k = (len(s) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


@app.post("/")
@app.post("/api")
@app.post("/api/")
def metrics(q: Query):
    out = {}
    for region in q.regions:
        lat = [r[1] for r in ROWS if r[0] == region]
        up = [r[2] for r in ROWS if r[0] == region]
        if not lat:
            continue
        out[region] = {
            "avg_latency": sum(lat) / len(lat),
            "p95_latency": percentile(lat, 95),
            "avg_uptime": sum(up) / len(up),
            "breaches": sum(1 for x in lat if x > q.threshold_ms),
        }
    return out