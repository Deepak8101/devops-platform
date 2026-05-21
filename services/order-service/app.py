import os
import logging
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager, jwt_required, get_jwt_identity
)
from prometheus_flask_exporter import PrometheusMetrics

# ── Logging setup ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("order-service")

# ── App setup ──────────────────────────────────────────────────
app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-prod")

jwt = JWTManager(app)
metrics = PrometheusMetrics(app)

# ── In-memory order store ──────────────────────────────────────
orders = {}

# ── Routes ─────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    logger.info("Health check called")
    return jsonify({"status": "healthy", "service": "order-service"}), 200


@app.route("/orders", methods=["POST"])
@jwt_required()
def create_order():
    current_user = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get("item") or not data.get("quantity"):
        logger.warning(f"Order creation failed for user '{current_user}': missing fields")
        return jsonify({"error": "item and quantity required"}), 400

    order_id = str(uuid.uuid4())
    order = {
        "id":         order_id,
        "user":       current_user,
        "item":       data["item"],
        "quantity":   data["quantity"],
        "status":     "pending",
        "created_at": datetime.utcnow().isoformat()
    }

    orders[order_id] = order
    logger.info(f"Order created: {order_id} by user '{current_user}'")
    return jsonify(order), 201


@app.route("/orders", methods=["GET"])
@jwt_required()
def get_orders():
    current_user = get_jwt_identity()
    user_orders = [o for o in orders.values() if o["user"] == current_user]
    logger.info(f"Orders fetched for user '{current_user}': {len(user_orders)} orders")
    return jsonify({"orders": user_orders, "count": len(user_orders)}), 200


@app.route("/orders/<order_id>", methods=["GET"])
@jwt_required()
def get_order(order_id):
    current_user = get_jwt_identity()

    if order_id not in orders:
        logger.warning(f"Order '{order_id}' not found")
        return jsonify({"error": "Order not found"}), 404

    order = orders[order_id]

    if order["user"] != current_user:
        logger.warning(f"User '{current_user}' tried to access order of '{order['user']}'")
        return jsonify({"error": "Unauthorized"}), 403

    return jsonify(order), 200


# ── Entry point ────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("Starting Order Service on port 5002")
    app.run(host="0.0.0.0", port=5002, debug=False)
