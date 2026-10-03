from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routes import router
from backend.logging_setup import configure_logging, get_logger

configure_logging()
logger = get_logger("app")

app = FastAPI(title="Agentic Order Management Automation", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.exception_handler(Exception)
def unhandled_error(_request: Request, exc: Exception):
    logger.exception("unhandled_error %s", type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred."},
    )


@app.get("/health")
def health():
    return {"status": "ok"}
