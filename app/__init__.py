from flask import Flask
from pathlib import Path

def create_app():
    app = Flask(__name__)

    # ------------------------------------------------------------------
    # Core configuration
    # ------------------------------------------------------------------
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    # Project root & output paths
    project_root = Path(__file__).resolve().parents[1]
    app.config['PROJECT_ROOT'] = project_root
    app.config['OUTPUT_BASE_DIR'] = project_root / "outputs"

    # ------------------------------------------------------------------
    # Blueprint registration
    #
    # IMPORTANT:
    # - API routes live ONLY under /api
    # - UI routes never define /api paths internally
    # - Order is intentional (UI first, API second)
    # ------------------------------------------------------------------
    from app.routes.main import bp as main_bp
    from app.routes.reports import bp as reports_bp
    from app.routes.analytics import bp as analytics_bp
    from app.routes.contacts import bp as contacts_bp
    from app.routes.api_routes import bp as api_bp

    # UI / page routes
    app.register_blueprint(main_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(contacts_bp)

    # API routes (single authority for /api/*)
    app.register_blueprint(api_bp)

    return app
