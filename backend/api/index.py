"""
Minimal health endpoint for Vercel serverless deployment.

This is a simplified version that will work in Lambda without
heavy dependencies. We'll expand functionality incrementally.
"""

import json
from datetime import datetime


def handler(event, context):
    """
    Lambda handler for health check endpoint.

    This minimal version avoids database connectivity and heavy imports
    to establish that basic serverless execution works.
    """

    # Parse the event path to route requests
    path = event.get('path', '/')

    # Handle different routes
    if path == '/health' or path == '/api/health':
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'status': 'healthy',
                'message': 'ResuMate API is running',
                'version': '1.0.0-minimal',
                'environment': 'production',
                'timestamp': datetime.utcnow().isoformat(),
                'note': 'Database connectivity will be added in next iteration'
            })
        }

    # Handle OPTIONS for CORS
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            },
            'body': ''
        }

    # 404 for unknown paths
    return {
        'statusCode': 404,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps({
            'error': 'Not Found',
            'message': f'Path {path} not found',
            'available_paths': ['/health', '/api/health']
        })
    }
