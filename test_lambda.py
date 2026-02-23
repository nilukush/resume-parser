"""Test if the lambda handler is working."""
import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.getcwd())

os.environ['DATABASE_URL'] = 'test'
os.environ['USE_DATABASE'] = 'false'
os.environ['ENABLE_OCR_FALLBACK'] = 'false'

try:
    from mangum import Mangum
    from app.main import app
    
    handler = Mangum(app, lifespan="off")
    
    # Simulate a Lambda event for /health
    event = {
        "requestContext": {
            "http": {
                "method": "GET",
                "path": "/health"
            }
        },
        "rawPath": "/health",
        "headers": {
            "accept": "application/json"
        }
    }
    
    print("Testing handler with /health endpoint...")
    print(f"Event: {json.dumps(event, indent=2)}")
    
    response = handler(event, {})
    print(f"\nResponse: {json.dumps(response, indent=2)}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
