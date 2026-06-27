# C5-REAL
import urllib.request, json, websocket, argparse

def run_cdp(target: str, js: str) -> None:
    try:
        with urllib.request.urlopen("http://localhost:9222/json") as r:
            targets = json.loads(r.read().decode())
    except Exception as e:
        print(f"ERR_CONN: {e}")
        return

    t = next((t for t in targets if target.lower() in t.get("url", "").lower() or target.lower() in t.get("title", "").lower()), None)
    if not t or not t.get("webSocketDebuggerUrl"):
        print(f"ERR_TARGET_WS: {target}")
        return

    ws = websocket.create_connection(t["webSocketDebuggerUrl"], suppress_origin=True)
    ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
    ws.recv()
    ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))

    while True:
        res = json.loads(ws.recv())
        if res.get("id") == 2:
            print(res.get("result", {}).get("result", {}).get("value", ""))
            break

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--url_match", required=True)
    p.add_argument("--js", required=True)
    args = p.parse_args()
    run_cdp(args.url_match, args.js)
