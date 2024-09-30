from flask import Flask
from config import Config
import logging
import os
from app.utils import static_versioning

def create_app(config_class=Config):
    app = Flask(__name__, 
                template_folder=os.path.abspath('app/templates'),
                static_folder=os.path.abspath('app/static'))
    app.config.from_object(config_class)

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Initialize extensions here (if any)

    # Register blueprints
    from app.routes import main_bp, process_bp, result_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(process_bp)
    app.register_blueprint(result_bp)

    # Ensure upload and output folders exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SAVED_RESULTS_FOLDER'], exist_ok=True)

    static_versioning.init_app(app)

    return app
