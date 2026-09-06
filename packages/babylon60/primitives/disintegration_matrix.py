"""
Bayesian Disintegration Module.
Strict C5-REAL Structural Invariants.
"""

TOL = 1e-12

def support(dist: dict) -> set:
    """
    supp(μ) = {i : μ[i] > TOL}
    Returns the support of a probability distribution.
    """
    return {k for k, v in dist.items() if v > TOL}

def pushforward(p: dict, F: dict) -> dict:
    """
    q = f_* p
    Calculates the pushforward distribution q(y) = Σ_x p(x) * F[x,y].
    """
    q: dict[str, float] = {}
    p_supp = support(p)
    for x in p_supp:
        px = p[x]
        Fx = F.get(x, {})
        for y, Fxy in Fx.items():
            if Fxy > 0:
                q[y] = q.get(y, 0.0) + px * Fxy
    return q

def disintegrate(p: dict, F: dict, y) -> dict:
    """
    f†_p(y)(x) = p(x)·F[x,y] / Σ_x' p(x')·F[x',y]
    Computes the posterior distribution.
    Enforces strict structural invariants.
    """
    q = pushforward(p, F)
    qy = q.get(y, 0.0)
    
    if qy <= TOL:
        raise ValueError(f"hallucinated: observation '{y}' outside pushforward support (q(y)=0).")
        
    posterior = {}
    p_supp = support(p)
    
    # Iterate strictly over prior support to ensure invariant mechanically
    for x in p_supp:
        px = p[x]
        Fx = F.get(x, {})
        Fxy = Fx.get(y, 0.0)
        
        numerator = px * Fxy
        if numerator > 0:
            posterior[x] = numerator / qy
            
    # Explicit invariant check: posterior support ⊆ prior support
    post_supp = support(posterior)
    if not post_supp.issubset(p_supp):
        raise ValueError("hallucinated: posterior assigns mass outside prior support.")
        
    return posterior

def disintegration_matrix(p: dict, F: dict, strict: bool = True) -> dict:
    """
    Returns the full kernel D: Y → X.
    D[y][x] = posterior for observation y.
    Normalizes row by row (each y defines a valid distribution over x).
    """
    q = pushforward(p, F)
    q_supp = support(q)
    
    D = {}
    for y in q_supp:
        try:
            D[y] = disintegrate(p, F, y)
        except ValueError:
            if strict:
                raise
    return D

def verify_symmetry(p: dict, F: dict, D: dict, tol: float = 1e-6) -> bool:
    """
    Verifies the Joint Probability Symmetry (AX-BD-1):
    p ⊗ f = (p·f) ⊗ f†_p
    """
    q = pushforward(p, F)
    
    for x, px in p.items():
        for y, Fxy in F.get(x, {}).items():
            joint_left = px * Fxy
            
            qy = q.get(y, 0.0)
            Dyx = D.get(y, {}).get(x, 0.0)
            joint_right = qy * Dyx
            
            if abs(joint_left - joint_right) > tol:
                return False
    return True
