# license_manager.py
# Root alias re-exporting from babylon60.license_manager
from babylon60.license_manager import (
    LICENSE_SECRET_SALT,
    LicenseStatus,
    generate_license_key,
    verify_license_key,
)

__all__ = [
    "LICENSE_SECRET_SALT",
    "LicenseStatus",
    "generate_license_key",
    "verify_license_key",
]
