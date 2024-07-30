##### Assumes Windows Powershell

# Move to the sub-folder 'python'
`cd python`

## Create a virtual environment
`python -m venv .`

## Spin up the environment
`.\Scripts\Activate.ps1`

## Install Requirements
`pip install -r requirements.txt`

## Run the app
`python app.py`

#### Output
`\GitHub\upload-scan-translate\python> py .\app.py
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.  
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 100-503-661`

 ## Visit templates/index.html at http://127.0.0.1:5000/ in your browser

 ## Example short-ish clips:
 ### Dit was de week
    - This Dutch news show is 2 minutes and there are tons of episodes on the internet archive
  https://archive.org/details/2205636-dit-was-de-week