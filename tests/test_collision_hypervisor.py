# C5-REAL EXERGY CERTIFIED
"""Unit tests for cortex.hypervisor.collision CollisionPrimitive."""

import pytest
from cortex.hypervisor.collision import CollisionPrimitive


def test_collision_detection():
    primitive = CollisionPrimitive(arena_bounds=(0, 10))
    positions = [(1, 2), (3, 4), (1, 2), (5, 6)]
    collisions = primitive.detect_collision(positions)
    assert collisions == [(1, 2)]


def test_collision_resolution():
    primitive = CollisionPrimitive(arena_bounds=(0, 10))
    positions = [(1, 2), (1, 2), (5, 6)]
    resolved = primitive.resolve_collision(positions)
    assert resolved == [(1, 2), (2, 2), (5, 6)]


def test_no_collision():
    primitive = CollisionPrimitive(arena_bounds=(0, 10))
    positions = [(1, 2), (3, 4), (5, 6)]
    collisions = primitive.detect_collision(positions)
    assert collisions == []
    resolved = primitive.resolve_collision(positions)
    assert resolved == [(1, 2), (3, 4), (5, 6)]
