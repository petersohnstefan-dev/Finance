"""Single source of truth for where the project's data files live.

Every module used to build its own path to ../data, which meant a test run could
not be pointed anywhere else: importing PortfolioManager alone was enough to
touch the live portfolio.db, and a sandboxed dry run still wrote to the real
files. Set FINANCE_DATA_DIR to redirect the whole application - see
tools/sandbox_run.py, which uses exactly that to run any script against a
throwaway copy.
"""
import os

_DEFAULT_DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))

DATA_DIR = os.path.abspath(os.environ.get("FINANCE_DATA_DIR") or _DEFAULT_DATA_DIR)

#: True when the application is running against a redirected data directory.
IS_SANDBOXED = DATA_DIR != _DEFAULT_DATA_DIR


def data_file(name: str) -> str:
    """Absolute path to a file inside the active data directory."""
    return os.path.join(DATA_DIR, name)


def ensure_data_dir() -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    return DATA_DIR
