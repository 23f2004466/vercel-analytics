from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import math
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

DATA_FILE = os.path.join(
    os.path.dirname(__file__),
    "q-vercel-latency.json"
)

with open(DATA_FILE, "r") as f:
    data = json.load(f)


def percentile(values, p):
    values = sorted(values)

    if not values:
        return 0

    k = (len(values) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)

    if f == c:
        return values[int(k)]

    return values[f] + (values[c] - values[f]) * (k - f)


@app.post("/")
def analytics(payload: dict):
    regions = payload["regions"]
    threshold = payload["threshold_ms"]

    results = []

    for region in regions:
        records = [
            r for r in data
            if r["region"] == region
        ]

        latencies = [
            r["latency_ms"]
            for r in records
        ]

        uptimes = [
            r["uptime_pct"]
            for r in records
        ]

        results.append({
            "region": region,
            "avg_latency": sum(latencies) / len(latencies),
            "p95_latency": percentile(latencies, 0.95),
            "avg_uptime": sum(uptimes) / len(uptimes),
            "breaches": sum(
                1 for x in latencies
                if x > threshold
            ),
        })

    return {"results": results}
