# C5-REAL EXERGY CERTIFIED
import unittest
from unittest.mock import patch, MagicMock
from ultrathink.adapters.kimi_adapter import KimiAdapter

class TestKimiAdapter(unittest.TestCase):

    @patch('os.environ.get')
    def test_missing_api_key(self, mock_env):
        mock_env.return_value = None
        with self.assertRaises(ValueError) as context:
            KimiAdapter()
        self.assertIn("MOONSHOT_API_KEY no encontrada", str(context.exception))

    def test_invalid_reasoning_effort(self):
        adapter = KimiAdapter(api_key="mock_key")
        with self.assertRaises(ValueError) as context:
            adapter.execute_transduction([{"role": "user", "content": "test"}], reasoning_effort="insane")
        self.assertIn("Violación de Ω202", str(context.exception))

    @patch('urllib.request.urlopen')
    def test_successful_transduction(self, mock_urlopen):
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"choices": [{"message": {"content": "Colapso exitoso"}}]}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        adapter = KimiAdapter(api_key="mock_key")
        result = adapter.execute_transduction([{"role": "user", "content": "ping"}], reasoning_effort="low")

        self.assertEqual(result["choices"][0]["message"]["content"], "Colapso exitoso")

if __name__ == '__main__':
    unittest.main()
