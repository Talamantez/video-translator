import os
import hashlib
from flask import url_for, current_app

def get_file_hash(filename):
    hasher = hashlib.md5()
    with open(filename, 'rb') as file:
        buf = file.read()
        hasher.update(buf)
    return hasher.hexdigest()[:8]

def versioned_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(current_app.static_folder, filename)
            if os.path.isfile(file_path):
                values['v'] = get_file_hash(file_path)
    return url_for(endpoint, **values)

def init_app(app):
    @app.before_request
    def before_request():
        app.jinja_env.globals['url_for'] = versioned_url_for
