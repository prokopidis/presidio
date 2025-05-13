# app.py

"""REST API server for anonymizer."""
import json
import logging
import os
from logging.config import fileConfig
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from presidio_anonymizer import AnonymizerEngine, DeanonymizeEngine
from presidio_anonymizer.entities import InvalidParamError
from presidio_anonymizer.services.app_entities_convertor import AppEntitiesConvertor
from ilsp_athenarc_asep_anonymizer.pii_anonymizer import PiiAnonymizer
import regex as re
from typing import Dict, List, Optional
from pydantic import BaseModel
from ilsp_athenarc_asep_anonymizer.celery import run_anonymization, celery
from celery.result import AsyncResult

DEFAULT_PORT = 3000
LOGGING_CONF_FILE = "logging.ini"

WELCOME_MESSAGE = r"""
#######################################################
# Welcome to the ILSP ATHENARC ASEP Anonymizer API
#######################################################
"""


class AnonymizeRequest(BaseModel):
    """
    Anonymize request data.
    
    :param text: the text to analyze
    :param language: the language of the text
    :param entities: List of PII entities that should be looked for in the text. If entities=None then all entities are looked for.
    :param score_threshold: A minimum value for which to return an identified entity
    :param log_decision_process: Should the decision points within the analysis be logged
    :param return_decision_process: Should the decision points within the analysis returned as part of the response
    :param allow_list: List of strings to be ignored during analysis.
    """
    text: Optional[str] = None
    language: Optional[str] = "el"
    entities: Optional[List[str]] = ['PERSON', 'PHONE_NUMBER', 'EMAIL_ADDRESS']
    score_threshold: Optional[float] = None
    return_decision_process: Optional[bool] = None
    allow_list: Optional[List[str]] = None
    # ad_hoc_recognizers: Optional[List[Dict]] = None  # Keeping as Dict for simplicity, can be a custom Pydantic model if needed
    # context: Optional[Dict[str, str]] = None
    # :param ad_hoc_recognizers: List of ad-hoc recognizer dictionaries.
    # :param context: Contextual information for analysis.
    # allow_list_match: str = "exact"
    #: param allow_list_match: Matching strategy for the allow list ('exact' or 'regex').
    # regex_flags: int = re.DOTALL | re.MULTILINE | re.IGNORECASE
    # :param regex_flags: Regex flags to be used for pattern recognizers.
    # :param correlation_id: cross call ID for this request
    # correlation_id: Optional[str] = None


class Server:
    """FastAPI server for the anonymizer."""

    def __init__(self):
        fileConfig(Path(Path(__file__).parent, LOGGING_CONF_FILE))
        self.logger = logging.getLogger("ilsp-athenarc-asep-anonymizer")
        self.logger.setLevel(os.environ.get("LOG_LEVEL", self.logger.level))
        self.app = FastAPI()
        self.logger.info("Starting anonymizer engine")
        self.anonymizer = PiiAnonymizer()
        self.logger.info(WELCOME_MESSAGE)

        @self.app.get("/health")
        async def health() -> str:
            """Return basic health probe result."""
            return "Presidio Anonymizer service is up"

        @self.app.post("/anonymize")
        async def anonymize(request: AnonymizeRequest) -> Response:
            self.logger.debug(request)
            if not request.text:
                raise Exception("No text provided")

            self.logger.info(
                f'Received anonymization request for text:\n\n'
                f'{request.text if len(request.text) < 4 * 80 else request.text[:4 * 80 - 3] + "..."}'
            )

            anonymization_id = run_anonymization.delay(request.text).id

            return Response(
                content=json.dumps({"anonymization_id": anonymization_id}), media_type="application/json"
            )

        @self.app.get("/anonymize/{anonymization_id}")
        async def get_anonymization(anonymization_id) -> Response:
            task_result = AsyncResult(anonymization_id, app=celery)

            return Response(content=json.dumps({
                "anonymization_id": anonymization_id,
                "status": task_result.status,
                "result": json.loads(task_result.result) if task_result.ready() else None
            }, ensure_ascii=False), media_type="application/json")

        @self.app.exception_handler(InvalidParamError)
        async def invalid_param_exception_handler(
                request: Request, exc: InvalidParamError
        ):
            self.logger.warning(
                f"Request failed with parameter validation error: {exc.err_msg}"
            )
            return Response(
                content=jsonable_encoder({"error": exc.err_msg}),
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                media_type="application/json",
            )

        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            return Response(
                content=jsonable_encoder({"error": exc.detail}),
                status_code=exc.status_code,
                media_type="application/json",
            )

        @self.app.exception_handler(Exception)
        async def server_error_exception_handler(request: Request, exc: Exception):
            self.logger.error(f"A fatal error occurred during execution: {exc}")
            return Response(
                content=jsonable_encoder({"error": "Internal server error"}),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                media_type="application/json",
            )


def create_app():
    server = Server()
    return server.app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", DEFAULT_PORT))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = FastAPI()
# anonymizer = PiiAnonymizer()


# class AnonymizeRequest(BaseModel):
#     text: str
#     analyzer_results: dict = None
#     operators: dict = None


# class AnonymizeResponse(BaseModel):
#     anonymized_text: str
#     items: list


# @app.post("/anonymize", response_model=AnonymizeResponse)
# async def anonymize_endpoint(request: AnonymizeRequest):
#     """
#     Endpoint to anonymize text using the PiiAnonymizer.
#     """
#     try:
#         result = anonymizer.anonymize(
#             text=request.text,
#             analyzer_results=request.analyzer_results,
#             operators=request.operators,
#         )
#         logger.info(f"Anonymized text: {result.text}")
#         logger.info(f"Anonymization items: {result.items}")
#         return AnonymizeResponse(anonymized_text=result.text, items=result.items)
#     except Exception as e:
#         logger.error(f"Error during anonymization: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# if __name__ == "__main__":
#     import uvicorn
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--host", type=str, default="0.0.0.0", help="Host address")
#     parser.add_argument("--port", type=int, default=8000, help="Port number")
#     args = parser.parse_args()
#     uvicorn.run(app, host=args.host, port=args.port)
