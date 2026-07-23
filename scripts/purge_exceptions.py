import os

def purge_broad_excepts():
    fixes = [
        (
            "babylon60-ide/backend/routes/inference.py",
            "except Exception:",
            "except (urllib.error.URLError, json.JSONDecodeError, OSError, ConnectionError):"
        ),
        (
            "babylon60/extensions/daemon/sync_manager.py",
            "except Exception:  # noqa: BLE001",
            "except (RuntimeError, ValueError, asyncio.TimeoutError, OSError):"
        ),
        (
            "babylon60/extensions/llm/provider.py",
            "except Exception:  # noqa: BLE001",
            "except (UnicodeDecodeError, AttributeError, ValueError):"
        ),
        (
            "babylon60/extensions/swarm/centauro_engine.py",
            "except Exception:  # noqa: BLE001",
            "except (AttributeError, TypeError):"
        ),
        (
            "babylon60/extensions/swarm/sortu_jit_executor.py",
            "except Exception:  # noqa: BLE001",
            "except (OSError, ValueError):"
        ),
        (
            "babylon60/extensions/training/collector.py",
            "except Exception:  # noqa: BLE001",
            "except (TypeError, ValueError):"
        ),
        (
            "babylon60/extensions/training/ttt_engine.py",
            "except Exception:  # noqa: BLE001",
            "except (json.JSONDecodeError, TypeError, ValueError):"
        )
    ]
    for filepath, old, new in fixes:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
            content = content.replace(old, new)
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"Fixed {filepath}")

def main():
    purge_broad_excepts()
    print("Done purging broad excepts.")

if __name__ == "__main__":
    main()
