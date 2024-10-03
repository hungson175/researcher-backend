import os
import logging
from github import Github
from github import InputFileContent
from pydantic.v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence

from customized_prompts import auto_translator_instructions
from dotenv import load_dotenv
import utils

load_dotenv()

async def upload_to_github_gist(content: str, filename: str = "report.md") -> dict:
    try:
        github_token = os.getenv("GITHUB_ACCESS_TOKEN")
        if not github_token:
            logging.error("GitHub access token is not set")
            return {
                "success": False,
                "message": "GitHub access token is not configured",
                "published_url": ""
            }

        # Initialize Github instance with your access token
        g = Github(github_token)
        
        # Create a new gist
        gist = g.get_user().create_gist(
            public=True,
            files={filename: InputFileContent(content)},
            description="Generated Report"
        )
        
        logging.info(f"Gist created successfully: {gist.html_url}")
        return {
            "success": True,
            "message": "",
            "published_url": gist.html_url
        }
    except Exception as e:
        logging.error(f"Error creating gist: {str(e)}")
        return {
            "success": False,
            "message": str(e),
            "published_url": ""
        }

class GeneratedAgent(BaseModel):
    server: str = Field(description="The server that conducts the research.")
    agent_role_prompt: str = Field(description="The role of the server in the research.")

def choose_translation_agent(research_topic: str, target_language: str = "Vietnamese") -> GeneratedAgent:
    system_prompt = auto_translator_instructions(target_language)
    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", "{query}"),
        ]
    )
    llm = ChatOpenAI(model=os.getenv("SMART_LLM_MODEL"), temperature=0.15)
    structured_llm = llm.with_structured_output(GeneratedAgent)

    chain: RunnableSequence = prompt_template | structured_llm
    return chain.invoke({"query": research_topic})


def generate_file_name(query: str):
    system_prompt = """Given the query, your task is to generate a file name for the report using 3-5 words.
    Expected output: The output file name WITHOUT extension.

    Examples:
        query: The Impact of Substances on Creativity and Innovation Throughout History
        output: impact_substances_creativity_innovation_history

        query: How does the brain process information?
        output: brain_process_information

        query: What is the impact of AI on the job market?
        output: impact_ai_job_market
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{query}")
    ])

    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.15)
    chain = prompt | llm
    return chain.invoke({"query": query})

def gen_report_file_names(query: str):
    file_prefix = generate_file_name(query)
    english_file_name = file_prefix.content + "_en.md"
    vietnamese_file_name = file_prefix.content + "_vi.md"
    return english_file_name, vietnamese_file_name

def translate_report(topic: str,report: str, target_language: str = "Vietnamese"):
    translator_role_data: GeneratedAgent = choose_translation_agent(topic, target_language)
    llm = ChatOpenAI(model_name=os.getenv("SMART_LLM_MODEL"), temperature=0.15)
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", utils.escape_curly_braces(translator_role_data.agent_role_prompt)),
        ("human", "{report}")
    ])
    translator = prompt_template | llm
    result = translator.invoke(input={"report": report})
    return {
        "en": report,
        "vi": result.content
    }
    
def escape_curly_braces(input):
    if isinstance(input, list):
        return [escape_curly_braces(i) for i in input]
    if isinstance(input, dict):
        return {k: escape_curly_braces(v) for k, v in input.items()}
    if isinstance(input, str):
        return input.replace("{", "{{").replace("}", "}}")
    raise ValueError(f"Unsupported type: {type(input)}")