import time
from sqlalchemy import create_engine
from urllib.parse import quote_plus
import sys

project_ref = "frcfaxckvqojizwhbaac"
password = "DaEndsieg25$"
username = "postgres" 
full_username = f"{username}.{project_ref}"

regions = [
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "eu-central-1", "eu-west-1", "eu-west-2", "eu-west-3", "eu-north-1",
    "ap-southeast-1", "ap-southeast-2", "ap-northeast-1", "ap-northeast-2", "ap-south-1",
    "sa-east-1", "ca-central-1"
]

def test_connection(region):
    pooler_host = f"aws-0-{region}.pooler.supabase.com"
    safe_password = quote_plus(password)
    safe_user = quote_plus(full_username)
    
    url = f"postgresql://{safe_user}:{safe_password}@{pooler_host}:6543/postgres"
    print(f"Testing {region}...", end="", flush=True)
    
    try:
        engine = create_engine(url, connect_args={"connect_timeout": 3})
        with engine.connect() as conn:
            print(" SUCCESS!")
            return url
    except Exception as e:
        err = str(e).lower()
        if "tenant or user not found" in err:
            print(" Not found.")
        elif "timeout" in err:
            print(" Timeout.")
        else:
            print(f" Error: {err}")
    return None

found_url = None
for region in regions:
    url = test_connection(region)
    if url:
        found_url = url
        break

if found_url:
    print(f"\nFOUND! Region: {region}")
    print(f"Connection String: {found_url}")
else:
    print("\nCould not find project in any region.")
