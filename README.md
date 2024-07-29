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


 # Searching the Internet Archive for Short Videos
 - To filter out long videos, go to https://archive.org/advancedsearch.php
 - Add a custom field: AND 'samples_only'
 source: https://archive.org/post/1128410/filtering-out-30-second-audio-samples-from-search-results 

 ## Example short-ish clips:
  ~2 min https://ia601307.us.archive.org/16/items/brigitte-bardot-marseillaise-backstage-of-bb-show-67/Brigitte%20Bardot%20-%20Marseillaise%20-%20%20Backstage%20of%20BB%20Show%2067%20.mp4