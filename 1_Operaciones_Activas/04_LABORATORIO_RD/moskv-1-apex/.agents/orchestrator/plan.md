# Moskv-1 Project Plan

This document outlines the step-by-step plan for building the sellable product "Moskv-1" from scratch with a robust, test-driven Python architecture.

## Milestones

### Milestone 1: Exploration and System Design
- **Objective**: Discover workspace parameters, identify any existing files, determine the design of the "Moskv-1" Python system, and outline code structure.
- **Verification**: Handoff report from the Explorer detailing the target structure, module design, and environment strategy.

### Milestone 2: Environment Setup & Symlink
- **Objective**: Set up a local Python virtual environment (`.venv`) adhering to the C5-REAL `managing-python-dependencies` protocol, and establish a symlink or mapping to `~/teamwork_projects/moskv_1` if needed.
- **Verification**: Verification command runs `python3 -m venv` and checks for virtual env isolation, packages, and symlink health.

### Milestone 3: Core Scaffolding & Module Implementation
- **Objective**: Create the foundational directory structure and write the core Python modules (e.g., event bus, cognitive region, and memory graph interfaces).
- **Verification**: Core imports work, structure matches specification, and unit tests run.

### Milestone 4: Test Suite & Continuous Verification
- **Objective**: Implement a robust test suite using `pytest`. Verify all core functions have 100% test coverage and run without crashing.
- **Verification**: Reviewer passes and Challenger confirms correctness. Auditor attests to clean C5-REAL execution.

## Coordination Registry
- Parent: c805a751-1ac5-488a-a638-d14d773a3864 (Sentinel)
- Successor: TBD
