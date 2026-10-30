
from flask import Flask, jsonify, Response, request, g
import os
import time
import psycopg2

from datetime import datetime, timezone
from prometheus_client import (
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST
)

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "database")
DB_NAME = os.getenv("DB_NAME", "enterprise_db")
DB_USER = os.getenv("DB_USER", "app_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "local_dev_only")

# Total HTTP requests
HTTP_REQUESTS = Counter(
    "enterprise_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

# Request processing duration
HTTP_DURATION = Histogram(
    "enterprise_http_request_duration_seconds",
    "HTTP request processing duration",
    ["endpoint"]
)


@app.before_request
def start_timer():
    g.start_time = time.time()


@app.after_request
def record_metrics(response):
    endpoint = request.endpoint or "unknown"

    HTTP_REQUESTS.labels(
        method=request.method,
        endpoint=endpoint,
        status=response.status_code
    ).inc()

    duration = time.time() - getattr(g, "start_time", time.time())

    HTTP_DURATION.labels(endpoint=endpoint).observe(duration)

    return response


def get_database_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=3
    )


@app.route("/")
def home():
    return jsonify({
        "project": "Enterprise Multi-Tier Cloud Infrastructure",
        "application": "Flask Application Tier",
        "status": "RUNNING",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "application-tier"
    }), 200


@app.route("/db-health")
def database_health():
    try:
        connection = get_database_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT 1")
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        return jsonify({
            "status": "healthy",
            "database": "connected",
            "test_query": result[0]
        }), 200

    except Exception as error:
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(error)
        }), 503


@app.route("/metrics")
def metrics():
    return Response(
        generate_latest(),
        mimetype=CONTENT_TYPE_LATEST
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
