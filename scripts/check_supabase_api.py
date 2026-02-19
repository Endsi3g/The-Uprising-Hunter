import requests
import sys

URL = "https://frcfaxckvqojizwhbaac.supabase.co/rest/v1/"
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZyY2ZheGNrdnFvaml6d2hiYWFjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE0NjQ0OTgsImV4cCI6MjA4NzA0MDQ5OH0.0pI6NMiD6m1AC3hGkfdCrRZgAOichFYTEKSbLbiqK-s"

try:
    response = requests.get(URL, headers={"apikey": ANON_KEY})
    print(f"API Status Code: {response.status_code}")
    print(f"API Headers: {response.headers}")
except Exception as e:
    print(f"API Connection Error: {e}")
    sys.exit(1)
