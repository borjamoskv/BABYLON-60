#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 Sovereign Hardened
# █ INSTAGRAM GRAPH API CLIENT | DOMAIN: channels.instagram | STATE: C5-REAL
# ============================================================================
"""
Official Meta Graph API Client for Instagram Business/Creator Accounts (@babylon60.ai).
Enforces fail-closed token verification, dry-run simulations, and error diagnostics.
Zero web scraping / zero headless browser automation.
"""

from dataclasses import dataclass
import json
import os
from typing import cast, Any, Dict, List, Optional
import urllib.parse
import urllib.request
import urllib.error


GRAPH_API_VERSION = "v21.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


@dataclass(frozen=True)
class InstagramPublishResult:
    """Rigid response of media container creation and publishing."""
    success: bool
    media_id: Optional[str]
    container_id: Optional[str]
    permalink: Optional[str]
    error_message: Optional[str] = None
    is_simulation: bool = False


class InstagramGraphClient:
    """
    Official Meta Graph API Client for Instagram.
    Publishes images, carousels, and reels to @babylon60.ai safely.
    """

    def __init__(
        self,
        account_id: Optional[str] = None,
        access_token: Optional[str] = None,
    ):
        self.account_id = account_id or os.environ.get("INSTAGRAM_ACCOUNT_ID", "")
        self.access_token = access_token or os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")

    def is_configured(self) -> bool:
        """Checks whether the client has credentials loaded."""
        return bool(self.account_id and self.access_token)

    def _request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Internal helper for Graph API HTTP calls with json decoding."""
        if not self.is_configured():
            raise RuntimeError("Instagram Graph API no está configurado (faltan INSTAGRAM_ACCOUNT_ID o INSTAGRAM_ACCESS_TOKEN).")

        query_params = params or {}
        query_params["access_token"] = self.access_token
        url = f"{GRAPH_API_BASE}/{endpoint.lstrip('/')}?{urllib.parse.urlencode(query_params)}"

        req_data = None
        headers = {"User-Agent": "BABYLON-60-SocialAgent/1.0"}
        if data:
            req_data = urllib.parse.urlencode(data).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"

        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return cast(Dict[str, Any], json.loads(resp.read().decode("utf-8")))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            try:
                err_json = json.loads(err_body)
                msg = err_json.get("error", {}).get("message", err_body)
            except Exception:
                msg = err_body
            raise RuntimeError(f"Meta Graph API Error ({e.code}): {msg}")

    def get_account_profile(self) -> Dict[str, Any]:
        """Retrieves profile info: username, biography, followers, media count."""
        if not self.is_configured():
            return {
                "account_id": self.account_id or "UNCONFIGURED",
                "username": "babylon60.ai",
                "status": "offline_simulation",
                "followers_count": 0,
                "media_count": 0,
            }
        return self._request(
            f"{self.account_id}",
            params={"fields": "id,username,name,biography,followers_count,media_count"},
        )

    def create_single_image_container(self, image_url: str, caption: str) -> str:
        """Creates an IG Container for a single image."""
        resp = self._request(
            f"{self.account_id}/media",
            method="POST",
            data={"image_url": image_url, "caption": caption},
        )
        return cast(str, resp["id"])

    def create_carousel_item_container(self, image_url: str) -> str:
        """Creates an individual child container for a multi-slide carousel."""
        resp = self._request(
            f"{self.account_id}/media",
            method="POST",
            data={"image_url": image_url, "is_carousel_item": "true"},
        )
        return cast(str, resp["id"])

    def create_carousel_container(self, children_ids: List[str], caption: str) -> str:
        """Creates the parent carousel container linking all child slides."""
        resp = self._request(
            f"{self.account_id}/media",
            method="POST",
            data={
                "media_type": "CAROUSEL",
                "children": ",".join(children_ids),
                "caption": caption,
            },
        )
        return cast(str, resp["id"])

    def publish_container(self, container_id: str) -> str:
        """Publishes an already created IG media container."""
        resp = self._request(
            f"{self.account_id}/media_publish",
            method="POST",
            data={"creation_id": container_id},
        )
        return cast(str, resp["id"])

    def simulate_carousel_publication(
        self,
        image_urls: List[str],
        caption: str,
    ) -> InstagramPublishResult:
        """
        Simulates the carousel publishing pipeline for verification or staging.
        Does not touch live Meta APIs.
        """
        simulated_children = [f"sim_container_child_{i:02d}" for i in range(1, len(image_urls) + 1)]
        simulated_parent = f"sim_container_carousel_{len(image_urls)}slides"
        simulated_media_id = "sim_media_published_17841400099"

        return InstagramPublishResult(
            success=True,
            media_id=simulated_media_id,
            container_id=simulated_parent,
            permalink=f"https://www.instagram.com/p/{simulated_media_id}/",
            is_simulation=True,
        )
