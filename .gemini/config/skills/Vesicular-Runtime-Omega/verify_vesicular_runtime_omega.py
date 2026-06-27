import sys
import json
import yaml
from pathlib import Path

def verify():
    skill_dir = Path(__file__).parent
    
    # 1. Verify SKILL.md
    if not (skill_dir / "SKILL.md").exists():
        sys.exit("SKILL.md missing")
        
    # 2. Verify schema.json
    try:
        with open(skill_dir / "schema.json") as f:
            schema = json.load(f)
            if "intent" not in schema.get("required", []):
                sys.exit("Schema missing intent")
    except Exception as e:
        sys.exit(f"Schema error: {e}")
        
    # 3. Verify policy.yaml
    try:
        with open(skill_dir / "policy.yaml") as f:
            policy = yaml.safe_load(f)
            if "ACTIVE" not in policy.get("states", []):
                sys.exit("Policy missing ACTIVE state")
    except Exception as e:
        sys.exit(f"Policy error: {e}")
        
    # 4. Verify validate_seatbelt_profile invariants
    try:
        sys.path.append(str(skill_dir))
        from scripts.run_vesicular import validate_seatbelt_profile
        
        # Test valid profile
        valid_profile = """(version 1)
(deny default)
(allow file-write* (subpath "/tmp"))"""
        ok, msg = validate_seatbelt_profile(valid_profile)
        if not ok:
            sys.exit(f"Valid profile failed verification: {msg}")
            
        # Test invalid root write
        invalid_profile_1 = """(version 1)
(deny default)
(allow file-write* (subpath "/"))"""
        ok, msg = validate_seatbelt_profile(invalid_profile_1)
        if ok:
            sys.exit("Security gate failed to block root file write")
            
        # Test invalid out of bounds write
        invalid_profile_2 = """(version 1)
(deny default)
(allow file-write* (subpath "/usr/bin"))"""
        ok, msg = validate_seatbelt_profile(invalid_profile_2)
        if ok:
            sys.exit("Security gate failed to block write out of bounds")

        # Test missing default deny
        invalid_profile_3 = """(version 1)
(allow file-write* (subpath "/tmp"))"""
        ok, msg = validate_seatbelt_profile(invalid_profile_3)
        if ok:
            sys.exit("Security gate failed to block missing deny default")

        print("Security gate invariants verified successfully.")
            
    except Exception as e:
        sys.exit(f"Security gate logic test error: {e}")
        
    print("Vesicular-Runtime-Omega: Verification PASS")
    sys.exit(0)

if __name__ == "__main__":
    verify()
