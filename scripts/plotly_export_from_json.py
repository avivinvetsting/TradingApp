from __future__ import annotations
import json
import sys
from pathlib import Path
import plotly.io as pio

# Usage: python scripts/plotly_export_from_json.py <input_json> <output_path> [format]
# format defaults to 'png'

def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: plotly_export_from_json.py <input_json> <output_path> [format]", file=sys.stderr)
        return 2
    in_json = Path(sys.argv[1])
    out_path = Path(sys.argv[2])
    fmt = sys.argv[3] if len(sys.argv) >= 4 else "png"

    data = json.loads(in_json.read_text(encoding="utf-8"))
    fig = pio.from_json(json.dumps(data))

    # Optional chromium args from env already handled by plotly if configured by caller
    fig.write_image(str(out_path), format=fmt, engine="kaleido")
    print(str(out_path))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
