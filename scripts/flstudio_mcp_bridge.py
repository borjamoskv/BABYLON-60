#!/usr/bin/env python3
"""
Antigravity MCP Bridge for FL Studio 21+
Connects Python AI Logic to FL Studio via CoreMIDI Virtual Ports and Mido.
"""

import sys
import time
import os
from typing import Dict, List, Optional
import mido

class FLStudioMCPBridge:
    def __init__(self, port_name: str = "Antigravity MCP Out"):
        self.port_name = port_name
        self.outport = None
        self._init_port()

    def _init_port(self):
        try:
            self.outport = mido.open_output(self.port_name, virtual=True)
            print(f"[MCP Bridge] Virtual MIDI Output Port active: '{self.port_name}'")
        except Exception as e:
            print(f"[MCP Bridge] Failed to open virtual port: {e}")

    def set_mixer_volume(self, track_id: int, volume: float):
        """
        Sets volume for FL Studio mixer track_id (0-125).
        volume is a float from 0.0 (silent) to 1.0 (0 dB / 100%).
        """
        if not self.outport:
            return
        track_id = max(0, min(125, int(track_id)))
        vol_byte = max(0, min(127, int(volume * 127)))
        # Send CC 10: data1 = track_id, data2 = vol_byte
        msg = mido.Message('control_change', channel=15, control=10, value=vol_byte)
        # Note: we embed track_id in pitch/control byte via protocol
        msg_track = mido.Message('control_change', channel=15, control=track_id, value=vol_byte)
        self.outport.send(msg_track)
        print(f"[MCP Bridge] Track {track_id} Volume -> {volume:.2f} (Byte: {vol_byte})")

    def set_mixer_pan(self, track_id: int, pan: float):
        """
        Sets panning for FL Studio mixer track_id.
        pan ranges from -1.0 (Left) to 1.0 (Right), 0.0 = Center.
        """
        if not self.outport:
            return
        track_id = max(0, min(125, int(track_id)))
        pan_byte = max(0, min(127, int((pan + 1.0) * 63.5)))
        msg = mido.Message('control_change', channel=15, control=11, value=pan_byte)
        self.outport.send(msg)
        print(f"[MCP Bridge] Track {track_id} Pan -> {pan:.2f}")

    def set_mute(self, track_id: int, mute: bool):
        if not self.outport:
            return
        val = 127 if mute else 0
        msg = mido.Message('control_change', channel=15, control=12, value=val)
        self.outport.send(msg)
        print(f"[MCP Bridge] Track {track_id} Mute -> {mute}")

    def set_solo(self, track_id: int, solo: bool):
        if not self.outport:
            return
        val = 127 if solo else 0
        msg = mido.Message('control_change', channel=15, control=13, value=val)
        self.outport.send(msg)
        print(f"[MCP Bridge] Track {track_id} Solo -> {solo}")

    def transport_play(self):
        if not self.outport:
            return
        msg = mido.Message('control_change', channel=15, control=14, value=1)
        self.outport.send(msg)
        print("[MCP Bridge] Transport -> PLAY/PAUSE")

    def transport_stop(self):
        if not self.outport:
            return
        msg = mido.Message('control_change', channel=15, control=14, value=2)
        self.outport.send(msg)
        print("[MCP Bridge] Transport -> STOP")

    def set_bpm(self, bpm: int):
        if not self.outport:
            return
        val = max(0, min(127, bpm - 60))
        msg = mido.Message('control_change', channel=15, control=15, value=val)
        self.outport.send(msg)
        print(f"[MCP Bridge] Set BPM -> {bpm}")

    def close(self):
        if self.outport:
            self.outport.close()
            print("[MCP Bridge] Closed MIDI port")


# Stem Mapping Protocol for "No Lo Entiende" (116 BPM, C Minor)
NO_LO_ENTIENDE_STEMS = {
    1: {"name": "No Lo Entiende 2-unai kiks selections.wav", "role": "Kick/Sub", "gain_db": 0.0, "pan": 0.0},
    2: {"name": "No Lo Entiende LOW END.wav", "role": "Sub Bass", "gain_db": -2.0, "pan": 0.0},
    3: {"name": "No Lo Entiende bass.wav", "role": "Bassline", "gain_db": -1.5, "pan": 0.0},
    4: {"name": "No Lo Entiende claps.wav", "role": "Claps", "gain_db": -3.0, "pan": 0.0},
    5: {"name": "No Lo Entiende SHAKERS.wav", "role": "Shakers 1", "gain_db": -6.0, "pan": -0.25},
    6: {"name": "No Lo Entiende SHAKER2.wav", "role": "Shakers 2", "gain_db": -6.0, "pan": 0.25},
    7: {"name": "No Lo Entiende top loop.wav", "role": "Top Loop", "gain_db": -4.0, "pan": 0.0},
    8: {"name": "No Lo Entiende SINTE PRIN.wav", "role": "Main Synth", "gain_db": -3.5, "pan": 0.0},
    9: {"name": "No Lo Entiende DUB SINT.wav", "role": "Dub Synth 1", "gain_db": -5.0, "pan": -0.4},
    10: {"name": "No Lo Entiende DUB SINT 2.wav", "role": "Dub Synth 2", "gain_db": -5.0, "pan": 0.4},
    11: {"name": "No Lo Entiende 11-Other - Teddy Pendergrass.wav", "role": "Teddy Sample", "gain_db": -4.0, "pan": 0.0},
    12: {"name": "Vocal Lead / Spoken Word", "role": "Lead Vocal", "gain_db": 0.0, "pan": 0.0},
}

def print_stem_routing_plan():
    print("=" * 70)
    print("  FL STUDIO MIXER ROUTING PLAN: 'No Lo Entiende' (116 BPM - Cmin)")
    print("=" * 70)
    for ch, info in NO_LO_ENTIENDE_STEMS.items():
        print(f"  Track {ch:02d} | Role: {info['role']:<15} | Gain: {info['gain_db']:+5.1f} dB | Pan: {info['pan']:+4.2f} | {info['name']}")
    print("=" * 70)

if __name__ == "__main__":
    print_stem_routing_plan()
    bridge = FLStudioMCPBridge()
    bridge.set_bpm(116)
    time.sleep(0.5)
    bridge.close()
