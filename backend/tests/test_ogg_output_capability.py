import json
import shutil
import subprocess

import pytest

from backend.app.services.ffmpeg_capabilities import ogg_encoder
from backend.app.utils.exceptions import DependencyError


@pytest.mark.parametrize("available,expected", [("libvorbis libopus", "libvorbis"), ("libopus", "libopus"), ("vorbis", None)])
def test_ogg_uses_a_supported_installed_encoder(monkeypatch, available, expected):
    ogg_encoder.cache_clear()
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "\n".join(f" A..... {name} audio encoder" for name in available.split()), ""))
    try:
        if expected:
            assert ogg_encoder() == expected
        else:
            with pytest.raises(DependencyError):
                ogg_encoder()
    finally:
        ogg_encoder.cache_clear()


@pytest.mark.parametrize("endpoint", ["extract-audio", "audio-converter"])
def test_real_ogg_conversion_decodes_with_available_encoder(client, tmp_path, endpoint):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("Requires actual FFmpeg and ffprobe")
    source = tmp_path / "tone.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=1", str(source)], check=True, timeout=20)
    response = client.post(f"/api/{endpoint}", files={"file": ("tone.wav", source.read_bytes(), "audio/wav")}, data={"format": "ogg", "bitrate": "128k"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/ogg")
    output = tmp_path / "result.ogg"
    output.write_bytes(response.content)
    info = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(output)]))
    assert info["streams"][0]["codec_name"] in {"vorbis", "opus"}
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(output), "-f", "null", "-"], check=True, timeout=15)
