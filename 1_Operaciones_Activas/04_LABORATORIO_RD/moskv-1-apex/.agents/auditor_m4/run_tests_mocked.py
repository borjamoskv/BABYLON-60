import sys
import os
from unittest.mock import MagicMock

# Add src to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Mock external modules
sys.modules['nats'] = MagicMock()
sys.modules['nats.js'] = MagicMock()
sys.modules['neo4j'] = MagicMock()

import pytest
# Run pytest programmatically
if __name__ == '__main__':
    sys.exit(pytest.main(["-v", "tests/"]))
