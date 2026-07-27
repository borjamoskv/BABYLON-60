import os
import time
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from babylon60.swarm.tensor_glial import TensorGlialLegion, fast_fading_memory

def test_fast_fading_memory_numpy_fallback():
    # Test the standalone fading memory function
    tensor_view = np.ones((5, 5), dtype=np.float32)
    last_update_ts = np.zeros(5, dtype=np.float64)
    now_ts = 1.0
    lambda_decay = 0.5

    fast_fading_memory(tensor_view, last_update_ts, now_ts, lambda_decay)

    # Check that values decayed
    expected_decay = np.exp(-0.5 * 1.0)
    assert np.allclose(tensor_view, expected_decay)
    assert np.all(last_update_ts == 1.0)

@patch("babylon60.swarm.tensor_glial.VSAEngine")
def test_tensor_glial_init(mock_vsa, tmp_path):
    file_path = str(tmp_path / "tensor.mmap")
    legion = TensorGlialLegion(num_agents=10, d_dim=16, file_path=file_path)

    assert os.path.exists(file_path)
    assert legion.agents_tensor.shape == (10, 16)

    # Reload existing
    legion2 = TensorGlialLegion(num_agents=10, d_dim=16, file_path=file_path)
    assert legion2.agents_tensor.shape == (10, 16)

@patch("babylon60.swarm.tensor_glial.VSAEngine")
def test_tensor_glial_batch_write(mock_vsa, tmp_path):
    file_path = str(tmp_path / "tensor2.mmap")
    legion = TensorGlialLegion(num_agents=10, d_dim=16, file_path=file_path)

    # Override vsa.encode_text for predictable testing
    def mock_encode(text):
        arr = np.zeros(16, dtype=np.float32)
        arr[0] = 1.0
        return arr
    legion.vsa.encode_text = mock_encode

    legion.batch_write_action([0, 1], ["test1", "test2"])

    # Should be normalized
    norm = np.linalg.norm(legion.agents_tensor[0])
    assert np.isclose(norm, 1.0)

@patch("babylon60.swarm.tensor_glial.VSAEngine")
def test_tensor_glial_map_reduce(mock_vsa, tmp_path):
    file_path = str(tmp_path / "tensor3.mmap")
    legion = TensorGlialLegion(num_agents=10, d_dim=16, file_path=file_path)

    # Simple mock for normalize
    legion.vsa.normalize.side_effect = lambda x: x / (np.linalg.norm(x) + 1e-12)

    legion.agents_tensor[0, :] = 1.0
    legion.agents_tensor[1, :] = 2.0

    collapsed = legion.map_reduce_centurion(0, 2)
    assert collapsed.shape == (16,)
    assert np.allclose(collapsed, 3.0 / np.linalg.norm(np.full(16, 3.0)))
