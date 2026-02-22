"""
Vercel serverless function entry point for ResuMate API.

This file provides lazy-loading of the FastAPI app to prevent
cold start issues in serverless environments.
"""

# Lazy import to prevent initialization at module load time
def handler(event, context):
    """Lambda handler that loads app on first invocation."""
    from mangum import Mangum
    from app.main import app
    
    # Create Mangum wrapper on first call
    if not hasattr(handler, '_mangum_handler'):
        handler._mangum_handler = Mangum(app, lifespan="off")
    
    return handler._mangum_handler(event, context)
