"""Choose an installed Ogg encoder without changing the host's FFmpeg build."""
import subprocess
from functools import lru_cache

from ..utils.exceptions import DependencyError


@lru_cache(maxsize=1)
def ogg_encoder() -> str:
    try:
        result = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DependencyError("Audio conversion is unavailable on this server.") from exc
    encoders = {parts[1] for line in result.stdout.splitlines() if len(parts := line.split()) > 1}
    if result.returncode == 0:
        for codec in ("libvorbis", "libopus"):
            if codec in encoders:
                return codec
    raise DependencyError("OGG conversion needs an installed Vorbis or Opus encoder.")
