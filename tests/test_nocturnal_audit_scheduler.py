import pytest
from scripts.nocturnal_audit_scheduler import execute_audit_iteration

def test_nocturnal_audit_single_iteration():
    result = execute_audit_iteration(iteration_num=1)
    assert result["status"] == "SUCCESS"
    assert result["planes_passed"] == 5
