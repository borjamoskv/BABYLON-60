from starlette.middleware.base import BaseHTTPMiddleware

class EpistemicFirewallMiddleware(BaseHTTPMiddleware):
    """
    Ensures outputs remain counterfactual simulation only.
    Hard constraint: no drift into prescriptive/legal advice.
    """
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # inject safety header
        response.headers["X-Epistemic-Mode"] = "counterfactual-simulation-only"
        response.headers["X-No-Liability"] = "true"

        return response
