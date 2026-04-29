def register_blueprints(app):
    from .admin import admin_bp
    from .api import api_bp
    from .customer import customer_bp
    from .health import health_bp
    from .main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(admin_bp)
