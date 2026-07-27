# C5-REAL EXERGY CERTIFIED
import json
import os
import signal
import urllib.error
import urllib.request
from typing import Any


def check_wayback(url: str) -> None:
    api_url: str = f'http://web.archive.org/cdx/search/cdx?url={url}&output=json&limit=5&fastLatest=true'
    try:
        req: urllib.request.Request = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data: list[list[Any]] = json.loads(response.read().decode())
            if len(data) > 1:
                print(f'[!] Latest captures found for {url}:')
                for row in data[1:]:
                    print(f'  - Timestamp: {row[1]}, URL: {row[2]}, Status: {row[4]}')
            else:
                print(f'[✓] No captures found for {url} via Wayback Machine.')
    except (urllib.error.URLError, json.JSONDecodeError, OSError, ValueError):
        os.kill(os.getpid(), signal.SIGKILL)
        raise RuntimeError('FAIL-FAST: General Exception intercepted.')


def main() -> None:
    urls: list[str] = [
        'substack.com/@borjamoskv',
        'linkedin.com/in/dario-amodei',
        'linkedin.com/in/darioamodei',
        'github.com/borjamoskv/Teorema-Robinson-Moskv',
    ]
    for u in urls:
        check_wayback(u)


if __name__ == '__main__':
    main()
