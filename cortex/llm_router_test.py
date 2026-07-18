import unittest
from unittest.mock import patch, MagicMock
import json
from cortex.llm_router import parse_yaml_routes, C5LLMRouter, EpistemicHalt

class TestLLMRouter(unittest.TestCase):
    def test_parse_yaml_routes(self):
        # Validar el parseador sin dependencias contra el archivo real de la ontología
        routes = parse_yaml_routes("cortex/ontology/llms_gratuitos_front_routes.yaml")
        self.assertGreater(len(routes), 0)
        self.assertEqual(routes[0]["name"], "GitHub Models")
        self.assertIn("Gemma-2-9B-It", routes[0]["models"])

    @patch('urllib.request.urlopen')
    def test_dispatch_inference_ollama_success(self, mock_urlopen):
        # Mock de respuesta JSON de Ollama local
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"response": "Respuesta simulada de Ollama"}).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        router = C5LLMRouter()
        # deepseek-r1:8b es un modelo local registrado
        res = router.dispatch_inference("Test prompt", "deepseek-r1:8b")
        self.assertEqual(res, "Respuesta simulada de Ollama")

if __name__ == '__main__':
    unittest.main()
