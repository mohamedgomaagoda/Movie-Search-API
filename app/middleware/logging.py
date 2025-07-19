from fastapi import Request
import logging
import time
import json
from typing import Callable
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

async def logging_middleware(request: Request, call_next: Callable):
    start_time = time.time()
    
    # Log request
    logger.info(f"Request started: {request.method} {request.url}")
    if request.query_params:
        logger.info(f"Query params: {dict(request.query_params)}")
    
    try:
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Request completed: {request.method} {request.url} "
            f"- Status: {response.status_code} "
            f"- Processing Time: {process_time:.3f}s"
        )
        
        return response
    except Exception as e:
        # Log error
        logger.error(
            f"Request failed: {request.method} {request.url} "
            f"- Error: {str(e)}"
        )
        raise 