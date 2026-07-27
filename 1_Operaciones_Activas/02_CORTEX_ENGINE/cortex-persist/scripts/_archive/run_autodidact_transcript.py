import asyncio
import json
import logging

from babylon60.extensions.skills.autodidact.synthesis import execute_cognitive_synthesis

logging.basicConfig(level=logging.INFO)


async def main():
    try:
        # 1. Caracterizar el Payload Textual
        with open("/tmp/transcript_es.json") as f:
            data = json.load(f)

        # Flatten structure: might be [[{text:...},...]] or {video_id: [{text:...},...]}
        if isinstance(data, dict):
            # Try to get the first value
            blocks = list(data.values())[0] if len(data) > 0 else []
        elif isinstance(data, list):
            # Flatten if it's a list of lists
            blocks = []
            for item in data:
                if isinstance(item, list):
                    blocks.extend(item)
                else:
                    blocks.append(item)
        else:
            logging.getLogger(__name__).info("Unknown transcript format.")
            return

        text_payload = " ".join([item.get("text", "") for item in blocks if isinstance(item, dict)])

        if len(text_payload) < 20:
            logging.getLogger(__name__).info("Transcript too small or invalid.")
            return

        logging.getLogger(__name__).info(f"Transcript Length: {len(text_payload)} caracteres.")

        # 2. Cristalizar (Autodidact-Ω)
        target_url = "https://www.youtube.com/watch?v=9r2DwV5KwTc"
        intent = "audio_ingest"

        logging.getLogger(__name__).info("Enviando a execute_cognitive_synthesis...")
        memo_id = await execute_cognitive_synthesis(
            raw_data=text_payload, source=target_url, force=True, intent=intent
        )
        logging.getLogger(__name__).info(f"ASIMILADO SOBERANO: {memo_id}")
    except Exception as e:  # noqa: BLE001
        logging.getLogger(__name__).info(f"ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(main())
