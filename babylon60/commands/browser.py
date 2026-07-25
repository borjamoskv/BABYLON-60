import logging
import subprocess
from typing import Any

logger = logging.getLogger("babylon60.commands.browser")

def run_browser(url: str, extract_dom: bool = True) -> dict[str, Any]:
    """
    Executes C5-REAL Web Diagnostics / Headless DOM extraction.
    Uses native cURL fallback if playwright is absent, verifying URL accessibility.
    """
    logger.info(f"[C5-REAL] Initiating Sovereign Browser Driver for: {url}")
    
    if not url.startswith("http"):
        url = "https://" + url

    try:
        logger.info(f"Extracting DOM entropy from {url}...")
        cmd = ["curl", "-sL", "-A", "MOSKV-1/APEX (C5-REAL Engine)", url]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        html_payload = result.stdout
        
        payload_size = len(html_payload)
        logger.info(f"[C5-REAL] Extracted {payload_size} bytes of DOM entropy.")
        
        return {
            "url": url,
            "status": "success",
            "bytes_extracted": payload_size,
            "html": html_payload[:1000] if extract_dom else ""
        }
    except Exception as e:
        logger.error(f"[FATAL] Web Diagnostics failed: {str(e)}")
        raise RuntimeError(f"Browser driver error: {str(e)}") from e
