import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from .config import Config
from .auth import bp as auth_bp
from .extensions import db, migrate
from .expenses import bp as expenses_bp
from .clients import bp as clients_bp
from .projects import bp as projects_bp
from .catalog import bp as catalog_bp
from .tasks import bp as tasks_bp
from . import models

load_dotenv()


# backend/app.py (excerpt)
def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    
    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(auth_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(tasks_bp)

    @app.get("/api/health")
    def health():
        return {"ok": True, "service": "projectpeak-api"}
    
    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
