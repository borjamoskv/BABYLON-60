# C5-REAL EXERGY CERTIFIED
from setuptools import setup, find_packages

setup(
    name="antigravity-ultrathink",
    version="1.0.0",
    description="MOSKV-1 APEX ULTRATHINK adapter for Google Antigravity SDK with Nodo 4 Skill Routing",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "antigravity-ultrathink=antigravity_ultrathink.cli:main",
        ],
    },
    python_requires=">=3.12",
)
