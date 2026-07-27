import logging

from griptape.drivers import OpenAiChatPromptDriver
from griptape.rules import Rule, Ruleset
from griptape.structures import Agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("recruiter")

class MercorCloneΩ:
    """
    Sovereign Recruitment Screening Engine (Mercor-Clone-Ω).
    Automates the 'Human-Expert-Loop' for multimillionaire-grade workforce scaling.
    """

    def __init__(self):
        self.ruleset = Ruleset(
            name="Mercor-Screening-Protocol",
            rules=[
                Rule("Always evaluate code quality over years of experience."),
                Rule("Identify 'Sovereign Patterns': autodidaction, exergy focus, system-thinking."),
                Rule("Assign a C1-C5 confidence score to every candidate."),
                Rule("Flag candidates with 'High Agency' for immediate escalation.")
            ]
        )
        # Using Griptape Agent structure
        self.screener = Agent(
            rulesets=[self.ruleset],
            prompt_driver=OpenAiChatPromptDriver(model="gpt-4o")
        )

    def screen_candidate(self, resume_text: str, github_handle: str = "") -> str:
        """
        Executes an autonomous screening loop.
        """
        logger.info(f"Screening candidate via Mercor-Clone-Ω (GitHub: {github_handle})")

        _prompt = f"""
        Execute screening on the following candidate data:
        Resume: {resume_text}
        GitHub: {github_handle}

        Output format:
        1. Agency Score (0-100)
        2. Technical Depth (C1-C5)
        3. Recommendation: [ESCALATE | ARCHIVE]
        4. Key Exergy Factor: [Why they are a multimillionaire asset]
        """

        # [C5-REAL] Ignición Determinista del Motor Griptape
        result = self.screener.run(_prompt)
        return result.output.to_text()

if __name__ == "__main__":
    cloner = MercorCloneΩ()
    logging.getLogger(__name__).info(cloner.screen_candidate("PhD in Physics, self-taught Rust dev, build own ETH builder.", "@sovereign_dev"))
