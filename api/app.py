import logging

from fastapi import FastAPI, Request
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware


# For seeing the requests going to the api from the frontend
class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        body = await request.body()
        response = await call_next(request)

        logging.info(f"Request: {request.method} {request.url}")
        logging.info(f"Headers: {dict(request.headers)}")
        logging.info(f"Body: {body.decode('utf-8')}")
        logging.info(f"Response Status Code: {response.status_code}")

        return response


# Initialize FastAPI app
logging.basicConfig(level=logging.INFO)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health") # Get Health of API
async def health_check():
    return {"status": "healthy"}