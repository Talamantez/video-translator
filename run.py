# run.py
import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    # This allows your app to work both locally and on Heroku
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)