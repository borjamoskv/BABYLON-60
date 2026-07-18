import os
import re

def fix_llm_router():
    path = "cortex/llm_router.py"
    with open(path, "r") as f:
        content = f.read()
    
    # fix dict
    content = content.replace("current_route: RouteConfig = {}", "current_route: dict[str, Any] = {}")
    # add Any to imports
    content = content.replace("from typing import List, TypedDict", "from typing import List, TypedDict, Any")
    
    # fix get models
    content = content.replace("actual_model = route.get(\"models\")[0] if route.get(\"models\") else \"llama3-70b-8192\"", 
                              "models = route.get(\"models\", [])\n                    actual_model = models[0] if models else \"llama3-70b-8192\"")
    content = content.replace("actual_model = route.get(\"models\")[0] if route.get(\"models\") else \"Llama-3-8B-Instruct\"",
                              "models = route.get(\"models\", [])\n                    actual_model = models[0] if models else \"Llama-3-8B-Instruct\"")
    
    # fix call openai
    content = content.replace("res_data[\"choices\"][0][\"message\"][\"content\"]", "str(res_data[\"choices\"][0][\"message\"][\"content\"])")
    
    # fix call ollama str | None
    content = content.replace("return self._call_ollama(route.get(\"url\"), model, prompt)", "return self._call_ollama(str(route.get(\"url\", \"\")), model, prompt)")

    with open(path, "w") as f:
        f.write(content)

def fix_bft_orchestrator():
    path = "cortex/bft_orchestrator.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace("return bft_consensus", "return int(bft_consensus)")
    with open(path, "w") as f:
        f.write(content)

def fix_tests():
    for f in ["cortex/bft_orchestrator_test.py", "cortex/llm_router_test.py"]:
        with open(f, "r") as file:
            content = file.read()
        content = content.replace("def run_test():", "def run_test() -> None:")
        content = content.replace("def setUp(self):", "def setUp(self) -> None:")
        content = content.replace("def tearDown(self):", "def tearDown(self) -> None:")
        with open(f, "w") as file:
            file.write(content)

def fix_generators():
    for root, dirs, files in os.walk("scripts"):
        for file in files:
            if file.startswith("generate_") and file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r") as f:
                    content = f.read()
                
                # fix definition missing types
                content = re.sub(r'def ([a-zA-Z0-9_]+)\(([^)]+)\) -> None:', r'def \1(\2) -> Any:', content)
                content = content.replace("import os", "import os\nimport sys\nsys.path.append(os.path.dirname(os.path.dirname(__file__)))")
                with open(path, "w") as f:
                    f.write(content)

if __name__ == "__main__":
    fix_llm_router()
    fix_bft_orchestrator()
    fix_tests()
    fix_generators()
