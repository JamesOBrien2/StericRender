#!/usr/bin/env python
"""Download SambVca 2 supporting XYZ when the ACS endpoint allows it."""

from __future__ import annotations

import argparse
import urllib.error
import urllib.request
from pathlib import Path


SI_URL = "https://pubs.acs.org/doi/suppl/10.1021/acs.organomet.6b00371/suppl_file/om6b00371_si_002.xyz"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="examples/sambvca/om6b00371_si_002.xyz")
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(SI_URL, timeout=30) as response:
            output.write_bytes(response.read())
    except urllib.error.HTTPError as exc:
        if exc.code == 403:
            raise SystemExit(
                "ACS returned HTTP 403 for scripted download. Download the supporting XYZ manually from "
                "https://pubs.acs.org/doi/10.1021/acs.organomet.6b00371 and save it to "
                f"{output}"
            ) from exc
        raise
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()

