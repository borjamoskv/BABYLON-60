import sys
from unittest.mock import AsyncMock, MagicMock

# Mock third-party dependencies that are missing in the global python environment
nats_mock = MagicMock()
nats_mock.connect = AsyncMock()

nats_js_mock = MagicMock()

sys.modules['nats'] = nats_mock
sys.modules['nats.js'] = nats_js_mock

neo4j_mock = MagicMock()
neo4j_mock.AsyncGraphDatabase = MagicMock()
sys.modules['neo4j'] = neo4j_mock
