import sys
import os
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel

# Inject core path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.middleware import EpistemicFirewallMiddleware
from fas_phase2_core import JurisprudenceState
from fas_digital_twin import DigitalTwinJurisprudentialEngine
from api.database import User, UsageLog, get_db

app = FastAPI(
    title="CORTEX-FAS Regulatory Dynamics Engine",
    description="Interpretative Risk Simulator for Legal Systems Under Stress. STRICTLY COUNTERFACTUAL.",
    version="6.0.0"
)

# Apply Epistemic Firewall
app.add_middleware(EpistemicFirewallMiddleware)

# Integrate Stripe Webhook Router
from api.webhook_handler import router as stripe_router
app.include_router(stripe_router)

# Models
class OutputContract(BaseModel):
    mode: str
    epistemic_status: str
    regime: str
    metrics: dict
    interpretation: str

class UserCreate(BaseModel):
    email: str

class StressTestInput(BaseModel):
    preset: str = "default"

# Dependency: API Key Authentication & Limit Verification
def verify_api_key(x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")
    db = get_db()
    try:
        user = db.query(User).filter(User.api_key == x_api_key).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid API Key")
        if user.requests_used >= user.requests_limit:
            raise HTTPException(status_code=402, detail="Payment Required: Request limit exceeded")
        return user
    finally:
        db.close()

# Routes
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": "6.0.0",
        "epistemic_mode": "counterfactual_only"
    }

@app.post("/users")
def create_user(user_in: UserCreate):
    db = get_db()
    try:
        user = db.query(User).filter(User.email == user_in.email).first()
        if not user:
            import secrets
            api_key = secrets.token_hex(32)
            user = User(
                email=user_in.email,
                api_key=api_key,
                tier="free",
                requests_limit=10,
                requests_used=0,
                activated_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return {"api_key": user.api_key, "tier": user.tier}
    finally:
        db.close()

@app.get("/usage")
def get_usage(user: User = Depends(verify_api_key)):
    return {
        "tier": user.tier,
        "requests_limit": user.requests_limit,
        "requests_used": user.requests_used
    }

@app.post("/stress_test", response_model=OutputContract)
def run_stress_test(input_data: StressTestInput = None, user: User = Depends(verify_api_key)):
    """
    Executes a baseline synthetic stress test using the JEF and Lyapunov engines.
    """
    if input_data is None:
        input_data = StressTestInput()

    state = JurisprudenceState()
    
    if input_data.preset == "strict_compliance":
        state.drift_vector["art13_lgt_strength"] = 0.90
        state.drift_vector["donation_skepticism"] = 0.90
    else:
        state.drift_vector["art13_lgt_strength"] = 0.50
        state.drift_vector["donation_skepticism"] = 0.50
    
    twin = DigitalTwinJurisprudentialEngine(state)
    db = get_db()
    try:
        analysis = twin.analyze_full()
        
        # Log to usage_logs
        log = UsageLog(
            user_id=user.id,
            endpoint="/stress_test",
            energy_score=analysis["energy"]["E_total"],
            lyapunov=analysis["lyapunov"]["lambda"],
            regime=analysis["regime"]
        )
        db.add(log)
        
        # Update user usage count and last seen timestamp
        db.query(User).filter(User.id == user.id).update({
            "requests_used": User.requests_used + 1,
            "last_request_at": datetime.utcnow()
        })
        
        db.commit()
        
        return OutputContract(
            mode="adversarial_stress_simulation",
            epistemic_status="counterfactual_only",
            regime=analysis["regime"],
            metrics={
                "energy": analysis["energy"]["E_total"],
                "lyapunov": analysis["lyapunov"]["lambda"],
                "flip_probability": analysis["lyapunov"]["flip_probability"]
            },
            interpretation="sensitivity to assumption perturbation calculated"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/analyze")
def analyze_state(user: User = Depends(verify_api_key)):
    return run_stress_test(StressTestInput(), user)

@app.get("/regime")
def get_regime(user: User = Depends(verify_api_key)):
    res = run_stress_test(StressTestInput(), user)
    return {"regime": res.regime, "epistemic_status": res.epistemic_status}

@app.get("/lyapunov")
def get_lyapunov(user: User = Depends(verify_api_key)):
    res = run_stress_test(StressTestInput(), user)
    return {"lyapunov": res.metrics["lyapunov"], "epistemic_status": res.epistemic_status}
