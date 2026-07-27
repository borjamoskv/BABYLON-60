# C5-REAL EXERGY CERTIFIED
from setuptools import setup, find_packages

setup(
    name="claude-ultrathink",
    version="1.0.0",
    description="C5-REAL Ultrathink P0 Bridge for Claude Code",
    author="borjamoskv",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "c5-claude=claude_ultrathink.cli:main",
        ],
    },
)
