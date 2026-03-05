from flask import jsonify
from nexus import create_app
from nexus.lab.models import init_auth_tables, init_hospital_tables

app = create_app()
init_auth_tables()
init_hospital_tables()

@app.route("/")
def home():
    return jsonify({
        "message": "NexusCare Backend Running",
        "health_check": "/health"
    })

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=True)