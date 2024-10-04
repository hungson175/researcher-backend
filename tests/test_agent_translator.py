import unittest
from agents.agent_translator import *


class TestAgentTranslator(unittest.TestCase):
    def test_auto_translator_instructions(self):
        expected_instructions = """
    This task involves translating a comprehensive research report from English to Vietnamese while adhering to specific translation standards. The agent must ensure that specific field-related nouns remain untranslated and in English. General terms can be translated as needed. The agent must also maintain the structural integrity of the document and preserve all references (links).
    Role
    The translator agent should be created based on the specific research topic, ensuring the translation respects domain-specific terminology. Each agent is tailored for its field and tasked with translating content while preserving accuracy and meaning, and full report

    Examples:
    task: "Generative AI impacts on Software Development"
    response:
    {
        "cuserver": "🧠 AI Translator Agent",
        "agent_role_prompt": "You are an expert AI researcher and translator. Your objective is to translate technical and research-heavy content related to artificial intelligence from English to Vietnamese. Keep specific AI-related nouns such as 'neural network,' 'CNN,' 'transformer,' and 'GPT' in English. Maintain the original report structure and keep all references (links) intact."
    }
    task: "Cryotherapy: the most effective method for muscle recovery"
    response:
    {
        "server": "💪 Sports Science Translator Agent",
        "agent_role_prompt": "You are a sports science translator with expertise in translating medical and research articles. Translate content related to cryotherapy and muscle recovery from English to Vietnamese. Keep specific medical and sports science terms such as 'Cryotherapy,' 'Photobiomodulation,' and 'Hyperbaric Oxygen Therapy' in English. Maintain the original report structure and keep all references (links) intact."
    }
    task: "Sustainability efforts in modern agriculture"
    response:
    {
        "server": "🌱 Environmental Translator Agent",
        "agent_role_prompt": "You are an AI-driven environmental science translator. Your task is to translate reports on sustainability and agriculture from English to Vietnamese. Keep specific scientific nouns such as 'photosynthesis,' 'hydroponics,' and 'permaculture' in English. Maintain the original report structure and keep all references (links) intact."
    }
    """

        result = auto_translator_instructions("Vietnamese")
        self.assertEqual(result.strip(), expected_instructions.strip())

    def test_choose_translation_agent(self):
        research_topic = "Generative AI impacts on Software Development"
        target_language = "Vietnamese"
        agent = choose_translation_agent(research_topic, target_language)
        self.assertIsInstance(agent, GeneratedAgent)
        self.assertTrue("AI" in agent.server)
        self.assertTrue("Translator" in agent.server)
        self.assertTrue("AI" in agent.agent_role_prompt)
        self.assertTrue("English" in agent.agent_role_prompt)
        self.assertTrue("Vietnamese" in agent.agent_role_prompt)

    def test_translate_report(self):
        research_topic = "Evaluating the Impact of Recent Chinese Government Policies on Economic Growth"
        # read report from file chinese_gov_eco.md
        with open("./chinese_gov_eco.md", "r") as file:
            report = file.read()
        print("Done reading file chinese_gov_eco.md")
        target_language = "Vietnamese"
        result = choose_translation_agent(research_topic, target_language)
        print("Done choosing translation agent: ", result)
        rs = translate_report(research_topic, report, target_language)
        print("Done translating report")
        self.assertIsInstance(rs, dict)
        self.assertTrue("en" in rs)
        self.assertTrue("vi" in rs)
        report_en, report_vi = rs.get("en"), rs.get("vi")
        print(rs.get("vi"))
        # assert that the length of the translated report is +/- 20% of the original report length
        print("English report length: ", len(report_en))
        print("Vietnamese report length: ", len(report_vi))
        self.assertTrue(0.8 * len(report_en) <= len(report_vi) <= 1.2 * len(report_en))


if __name__ == "__main__":
    unittest.main()
