from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class DomainError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.message})

    try:
        from app.rag.core.exceptions import AppError as RagAppError
    except Exception:
        RagAppError = None

    if RagAppError is not None:
        @app.exception_handler(RagAppError)
        async def rag_error_handler(_: Request, exc: RagAppError) -> JSONResponse:
            return JSONResponse(status_code=exc.status_code, content={"error": exc.message})

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else None
        message = "Invalid request"
        if first:
            field = ".".join(str(part) for part in first.get("loc", []) if part != "body")
            if field:
                message = f"Invalid {field}"
            elif first.get("msg"):
                message = str(first["msg"])
        return JSONResponse(status_code=400, content={"error": message})

    @app.exception_handler(HTTPException)
    async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
