import os
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableSequence
from langchain_core.prompts import ChatPromptTemplate
from pydantic.v1 import BaseModel, Field

import utils
import dotenv

dotenv.load_dotenv()


class GeneratedAgent(BaseModel):
    server: str = Field(description="The server that conducts the research.")
    agent_role_prompt: str = Field(description="The role of the server in the research.")


def auto_translator_instructions(target_language: str):
    return f"""
    This task involves translating a comprehensive research report from English to {target_language} while adhering to specific translation standards. The agent must ensure that specific field-related nouns remain untranslated and in English. General terms can be translated as needed. The agent must also maintain the structural integrity of the document and preserve all references (links).
    Role
    The translator agent should be created based on the specific research topic, ensuring the translation respects domain-specific terminology. Each agent is tailored for its field and tasked with translating content while preserving accuracy and meaning, and full report

    Examples:
    task: "Generative AI impacts on Software Development"
    response:
    {{
        "cuserver": "🧠 AI Translator Agent",
        "agent_role_prompt": "You are an expert AI researcher and translator. Your objective is to translate technical and research-heavy content related to artificial intelligence from English to {target_language}. Keep specific AI-related nouns such as 'neural network,' 'CNN,' 'transformer,' and 'GPT' in English. Maintain the original report structure and keep all references (links) intact."
    }}
    task: "Cryotherapy: the most effective method for muscle recovery"
    response:
    {{
        "server": "💪 Sports Science Translator Agent",
        "agent_role_prompt": "You are a sports science translator with expertise in translating medical and research articles. Translate content related to cryotherapy and muscle recovery from English to {target_language}. Keep specific medical and sports science terms such as 'Cryotherapy,' 'Photobiomodulation,' and 'Hyperbaric Oxygen Therapy' in English. Maintain the original report structure and keep all references (links) intact."
    }}
    task: "Sustainability efforts in modern agriculture"
    response:
    {{
        "server": "🌱 Environmental Translator Agent",
        "agent_role_prompt": "You are an AI-driven environmental science translator. Your task is to translate reports on sustainability and agriculture from English to {target_language}. Keep specific scientific nouns such as 'photosynthesis,' 'hydroponics,' and 'permaculture' in English. Maintain the original report structure and keep all references (links) intact."
    }}
    """


def choose_translation_agent(research_topic: str, target_language: str = "Vietnamese") -> GeneratedAgent:
    system_prompt = auto_translator_instructions(target_language)
    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", utils.escape_curly_braces(system_prompt)),
            ("user", "{query}"),
        ]
    )
    llm = ChatOpenAI(model=os.getenv("SMART_LLM_MODEL"), temperature=0.15)
    structured_llm = llm.with_structured_output(GeneratedAgent)

    chain: RunnableSequence = prompt_template | structured_llm
    return chain.invoke({"query": research_topic})


def translate_report(topic: str, report: str, target_language: str = "Vietnamese"):
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
