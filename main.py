from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
# importing cros origin resource
from fastapi.middleware.cors import CORSMiddleware
import torch
import uvicorn
from pydantic import BaseModel
from src.utils import setup_logger, process_response

from src.language_chain import MedicalChatbot

logging = setup_logger(__name__, 'logs/main.log')
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

origins = [
    "http://localhost:8000",
    "http://localhost:8080",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

medical_chatbot = MedicalChatbot()  # Initialize once at startup

class UserText(BaseModel):
    message: str

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={'message': 'Hello World!'}, media_type="text/html"
    )

@app.post('/api/chat')
async def chat_bot(usertext: UserText):
    logging.info('received the request {}'.format(usertext.message))
    response = medical_chatbot.answer_question(usertext.message)
    logging.info('response {}'.format(response))
    processed_response = process_response(response)
    return {'response': processed_response}

@app.on_event("shutdown")
async def shutdown_event():
    # Clean up resources
    if medical_chatbot.llm:
        del medical_chatbot.llm.model
        torch.cuda.empty_cache()

if __name__=="__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True, workers=3)
