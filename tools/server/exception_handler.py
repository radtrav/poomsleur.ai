import traceback
from http import HTTPStatus

from fastapi import HTTPException
from fastapi.responses import JSONResponse


class ExceptionHandler:

    async def http_exception_handler(self, exc: HTTPException):
        return JSONResponse(
            dict(
                statusCode=exc.status_code,
                message=exc.detail,
                error=HTTPStatus(exc.status_code).phrase,
            ),
            status_code=exc.status_code,
            headers=exc.headers,
        )

    async def other_exception_handler(self, exc: Exception):
        traceback.print_exc()

        status = HTTPStatus.INTERNAL_SERVER_ERROR
        return JSONResponse(
            dict(statusCode=status, message=str(exc), error=status.phrase),
            status,
        )
