#!/usr/bin/env python3
import json
import sys
import os
import glob
from pathlib import Path

def get_historical_anergy_threshold() -> float:
    """
    Computes dynamic historical threshold based on past transcripts to enforce continuous improvement.
    Fallback to 1000 if no data is found.
    """
    brains_path = os.path.expanduser("~/.gemini/antigravity/brain/*/.system_generated/logs/transcript.jsonl")
    transcripts = glob.glob(brains_path)
    if not transcripts:
        return 1000.0
        
    # As a baseline for C5-REAL, we force a continuous 5% optimization pressure 
    # over the static baseline if transcripts exist. A full I/O scan here is heavy, 
    # so we mock the regression calculation based on the count of past sessions.
    baseline = 1000.0
    optimization_pressure = min(0.50, len(transcripts) * 0.01) # Max 50% tighter
    return baseline * (1.0 - optimization_pressure)


def calculate_exergy(transcript_path: str):
    """
    Thermodynamic Context Parser for MOSKV-1 APEX
    Calculates the generation of entropy (anergy) vs useful structural mutations.
    """
    if not os.path.exists(transcript_path):
        print(f"Error: Transcript not found at {transcript_path}")
        sys.exit(1)

    total_steps = 0
    user_inputs = 0
    model_responses = 0
    tool_calls = 0
    total_content_length = 0
    
    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                step = json.loads(line)
                total_steps += 1
                step_type = step.get("type", "")
                content = step.get("content", "")
                
                if step_type == "USER_INPUT":
                    user_inputs += 1
                elif step_type in ("PLANNER_RESPONSE", "MODEL_RESPONSE"):
                    model_responses += 1
                    total_content_length += len(content)
                    if step.get("tool_calls"):
                        tool_calls += len(step.get("tool_calls"))
            except json.JSONDecodeError:
                continue
                
    # Basic Heuristic: Low Exergy = High narrative content vs low tool usage.
    # We define anergy roughly as the length of text generated per tool call.
    anergy_ratio = total_content_length / (tool_calls if tool_calls > 0 else 1)
    
    dynamic_threshold = get_historical_anergy_threshold()
    
    print("=== MOSKV-1 EXERGY SENSOR ===")
    print(f"Transcript Path: {transcript_path}")
    print(f"Total Steps: {total_steps}")
    print(f"User Inputs: {user_inputs}")
    print(f"Model Responses: {model_responses}")
    print(f"Tool Executions (Mutations): {tool_calls}")
    print(f"Total Cognitive Volume (Chars): {total_content_length}")
    print("-----------------------------")
    print(f"Thermodynamic Friction (Anergy Ratio): {anergy_ratio:.2f} chars/tool")
    print(f"Dynamic Threshold (Continuous Optimization): {dynamic_threshold:.2f}")
    
    if anergy_ratio > dynamic_threshold:
        print(f"[!] ALERTA: Baja Exergía. Demasiada prosa por cada mutación estructural (Umbral: {dynamic_threshold:.2f}).")
    else:
        print("[✓] ESTADO: Alta Densidad Exergética. Operación Turbo.")


def ingest_mac_maestro_ndjson(log_path: str):
    """
    Ingests structural logs from Mac-Maestro physical UI mutations.
    """
    if not os.path.exists(log_path):
        return 0
    mutations = 0
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                if event.get("action") == "mutation":
                    mutations += 1
            except json.JSONDecodeError:
                pass
    return mutations

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 exergy_sensor.py <path_to_transcript.jsonl>")
        sys.exit(1)
    calculate_exergy(sys.argv[1])
