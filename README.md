##### Assumes Windows Powershell

## Create a virtual environment
`python -m venv venv`

## Spin up the environment
`.\venv\Scripts\Activate.ps1`

## Install Requirements
`pip install -r requirements.txt`

## Run the app
`python app.py`

#### Output
`\GitHub\video-translator> py .\app.py
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.  
 * Running on http://127.0.0.1:8080
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 100-503-661`

 ## Visit templates/index.html at http://127.0.0.1:8080/ in your browser

 ## Example short-ish clips:
 ### Dit was de week
    - This Dutch news show is 2 minutes and there are tons of episodes on the internet archive
  https://archive.org/details/2205636-dit-was-de-week

  # Test
  `pytest tests/test_video_processor.py`
