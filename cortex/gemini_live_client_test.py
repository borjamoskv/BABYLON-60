# C5-REAL EXERGY CERTIFIED
"""Unit tests for cortex.gemini_live_client (C5-REAL)."""

import pytest
from cortex.gemini_live_client import (
    AudioFormatMismatchError,
    AudioStreamConfig,
    GeminiLiveClient,
)

class TestAudioStreamConfig:
    def test_default_config_valid(self) -> None:
        config = AudioStreamConfig()
        assert config.input_sample_rate == 16000
        assert config.output_sample_rate == 24000
        assert config.channels == 1
        assert config.bit_depth == 16

    def test_invalid_input_sample_rate_raises(self) -> None:
        with pytest.raises(AudioFormatMismatchError, match="Input sample rate MUST be 16000"):
            AudioStreamConfig(input_sample_rate=44100)

    def test_invalid_output_sample_rate_raises(self) -> None:
        with pytest.raises(AudioFormatMismatchError, match="Output sample rate MUST be 24000"):
            AudioStreamConfig(output_sample_rate=48000)

    def test_invalid_channels_raises(self) -> None:
        with pytest.raises(AudioFormatMismatchError, match="Audio channels MUST be 1"):
            AudioStreamConfig(channels=2)

    def test_invalid_bit_depth_raises(self) -> None:
        with pytest.raises(AudioFormatMismatchError, match="Bit depth MUST be 16"):
            AudioStreamConfig(bit_depth=24)

class TestGeminiLiveClient:
    def test_create_session_success(self) -> None:
        client = GeminiLiveClient(api_key="test_key_123")
        session = client.create_session("sess_01")
        assert session.session_id == "sess_01"
        assert session.is_active is True
        assert session.cortex_taint.startswith("CORTEX-TAINT:borjamoskv:gemini_live:")

    def test_create_empty_session_id_raises(self) -> None:
        client = GeminiLiveClient(api_key="test_key_123")
        with pytest.raises(ValueError, match="session_id cannot be empty"):
            client.create_session("")

    def test_barge_in_purges_buffer(self) -> None:
        client = GeminiLiveClient(api_key="test_key_123")
        session = client.create_session("sess_barge")
        session.buffer_bytes = b"sample_pcm_audio_stream_data_12345"

        purged = client.process_barge_in("sess_barge")
        assert purged == len(b"sample_pcm_audio_stream_data_12345")
        assert session.buffer_bytes == b""

    def test_barge_in_invalid_session_raises(self) -> None:
        client = GeminiLiveClient()
        with pytest.raises(KeyError, match="Session invalid_id not found"):
            client.process_barge_in("invalid_id")

    def test_generate_websocket_url_ephemeral(self) -> None:
        client = GeminiLiveClient(api_key="test_key_123")
        client.create_session("sess_wss")
        url = client.generate_websocket_url("sess_wss", use_ephemeral_token=True)
        assert "generativelanguage.googleapis.com" in url
        assert "key=eph_" in url
        assert "version=v1alpha" in url

    def test_generate_websocket_url_direct(self) -> None:
        client = GeminiLiveClient(api_key="test_key_123")
        client.create_session("sess_wss_direct")
        url = client.generate_websocket_url("sess_wss_direct", use_ephemeral_token=False)
        assert "key=test_key_123" in url
