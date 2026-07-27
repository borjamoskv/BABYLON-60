import logging
import asyncio

from babylon60.engine import CortexEngine


async def main():
    engine = CortexEngine(db_path="test_assurance_crash.db")
    logging.getLogger(__name__).info("Type of engine.ledger_writer:", type(engine.ledger_writer))


if __name__ == "__main__":
    asyncio.run(main())
