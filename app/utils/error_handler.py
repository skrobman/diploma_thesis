import logging
from functools import wraps
from fastapi import HTTPException
from sqlalchemy.exc import OperationalError
from starlette.status import HTTP_504_GATEWAY_TIMEOUT, HTTP_500_INTERNAL_SERVER_ERROR

logger = logging.getLogger(__name__)

def handle_db_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)

        except HTTPException as e:
            raise e

        except OperationalError as e:
            logger.warning(f"Database timeout or connection error in {func.__name__}: {e}")
            raise HTTPException(
                status_code=HTTP_504_GATEWAY_TIMEOUT,
                detail="Service is temporarily overloaded."
            )

        except Exception as e:
            logger.exception(f"An unexpected error occurred in {func.__name__}: {e}")
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An internal server error occurred."
            )

    return wrapper