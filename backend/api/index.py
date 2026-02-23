"""
Vercel serverless function entry point for ResuMate API.

This file wraps the FastAPI application with Mangum to work
with Vercel's serverless functions (AWS Lambda).
"""

import logging
import sys
import traceback

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Vercel serverless function handler with detailed error logging.

    This wrapper function catches and logs any errors that occur during
    import or initialization, making debugging easier in serverless environments.
    """
    try:
        # Step 1: Import Mangum (should always work)
        from mangum import Mangum
        logger.info("✅ Step 1: Mangum imported successfully")

        # Step 2: Import FastAPI app (this is where errors usually occur)
        try:
            from app.main import app
            logger.info("✅ Step 2: FastAPI app imported successfully")
        except Exception as e:
            logger.error(f"❌ Step 2 FAILED: Could not import app.main")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": '{"error": "Failed to import FastAPI app", "details": "' + str(e) + '"}'
            }

        # Step 3: Create Mangum handler
        try:
            mangum_handler = Mangum(
                app,
                lifespan="off",
                api_gateway_base_path=None,
                text_mime_types=["application/json"],
            )
            logger.info("✅ Step 3: Mangum handler created successfully")
        except Exception as e:
            logger.error(f"❌ Step 3 FAILED: Could not create Mangum handler")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": '{"error": "Failed to create Mangum handler", "details": "' + str(e) + '"}'
            }

        # Step 4: Call Mangum handler
        try:
            logger.info(f"✅ Step 4: Processing request - Path: {event.get('rawPath', 'unknown')}")
            response = mangum_handler(event, context)
            logger.info(f"✅ Step 5: Request completed successfully")
            return response
        except Exception as e:
            logger.error(f"❌ Step 5 FAILED: Request processing failed")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": '{"error": "Request processing failed", "details": "' + str(e) + '"}'
            }

    except Exception as e:
        # This should never happen, but just in case
        logger.error(f"❌ CRITICAL: Unexpected error in handler")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": '{"error": "Unexpected error", "details": "' + str(e) + '"}'
        }
