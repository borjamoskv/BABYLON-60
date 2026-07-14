from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
import jwt
import os
from datetime import datetime

app = FastAPI(
    title="CORTEX Analysis API",
    description="Exposes CORTEX and MOSKV-1 for external AI analysis. [C5-REAL]",
    version="1.0.0",
    docs_url=None, # Custom docs endpoint for the brutalist theme
)

security = HTTPBearer()
JWT_SECRET = os.environ.get("CORTEX_JWT_SECRET", "moskv-c5-real-fallback-secret-2026")

def verify_jwt(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid token - CORTEX Membrane Rejected")

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    css_content = ""
    css_path = os.path.join(os.path.dirname(__file__), "swagger_theme.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            css_content = f"<style>{f.read()}</style>"
            
    return HTMLResponse(
        f"""
        <!DOCTYPE html>
        <html>
        <head>
        <title>CORTEX API docs</title>
        <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css" >
        {css_content}
        </head>
        <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>
            window.onload = function() {{
                const ui = SwaggerUIBundle({{
                    url: '/openapi.json',
                    dom_id: '#swagger-ui',
                }})
            }}
        </script>
        </body>
        </html>
        """
    )

@app.get("/health")
def health_check():
    return {
        "status": "C5-REAL Homeostasis",
        "timestamp": datetime.utcnow().isoformat(),
        "entropy": "purged"
    }

@app.get("/facts")
def get_facts(query: str, payload: dict = Depends(verify_jwt)):
    return {
        "query": query,
        "operator": payload.get("sub", "borjamoskv"),
        "results": [
            {
                "fact": f"CORTEX resolved '{query}' with absolute kinetic collapse.", 
                "confidence": "C5-REAL"
            }
        ]
    }
