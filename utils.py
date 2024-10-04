import os
import logging
from github import Github
from github import InputFileContent
from pydantic.v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

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


def escape_curly_braces(input):
    if isinstance(input, list):
        return [escape_curly_braces(i) for i in input]
    if isinstance(input, dict):
        return {k: escape_curly_braces(v) for k, v in input.items()}
    if isinstance(input, str):
        return input.replace("{", "{{").replace("}", "}}")
    raise ValueError(f"Unsupported type: {type(input)}")


def gen_mock_report() -> str:
    # return the content of file ./tests/chinese_gov_eco.md
    with open("./tests/chinese_gov_eco.md", "r") as file:
        return file.read()
