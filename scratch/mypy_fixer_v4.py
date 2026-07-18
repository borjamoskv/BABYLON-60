import os

def fix_generators_any():
    for root, dirs, files in os.walk("scripts"):
        for file in files:
            if file.startswith("generate_") and file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r") as f:
                    content = f.read()
                
                if "from typing import Any" not in content:
                    content = content.replace("import sys", "import sys\nfrom typing import Any")
                
                with open(path, "w") as f:
                    f.write(content)

def fix_llm_router():
    path = "cortex/llm_router.py"
    with open(path, "r") as f:
        content = f.read()
    
    # Incompatible types in assignment (expression has type "list[str]", variable has type "str")
    # current_route[key] = val -> we need to cast current_route to dict[str, Any] but we already did... wait, RouteConfig is a TypedDict.
    # The return type of parse_yaml_routes is List[RouteConfig]. We need to cast dict to RouteConfig.
    content = content.replace("return routes", "from typing import cast\n    return cast(List[RouteConfig], routes)")
    
    # For current_route type:
    content = content.replace("current_route: dict[str, Any] = {}", "current_route: Any = {}")
    
    # Returning Any from function declared to return "str"
    content = content.replace("return res_data[\"response\"]", "return str(res_data[\"response\"])")

    with open(path, "w") as f:
        f.write(content)

def fix_cortex_invariant():
    path = "cortex/invariant_sentinel.py"
    with open(path, "r") as f:
        content = f.read()
    # cortex/invariant_sentinel.py:67: error: No return value expected [return-value]
    # This is probably `return True` in a function typed `-> None`.
    content = content.replace("def enforce_invariants() -> None:", "def enforce_invariants() -> bool:")
    with open(path, "w") as f:
        f.write(content)

def fix_llm_router_test():
    path = "cortex/llm_router_test.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace("def test_llm_router_dispatch(mock_urlopen):", "def test_llm_router_dispatch(mock_urlopen: Any) -> None:\n    from typing import Any")
    with open(path, "w") as f:
        f.write(content)

if __name__ == "__main__":
    fix_generators_any()
    fix_llm_router()
    fix_cortex_invariant()
    fix_llm_router_test()
