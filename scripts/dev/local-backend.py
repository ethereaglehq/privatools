"""Run the complete app locally, with account data separate from job files.

Uses the repository's pinned virtual environment. No production environment
file or credentials are loaded; explicit process environment overrides remain
available. The built frontend and its API share one loopback origin so session
cookies, path-scoped CSP, downloads, and the installed PWA all work together.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true", help="Reload backend code during development")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")

    root = Path(__file__).resolve().parents[2]
    python = root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.is_file():
        parser.exit(1, "Backend dependencies are missing. Run npm run setup:backend first.\n")

    env = os.environ.copy()
    # Share only the PUBLIC development identity key with the Vite preview.
    # Never load a secret key or a production environment file implicitly.
    local_frontend_env = root / "frontend" / ".env.local"
    if not env.get("CLERK_PUBLISHABLE_KEY") and local_frontend_env.is_file():
        for line in local_frontend_env.read_text().splitlines():
            name, sep, value = line.partition("=")
            if sep and name.strip() == "VITE_CLERK_PUBLISHABLE_KEY":
                public_key = value.strip().strip("\"'")
                if public_key.startswith("pk_test_"):
                    env["CLERK_PUBLISHABLE_KEY"] = public_key
                break
    defaults = {
        "ENVIRONMENT": "development",  # Local HTTP cookies; production keeps Secure cookies.
        "FRONTEND_PATH": str(root / "frontend" / "dist"),
        "PRIVATOOLS_DATA_DIR": str(root / "data" / "local"),
        "TEMP_DIR": str(root / "temp" / "local"),
        "TRUSTED_HOSTS": "localhost,127.0.0.1",
        "ALLOWED_ORIGINS": f"http://127.0.0.1:{args.port},http://localhost:{args.port}",
        "NUMBA_DISABLE_JIT": "1",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
    }
    # Homebrew native libraries are outside macOS's default dynamic-library
    # search path. WeasyPrint/Cairo/QR decoding need to find these libraries.
    if sys.platform == "darwin":
        library_dirs = [str(p) for p in (Path("/opt/homebrew/lib"), Path("/usr/local/lib")) if p.is_dir()]
        if library_dirs:
            defaults["DYLD_FALLBACK_LIBRARY_PATH"] = ":".join(library_dirs + ["/usr/lib"])
    for name, value in defaults.items():
        env.setdefault(name, value)

    # tempfile-based media/archive processors and path-based PDF processors
    # must use the same managed directory so the janitor covers both.
    os.chdir(root)
    Path(env["TEMP_DIR"]).mkdir(parents=True, exist_ok=True, mode=0o700)
    Path(env["PRIVATOOLS_DATA_DIR"]).mkdir(parents=True, exist_ok=True, mode=0o700)
    env["TMPDIR"] = str(Path(env["TEMP_DIR"]).resolve())
    env.setdefault("U2NET_HOME", str(Path(env["PRIVATOOLS_DATA_DIR"]) / "models"))

    if not (Path(env["FRONTEND_PATH"]) / "index.html").is_file():
        parser.exit(1, "Frontend build is missing. Run npm --prefix frontend run build first.\n")

    print(f"PrivaTools: http://127.0.0.1:{args.port}/", flush=True)
    print("Accounts persist in data/local; temporary processing files use temp/local (unless overridden).", flush=True)
    command = [str(python), "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", str(args.port)]
    if args.reload:
        command.extend(["--reload", "--reload-dir", str(root / "backend" / "app")])
    os.execve(python, command, env)


if __name__ == "__main__":
    main()
