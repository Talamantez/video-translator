import os

class Config:
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    OUTPUT_FOLDER = os.path.join(os.getcwd(), 'output')
    SAVED_RESULTS_FOLDER = os.path.join(os.getcwd(), 'saved_results')
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 * 1024  # 16 GB limit
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
