from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import math
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
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
    lower = math.floor(k)
    upper = math.ceil(k)

    if lower == upper:
        return values[lower]

    return values[lower] + (values[upper] - values[lower]) * (k - lower)


@app.options("/")
async def options():
    response = JSONResponse(content={})
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


@app.post("/")
async def analytics(payload: dict):
    regions = payload["regions"]
    threshold = payload["threshold_ms"]

    results = []

    for region in regions:
        records = [
            r for r in data
            if r["region"] == region
        ]

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        results.append({
            "region": region,
            "avg_latency": sum(latencies) / len(latencies),
            "p95_latency": percentile(latencies, 0.95),
            "avg_uptime": sum(uptimes) / len(uptimes),
            "breaches": sum(x > threshold for x in latencies),
        })

    response = JSONResponse(content={"results": results})
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response
