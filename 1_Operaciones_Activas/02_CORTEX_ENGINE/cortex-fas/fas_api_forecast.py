#!/usr/bin/env python3
"""
FAS v16 — Doctrinal Weather Forecast API
Reality level: C5-REAL
Aesthetics: Industrial Noir 2026

Exposes the FAS engine via a REST API to query litigation temperature and doctrinal weather forecasts.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
from datetime import datetime

from fas_phase2_core import (
    JurisprudenceState, CaseNode, Jurisdiction, EconomicEvent, JudicialInference
)
from fas_energy_physics import JuridicalPhysicsEngine
from fas_lyapunov_chaos import LyapunovProxyEngine

app = FastAPI(
    title="CORTEX Doctrinal Weather Forecast",
    description="API for Litigation Temperature Index and Jurisprudential Risk Surface.",
    version="1.0.0"
)

# Global State Singleton for the API
global_state = JurisprudenceState()

class StructureInput(BaseModel):
    sector: str
    economic_events: List[str]  # e.g., ["payment_fixed_amount", "tight_temporal_coupling"]

class ForecastResponse(BaseModel):
    regime: str
    temperature_index: float  # E_total equivalent
    phase_transition: str
    dominant_attractor: str
    risk_surface: Dict[str, float]

@app.post("/forecast", response_model=ForecastResponse)
async def analyze_structure(input_data: StructureInput):
    """
    Evaluates a specific business structure against the current jurisprudential energy field.
    Returns the "Litigation Temperature Index".
    """
    try:
        # 1. Parse Economic Events from request
        parsed_events = []
        for e_str in input_data.economic_events:
            try:
                parsed_events.append(EconomicEvent(e_str))
            except ValueError:
                pass # Ignore invalid events for pure simulation
        
        # 2. Simulate the structure being evaluated as a potential case
        # (This calculates how this specific structure would stress the current thresholds)
        temp_case = CaseNode(
            case_id=f"SIM-{input_data.sector}-{datetime.now().timestamp()}",
            jurisdiction=Jurisdiction.AEAT, # Start at lowest jurisdiction
            date=datetime.now(),
            source_type="simulation",
            events_economic=parsed_events,
            events_inference=[], # Left empty, physics engine will infer based on pressure
            events_system=[]
        )
        
        # We don't append it to history permanently, just check the state
        physics = JuridicalPhysicsEngine(global_state)
        analysis = physics.analyze()
        
        # Risk surface calculation based on drift
        risk_surface = {
            "reclassification_risk (art.13)": analysis["drift_vector"].get("art13_lgt_strength", 0.0),
            "simulation_risk (art.16)": analysis["drift_vector"].get("art16_lgt_expansion", 0.0),
            "burden_shift_risk": analysis["drift_vector"].get("burden_shift_intensity", 0.0),
        }
        
        return ForecastResponse(
            regime=analysis["regime"],
            temperature_index=analysis["energy"]["E_total"],
            phase_transition=analysis["phase_transition"],
            dominant_attractor=analysis["dominant_attractor"],
            risk_surface=risk_surface
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class LyapunovInput(BaseModel):
    epsilon_events: List[str]

class LyapunovResponse(BaseModel):
    lyapunov_lambda: float
    regime: str
    interpretation: str
    risk_level: str

@app.post("/lyapunov/analyze", response_model=LyapunovResponse)
async def analyze_chaos(input_data: LyapunovInput):
    try:
        parsed_events = []
        for e_str in input_data.epsilon_events:
            try:
                parsed_events.append(EconomicEvent(e_str))
            except ValueError:
                pass
                
        eps_case = CaseNode(
            case_id=f"EPSILON-{datetime.now().timestamp()}",
            jurisdiction=Jurisdiction.AEAT,
            date=datetime.now(),
            source_type="simulation",
            events_economic=parsed_events,
            events_inference=[],
            events_system=[]
        )
        
        lyapunov_engine = LyapunovProxyEngine(global_state)
        res = lyapunov_engine.analyze_chaos([eps_case])
        
        return LyapunovResponse(
            lyapunov_lambda=res["lyapunov_lambda"],
            regime=res["regime"],
            interpretation=res["interpretation"],
            risk_level=res["risk_level"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_system_status():
    """Returns the macro-state of the Jurisprudence Engine."""
    physics = JuridicalPhysicsEngine(global_state)
    return physics.analyze()

if __name__ == "__main__":
    print("[CORTEX] Doctrinal Weather Forecast API Initializing...")
    print("[CORTEX] Binding to 0.0.0.0:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
