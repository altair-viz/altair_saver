import json
import os
import shutil
from urllib.request import urlretrieve

PACKAGES = {"vega": ["5.9.0"], "vega-lite": ["4.0.2"], "vega-embed": ["6.2.1"]}

OUTDIR = os.path.join(os.path.dirname(__file__), "..", "altair_viewer", "scripts")


def main():
    for filename in os.listdir(OUTDIR):
        os.remove(os.path.join(OUTDIR, filename))
    with open(os.path.join(OUTDIR, "listing.json"), "w") as f:
        json.dump(PACKAGES, f, indent=2)
    for package, versions in PACKAGES.items():
        for version in versions:
            filename = os.path.join(OUTDIR, f"{package}-{version}.js")
            url = f"https://cdn.jsdelivr.net/npm/{package}@{version}"
            urlretrieve(url, filename)


if __name__ == "__main__":
    main()
