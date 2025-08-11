# backend/app.py
import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from config import Config
from auth import bp as auth_bp
from extensions import db, migrate

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    db.init_app(app)
    import models  # noqa

    migrate.init_app(app, db)

    app.register_blueprint(auth_bp)

    @app.get("/api/health")
    def health():
        return jsonify(ok=True, service="projectpeak-api")

    return app


app = create_app()


@app.get("/api/debug/cookies")
def debug_cookies():
    from flask import request, jsonify

    return jsonify(
        {
            "raw": request.headers.get("Cookie"),
            "parsed": dict(request.cookies),
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
