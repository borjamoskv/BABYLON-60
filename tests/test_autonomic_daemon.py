from cortex.agents.autonomic_daemon import AutonomicSwarmDaemon

def test_daemon_initialization():
    daemon = AutonomicSwarmDaemon()
    assert daemon.timestamp is not None
    assert daemon.db_conn is not None

def test_daemon_process_scanning():
    daemon = AutonomicSwarmDaemon()
    proc_data = daemon.scan_processes()
    assert "current_pid" in proc_data
    assert "zombies_count" in proc_data
    assert isinstance(proc_data["zombies_list"], list)

def test_daemon_workspace_checking():
    daemon = AutonomicSwarmDaemon()
    work_data = daemon.check_workspace()
    assert "git_dirty" in work_data
    assert "ast_ok" in work_data
    assert isinstance(work_data["ast_ok"], bool)
