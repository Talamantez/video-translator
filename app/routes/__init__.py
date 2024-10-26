from flask import Flask
from .main_routes import main_bp
from .process_routes import process_bp
from .result_routes import result_bp

def create_app():
    app = Flask(__name__)
    
    # Configure app settings if needed
    app.config['SECRET_KEY'] = 'your-secret-key-here'  # You should use an environment variable for this
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(process_bp)
    app.register_blueprint(result_bp)
    
    return app
