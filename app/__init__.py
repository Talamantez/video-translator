from flask import Flask
from config import Config
import logging
import os
from app.routes import main

def create_app(config_class=Config):
    app = Flask(__name__, 
                template_folder=os.path.abspath('app/templates'),
                static_folder=os.path.abspath('app/static'))
    app.config.from_object(config_class)

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Initialize extensions here (if any)

    # Register blueprints
    
    app.register_blueprint(main)

    # Ensure upload and output folders exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SAVED_RESULTS_FOLDER'], exist_ok=True)

    return app
