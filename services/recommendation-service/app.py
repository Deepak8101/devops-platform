import os
import logging
from flask import Flask, jsonify
from flask_jwt_extended import (
    JWTManager, jwt_required, get_jwt_identity
)
from prometheus_flask_exporter import PrometheusMetrics

# ── Logging ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("recommendation-service")

# ── App setup ──────────────────────────────────────────────────
app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-prod")

jwt     = JWTManager(app)
metrics = PrometheusMetrics(app)

# ── Static recommendation catalogue ───────────────────────────
RECOMMENDATIONS = {
    "default": [
        {"id": "p001", "name": "Mechanical Keyboard",  "category": "Electronics", "score": 0.95},
        {"id": "p002", "name": "4K Monitor",           "category": "Electronics", "score": 0.91},
        {"id": "p003", "name": "Ergonomic Chair",      "category": "Furniture",   "score": 0.88},
        {"id": "p004", "name": "Noise Cancelling Headphones", "category": "Electronics", "score": 0.85},
        {"id": "p005", "name": "Standing Desk",        "category": "Furniture",   "score": 0.82},
    ],
    "deepak": [
        {"id": "p010", "name": "MacBook Pro",          "category": "Electronics", "score": 0.98},
        {"id": "p011", "name": "Docker in Practice",   "category": "Books",       "score": 0.96},
        {"id": "p012", "name": "Kubernetes Handbook",  "category": "Books",       "score": 0.94},
        {"id": "p013", "name": "Vim Keyboard",         "category": "Electronics", "score": 0.90},
        {"id": "p014", "name": "Dev Stickers Pack",    "category": "Accessories", "score": 0.87},
    ]
}

# ── Routes ─────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    logger.info("Health check called")
    return jsonify({"status": "healthy", "service": "recommendation-service"}), 200


@app.route("/recommendations", methods=["GET"])
@jwt_required()
def get_recommendations():
    current_user = get_jwt_identity()

    # Use personalised list if exists, else default
    recs = RECOMMENDATIONS.get(current_user, RECOMMENDATIONS["default"])

    logger.info(f"Recommendations fetched for user '{current_user}': {len(recs)} items")
    return jsonify({
        "user":            current_user,
        "recommendations": recs,
        "count":           len(recs)
    }), 200


@app.route("/recommendations/<category>", methods=["GET"])
@jwt_required()
def get_by_category(category):
    current_user = get_jwt_identity()

    recs = RECOMMENDATIONS.get(current_user, RECOMMENDATIONS["default"])
    filtered = [r for r in recs if r["category"].lower() == category.lower()]

    logger.info(f"Category '{category}' fetched for user '{current_user}': {len(filtered)} items")

    if not filtered:
        return jsonify({"error": f"No recommendations for category '{category}'"}), 404

    return jsonify({
        "user":            current_user,
        "category":        category,
        "recommendations": filtered,
        "count":           len(filtered)
    }), 200


# ── Entry point ────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("Starting Recommendation Service on port 5003")
    app.run(host="0.0.0.0", port=5003, debug=False)
