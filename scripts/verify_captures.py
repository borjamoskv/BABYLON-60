#!/usr/bin/env python3
import urllib.request
import json

def check_wayback(url):
    # Fetch the latest 5 captures from Wayback Machine
    api_url = f"http://web.archive.org/cdx/search/cdx?url={url}&output=json&limit=5&fastLatest=true"
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if len(data) > 1:
                print(f"[!] Latest captures found for {url}:")
                for row in data[1:]:
                    print(f"  - Timestamp: {row[1]}, URL: {row[2]}, Status: {row[4]}")
            else:
                print(f"[✓] No captures found for {url} via Wayback Machine.")
    except Exception as e:
        print(f"Error checking {url}: {e}")

if __name__ == "__main__":
    urls = [
        "substack.com/@borjamoskv",
        "linkedin.com/in/dario-amodei",
        "linkedin.com/in/darioamodei",
        "github.com/borjamoskv/Teorema-Robinson-Moskv"
    ]
    for u in urls:
        check_wayback(u)
