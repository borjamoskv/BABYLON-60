import urllib.request
import json
import os
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

dois = {
    "PolyUnpack_2006": "10.1109/ACSAC.2006.38",
    "OmniUnpack_2007": "10.1109/ACSAC.2007.46",
    "Ether_2008": "10.1145/1455770.1455780"
}

os.makedirs("papers/unpacking", exist_ok=True)

for name, doi in dois.items():
    url = f"https://api.crossref.org/works/{doi}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            oa_loc = data.get("message", {}).get("resource", {}).get("primary")
            if oa_loc and oa_loc.get("URL"):
                pdf_url = oa_loc["URL"]
                print(f"Downloading {name} from {pdf_url}...")
                
                req_pdf = urllib.request.Request(pdf_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req_pdf) as pdf_resp:
                    with open(f"papers/unpacking/{name}.pdf", 'wb') as f:
                        f.write(pdf_resp.read())
                print(f"Success: {name}")
            else:
                print(f"No Open Access PDF found for {name} ({doi})")
    except Exception as e:
        print(f"Failed {name}: {e}")
