# babylon60/premium_features/ha_cluster.py
# Execution Protocol: Premium Feature - High Availability Zero-Copy Clustering
# Validates Enterprise tier before allowing instantiation.

from license_sovereign_validator import verify_license_key, LicenseStatus
try:
    import strike_rs
except ImportError:
    strike_rs = None

class HighAvailabilityCluster:
    def __init__(self, license_key: str | None = None, service_name: str = "b60_hypervisor"):
        self.license_status: LicenseStatus = verify_license_key(license_key)
        self._enforce_enterprise_tier()
        
        # Initialize zero-copy shared memory via strike_rs ABFT Hypervisor
        self.service_name = service_name
        if strike_rs is not None and hasattr(strike_rs, "AgencyHypervisor"):
            self.hypervisor = strike_rs.AgencyHypervisor(service_name)
            self.is_active = True
        else:
            self.hypervisor = None
            self.is_active = False

    def _enforce_enterprise_tier(self) -> None:
        if self.license_status.tier not in ("enterprise",):
            raise PermissionError(
                "Fail-fast: High Availability Clustering is an Enterprise feature. "
                f"Current tier: {self.license_status.tier.upper()}. "
                "Upgrade to ENTERPRISE for zero-copy replication."
            )

    def publish_node(self, node_id: str, payload_hash: str) -> None:
        """Publishes a BFT node to the Zero-Copy IPC bus."""
        assert self.is_active
        self.hypervisor.publish_node(payload_hash)
        
    @staticmethod
    def start_hypervisor_daemon(db_path: str, service_name: str = "b60_hypervisor") -> None:
        """Starts the Rust Single-Writer daemon draining the shared memory."""
        if strike_rs is None or not hasattr(strike_rs, "AgencyHypervisor"):
            raise NotImplementedError("strike_rs extension missing or crashed on import")
        strike_rs.AgencyHypervisor.start_writer_daemon(service_name, db_path)
