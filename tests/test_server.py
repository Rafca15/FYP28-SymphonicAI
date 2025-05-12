import queue
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from server import start_server


def test_server_reusability():
    q = queue.Queue()
    server1 = start_server(q, "127.0.0.1", 8001)
    server2 = start_server(q, "127.0.0.1", 8001)
    assert server1 is server2
