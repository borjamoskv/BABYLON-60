# [C5-REAL] Exergy-Maximized
from babylon60.extensions.scraper.engine import ScraperEngine
from babylon60.extensions.scraper.models import ExtractionStrategy, ScrapeRequest, ScrapeResult

from .models import MarketReport, NicheTarget

try:
    import instructor  # pyright: ignore[reportMissingImports]
    from openai import AsyncOpenAI
except ImportError:
    instructor = None


class NicheArbitrageEngine:
    """Orchestrates scraping and synthesis for Niche Arbitrage."""

    def __init__(self, llm_client=None):
        self.scraper = ScraperEngine()
        self.llm_client = llm_client
        if not self.llm_client and instructor:
            self.llm_client = instructor.from_openai(AsyncOpenAI())

    async def run_pipeline(self, target: NicheTarget) -> MarketReport:
        """Runs the fully autonomous pipeline for a given target."""

        scrape_req = ScrapeRequest(url=target.url, strategy=ExtractionStrategy.AUTO)
        scrape_result: ScrapeResult = await self.scraper.scrape(scrape_req)

        if not scrape_result.success or not scrape_result.markdown:  # type: ignore[type-error]
            return MarketReport(
                target_name=target.name,
                summary=f"FAILED EXTRACTION: {scrape_result.error}",
                signals=[],
            )

        report = await self.synthesize_signals(target.name, scrape_result.markdown)  # type: ignore[type-error]
        return report

    async def synthesize_signals(self, target_name: str, raw_markdown: str) -> MarketReport:
        """Uses structured LLM output to extract market signals with exergy scoring."""
        if not self.llm_client:
            raise RuntimeError("LLM Client not configured for synthesis.")


        system_prompt = (
            "You are a Sovereign Arbitrage Agent analyzing raw web extractions. "
            "Your goal is to extract actionable market inefficiencies, trends, or user complaints "
            "that can be monetized or arbitraged. "
            "Apply thermodynamic rigor: only return signals with high 'exergy' (useful work/value). "
            "Ignore noise, pleasantries, and generic information. "
            "Fill the proposed_arbitrage field with a concrete mechanism to extract value."
        )

        try:
            max_chars = 60000
            content_to_analyze = raw_markdown[:max_chars]

            report = await self.llm_client.chat.completions.create(
                model="gpt-4o",  # Model policy: "high tier"
                response_model=MarketReport,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Analyze this extraction from {target_name}:\n\n{content_to_analyze}",
                    },
                ],
            )

            report.target_name = target_name
            return report

        except (ValueError, TypeError, OSError, KeyError) as e:
            return MarketReport(
                target_name=target_name, summary=f"LLM Synthesis Failed: {str(e)}", signals=[]
            )
