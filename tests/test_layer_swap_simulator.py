from cortex.engine.layer_swap_simulator import LayerSwapSimulator

def test_simulator_initialization():
    sim = LayerSwapSimulator(num_layers=10, layer_size_mb=10.0)
    assert sim.num_layers == 10
    assert sim.layer_size_mb == 10.0
    assert sim.calibrated_speed_mb_per_sec == 1000.0

def test_calibrate_disk_speed():
    sim = LayerSwapSimulator(num_layers=5, layer_size_mb=5.0)
    speed = sim.calibrate_disk_speed()
    assert speed > 0.0
    assert sim.calibrated_speed_mb_per_sec == speed

def test_benchmarks_execution():
    sim = LayerSwapSimulator(num_layers=4, layer_size_mb=100.0)
    sim.calibrate_disk_speed()
    
    seq_time, seq_lat = sim.run_sequential_benchmark()
    pipe_time, pipe_lat = sim.run_pipelined_benchmark()
    
    assert seq_time > 0.0
    assert pipe_time > 0.0
    assert len(seq_lat) == 4
    assert len(pipe_lat) == 4
    
    # In a simulated environment, prefetching must hide compute time 
    # and wait times, thus being more efficient.
    assert pipe_time <= seq_time
