from fastapi import Request, Response
from kitchen_commons.shared.Correlation import (
    get_correlation_id, 
    set_correlation_id, 
    generate_correlation_id
)
from kitchen_commons.shared.Logging import logger

async def correlation_middleware(request: Request, call_next):
    
    # Extract from header or generate new
    corr_id = request.headers.get('X-Correlation-ID')
    
    if not corr_id:
        corr_id = generate_correlation_id()
        logger.info("Generated new correlation ID", 
                   path=request.url.path,
                   method=request.method)
    else:
        logger.info("Received correlation ID from header",
                   path=request.url.path,
                   method=request.method)
    
    # Set in context for this request
    set_correlation_id(corr_id)
    
    # Process request
    response: Response = await call_next(request)
    
    # Add to response headers
    response.headers['X-Correlation-ID'] = corr_id
    
    return response