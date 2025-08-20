from __future__ import annotations
import os
from pathlib import Path

import plotly
import plotly.express as px
import plotly.io as pio
import os
import shutil

# Ensure reports directory exists
reports_dir = Path("reports")
reports_dir.mkdir(parents=True, exist_ok=True)

def _configure_kaleido_for_wsl() -> None:
    # Add WSL-safe Chromium flags
    try:
        args = list(getattr(pio.kaleido.scope, "chromium_args", []))
        extra = [
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--single-process",
            "--no-zygote",
        ]
        for a in extra:
            if a not in args:
                args.append(a)
        pio.kaleido.scope.chromium_args = args
    except Exception:
        pass

    # Kaleido has a bug when the install path contains spaces (like /mnt/d/Investment Codes/...)
    # Workaround: copy the kaleido executable folder to /tmp without spaces and fix quoting in wrapper
    try:
        import kaleido as _k
        pkg_dir = os.path.dirname(_k.__file__)
        src_exec_dir = os.path.join(pkg_dir, "executable")
        dst_dir = "/tmp/kaleido_executable"
        try:
            shutil.rmtree(dst_dir)
        except FileNotFoundError:
            pass
        shutil.copytree(src_exec_dir, dst_dir)
        wrapper_path = os.path.join(dst_dir, "kaleido")
        try:
            # Fix: quote DIR usage to handle spaces
            content = Path(wrapper_path).read_text(encoding="utf-8")
            content = content.replace("cd $DIR", 'cd "$DIR"')
            Path(wrapper_path).write_text(content, encoding="utf-8")
        except Exception:
            pass
        os.chmod(wrapper_path, 0o755)
        pio.kaleido.scope.executable = wrapper_path
    except Exception:
        pass

_configure_kaleido_for_wsl()

print(f"plotly={plotly.__version__}")

# Simple figure
fig = px.line(x=[0, 1, 2, 3], y=[0, 1, 0, 1], title="Plotly Verification (WSL + Kaleido)")

# Attempt static export via Kaleido (headless)
out_png = reports_dir / "plotly_test.png"
out_html = reports_dir / "plotly_test.html"

# Always write an interactive HTML fallback without external CDN to avoid hangs
fig.write_html(str(out_html), include_plotlyjs="inline")

# Try static export; if it fails, we still have HTML
try:
    fig.write_image(str(out_png), format="png", engine="kaleido")
    print(f"Wrote PNG: {out_png.resolve()}")
except Exception as exc:
    print(f"PNG export failed: {exc}")
    print(f"Wrote HTML: {out_html.resolve()}")
