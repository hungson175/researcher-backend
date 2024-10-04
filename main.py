import os
import dotenv
from fastapi import FastAPI, HTTPException, WebSocket
from pydantic.v1 import BaseModel, Field
from supabase import create_client, Client
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate, \
    SystemMessagePromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from backend.report_type import DetailedReport
from fastapi.middleware.cors import CORSMiddleware

import logging
import asyncio

import agents
from agents.agent_translator import translate_report
from utils import upload_to_github_gist
import utils

app = FastAPI()
dotenv.load_dotenv()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://researcher-frontend.vercel.app"],
    # Replace with your React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase credentials
supabase: Client = create_client(
    os.getenv("PUBLIC_SUPABASE_URL"),
    os.getenv("PUBLIC_SUPABASE_ANON_KEY")
)

system_prompt = ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template(
            "you are a helpful assistant"
        ),
        # The `variable_name` here is what must align with memory
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{question}")
    ]
)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)  # Chat model , not completion
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
conversation = LLMChain(
    llm=llm,
    prompt=system_prompt,
    verbose=True,
    memory=memory,
)


class Message(BaseModel):
    input: str


class ReportRequest(BaseModel):
    query: str
    report_type: str = "research_report"
    report_source: str = "web_search"
    # tone: Tone = Tone.FORMAL
    # subtopics: list = []


@app.post("/chat")
async def generate_text(request: Message):
    try:
        # Use the chain with history to generate text
        response = conversation.invoke({"question": request.input})
        return {"generated_text": response["text"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/genreport")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        data = await websocket.receive_json()
        request = ReportRequest(**data)

        # Uncomment the following line to use the mock implementation
        # response = await mock_report_generation(websocket, request)

        detailed_report = DetailedReport(
            query=request.query,
            report_type=request.report_type,
            report_source=request.report_source,
            source_urls=[],
            config_path=None,
            websocket=websocket,
            subtopics=[]
        )

        final_report = await detailed_report.run()
        await websocket.send_text(final_report)

        # Upload the report to GitHub Gist

        report = translate_report(request.query,final_report, "Vietnamese")
        (english_file_name, vietnamese_file_name) = utils.gen_report_file_names(request.query)
        upload_result_en = await upload_to_github_gist(report["en"], english_file_name)
        upload_result_vi = await upload_to_github_gist(report["vi"], vietnamese_file_name)

        logging.info(f"Upload result English: {upload_result_en}")
        logging.info(f"Upload result Vietnamese: {upload_result_vi}")

        response = {
            "success": upload_result_en["success"] and upload_result_vi["success"],
            "message": upload_result_en["message"],
            "en_content": report["en"],
            "vi_content": report["vi"],
            "published_url_en": upload_result_en["published_url"],
            "published_url_vi": upload_result_vi["published_url"]
        }

        await websocket.send_json(response)

    except Exception as e:
        logging.error(f"Error in websocket endpoint: {str(e)}")
        await websocket.send_json({
            "success": False,
            "message": str(e),
            "en_content": "",
            "vi_content": "",
            "published_url_en": "",
            "published_url_vi": ""
        })
    finally:
        await websocket.close()


@app.post("/genreport")
async def generate_report(request: ReportRequest):
    try:
        detailed_report = DetailedReport(
            query=request.query,
            report_type=request.report_type,
            report_source=request.report_source,
            source_urls=[],
            config_path=None,
            websocket=None,
            subtopics=[]
        )

        final_report = await detailed_report.run()
        return {"report": final_report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def mock_report_generation(websocket: WebSocket, request: ReportRequest):
    await asyncio.sleep(1)  # Simulate some processing time
    await websocket.send_text("Initiating research process...")
    await asyncio.sleep(1)

    mock_report = utils.gen_mock_report()
    print("Mock report generated: ", mock_report)

    for line in mock_report.split('\n'):
        await websocket.send_text(line)
        await asyncio.sleep(0.1)  # Simulate gradual report generation

    en_content = mock_report
    vi_content = translate_report(en_content, "Vietnamese")
    mock_gist_en = await upload_to_github_gist(en_content, "en.md")
    mock_gist_vi = await upload_to_github_gist(vi_content, "vi.md")
    if mock_gist_en["success"] and mock_gist_vi["success"]:
        return {
            "success": True,
            "message": "Reports uploaded successfully",
            "en_content": en_content,
            "vi_content": vi_content,
            "published_url_en": mock_gist_en["published_url"],
            "published_url_vi": mock_gist_vi["published_url"]
        }
    else:
        return {
            "success": False,
            "message": "Failed to upload reports",
            "en_content": "",
            "vi_content": "",
            "published_url_en": "",
            "published_url_vi": ""
        }
