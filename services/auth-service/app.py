# ──────────────────────────────────────────────────────────────
# AUTH SERVICE — app.py
# Purpose: Handle all user identity operations
#          (signup, login, token verification)
# Port: 5001
# ──────────────────────────────────────────────────────────────


# ── CHUNK 1: Imports (Tools on the counter) ───────────────────

import os                          # Read environment variables (secrets)
import logging                     # Write diary logs of everything that happens
import bcrypt                      # Hash passwords — the meat grinder 🥩
from datetime import timedelta     # Express time durations (e.g. 1 hour)

from flask import Flask, request, jsonify          # Web server + read requests + send JSON
from flask_jwt_extended import (
    JWTManager,                    # Sets up JWT for the whole app
    create_access_token,           # Mints a new token (wristband)
    jwt_required,                  # Bodyguard — blocks requests without valid token
    get_jwt_identity               # Reads WHO the token belongs to
)
from prometheus_flask_exporter import PrometheusMetrics  # Auto-tracks all requests


# ── CHUNK 2: Logging Setup (Set up the diary) ─────────────────

logging.basicConfig(
    level=logging.INFO,            # Show INFO, WARNING, ERROR, CRITICAL (not DEBUG)
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    # Produces: 2026-03-18 20:00:01 [INFO] auth-service: User deepak logged in
)
logger = logging.getLogger("auth-service")   # Our named logger for this service


# ── CHUNK 3: App Creation & Config (Build the restaurant) ─────

app = Flask(__name__)              # Create the entire web server in one line

# JWT secret key — used to sign tokens (like a wax seal)
# Read from environment variable; fallback is for development ONLY
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-prod")

# Tokens expire after 1 hour — limits damage if a token is stolen
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

jwt = JWTManager(app)             # Wire JWT into the Flask app
metrics = PrometheusMetrics(app)  # Wire Prometheus monitoring into the Flask app


# ── CHUNK 4: User Storage (In-memory filing cabinet) ──────────

# Dictionary: { "deepak": "$2b$12$hashedpassword..." }
# ⚠️  Lives in RAM — resets on restart
# ✅  Fine for development; replace with PostgreSQL in production
users = {}


# ── CHUNK 5: Endpoints (The 4 doors of the service) ───────────

# ── DOOR 1: Health Check ──────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    """
    Kubernetes liveness probe.
    Kubernetes pings this every 30s.
    No response = Kubernetes restarts the container automatically.
    """
    logger.info("Health check called")
    return jsonify({
        "status": "healthy",
        "service": "auth-service"
    }), 200                        # 200 = OK


# ── DOOR 2: Signup ────────────────────────────────────────────
@app.route("/signup", methods=["POST"])
def signup():
    """
    Register a new user.
    Accepts: { "username": "deepak", "password": "mypassword" }
    Returns: success message or error
    """
    data = request.get_json()      # Open the envelope — read incoming JSON

    # Validate: reject if username or password is missing
    if not data or not data.get("username") or not data.get("password"):
        logger.warning("Signup failed: missing username or password")
        return jsonify({"error": "Username and password required"}), 400   # 400 = Bad Request

    username = data["username"]
    password = data["password"]

    # Reject if user already exists
    if username in users:
        logger.warning(f"Signup failed: user '{username}' already exists")
        return jsonify({"error": "User already exists"}), 409              # 409 = Conflict

    # Hash the password — NEVER store plain text
    # bcrypt.gensalt() adds random salt → same password hashes differently each time
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    users[username] = hashed       # Store hash, not the real password

    logger.info(f"New user registered: '{username}'")
    return jsonify({"message": f"User '{username}' created successfully"}), 201  # 201 = Created


# ── DOOR 3: Login ─────────────────────────────────────────────
@app.route("/login", methods=["POST"])
def login():
    """
    Login and receive a JWT token (wristband).
    Accepts: { "username": "deepak", "password": "mypassword" }
    Returns: { "token": "eyJhbGci...", "username": "deepak" }
    """
    data = request.get_json()

    # Validate input
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"error": "Username and password required"}), 400

    username = data["username"]
    password = data["password"]

    # Check if user exists
    if username not in users:
        logger.warning(f"Login failed: user '{username}' not found")
        # ⚠️  Same error for "user not found" AND "wrong password"
        # Security: never tell a hacker WHICH one failed
        return jsonify({"error": "Invalid credentials"}), 401              # 401 = Unauthorized

    # Verify password against stored hash
    # bcrypt re-hashes the input with the same salt and compares
    if not bcrypt.checkpw(password.encode("utf-8"), users[username]):
        logger.warning(f"Login failed: wrong password for '{username}'")
        return jsonify({"error": "Invalid credentials"}), 401

    # All checks passed — mint a JWT token
    # The username is baked INTO the token (no DB call needed to retrieve it later)
    token = create_access_token(identity=username)

    logger.info(f"User logged in: '{username}'")
    return jsonify({
        "token": token,
        "username": username
    }), 200                                                                 # 200 = OK


# ── DOOR 4: Verify ────────────────────────────────────────────
@app.route("/verify", methods=["GET"])
@jwt_required()                    # 🛡️  Bodyguard — if no valid token → 401, function never runs
def verify():
    """
    Verify a JWT token is valid and not expired.
    Requires: Authorization: Bearer <token> in request header
    Returns: { "valid": true, "username": "deepak" }
    """
    current_user = get_jwt_identity()   # Read username baked into the token
    logger.info(f"Token verified for user: '{current_user}'")
    return jsonify({
        "valid": True,
        "username": current_user
    }), 200


# ── CHUNK 6: Entry Point (Start the engine) ───────────────────

if __name__ == "__main__":
    # Only runs when you execute: python app.py directly
    # Skipped if another file imports this module
    logger.info("Starting Auth Service on port 5001")
    app.run(
        host="0.0.0.0",            # Listen on ALL interfaces (required inside Docker/K8s)
        port=5001,                 # Auth=5001, Order=5002, Recommendation=5003
        debug=False                # NEVER True in production — exposes code internals
    )

