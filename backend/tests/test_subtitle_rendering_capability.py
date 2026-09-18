"""Subtitle fallback timing and useful failure contracts."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from backend.app.services import video_tools_service, subtitle_renderer
from backend.app.utils.exceptions import DependencyError, ValidationError


def test_missing_all_render_filters_is_dependency_error(monkeypatch):
    monkeypatch.setattr(video_tools_service.subprocess, "run", lambda command, **kwargs: subprocess.CompletedProcess(command, 0, " ... scale V->V Scale video\n", ""))
    with pytest.raises(DependencyError, match="libass or the overlay"):
        video_tools_service.burn_subtitles("not-opened.mp4", "not-opened.srt")


def test_without_libass_uses_plain_renderer(monkeypatch, tmp_path):
    monkeypatch.setattr(video_tools_service.subprocess, "run", lambda command, **kwargs: subprocess.CompletedProcess(command, 0, " ... overlay VV->V Overlay video\n", ""))
    monkeypatch.setattr(video_tools_service, "temp_output", lambda *args: tmp_path / "result.mp4")
    calls = []
    monkeypatch.setattr(subtitle_renderer, "render_plain_subtitles", lambda *args: calls.append(args))
    assert video_tools_service.burn_subtitles("video.mp4", "captions.srt") == str(tmp_path / "result.mp4")
    assert calls[0][:3] == ("video.mp4", "captions.srt", str(tmp_path / "result.mp4"))


def test_native_subtitle_path_never_enters_filter_expression(monkeypatch, tmp_path):
    source = tmp_path / "path:with'quote.srt"
    source.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello\n")
    monkeypatch.setattr(video_tools_service.subprocess, "run", lambda command, **kwargs: subprocess.CompletedProcess(command, 0, " ... subtitles V->V Render subtitles\n", ""))
    calls = []
    def run(args, **kwargs):
        calls.append((args, kwargs))
        assert (Path(kwargs["cwd"]) / "captions.srt").read_text() == source.read_text()
    monkeypatch.setattr(video_tools_service, "_run_ffmpeg", run)
    video_tools_service.burn_subtitles("video.mp4", str(source))
    assert calls[0][0][calls[0][0].index("-vf") + 1] == "subtitles=captions.srt"
    assert not Path(calls[0][1]["cwd"]).exists()


@pytest.mark.parametrize("content", ["not a subtitle", "1\n00:00:02,000 --> 00:00:01,000\nWrong order", "1\n00:99:00,000 --> 01:00:00,000\nInvalid time"])
def test_bad_cues_fail_before_rendering(tmp_path, content):
    source = tmp_path / "bad.srt"
    source.write_text(content)
    with pytest.raises(ValidationError):
        subtitle_renderer.read_cues(str(source))


def test_utf8_bom_and_plain_formatting(tmp_path):
    source = tmp_path / "captions.srt"
    source.write_text("\ufeff1\r\n00:00:00,250 --> 00:00:01,250\r\n<b>Café &amp; tea</b>\r\n", encoding="utf-8")
    assert subtitle_renderer.read_cues(str(source)) == [(0.25, 1.25, "Café & tea")]


def test_subtitle_route_preserves_dependency_status(client, monkeypatch):
    def unavailable(*args):
        raise DependencyError("Subtitle rendering needs FFmpeg with libass.")
    monkeypatch.setattr(video_tools_service, "burn_subtitles", unavailable)
    response = client.post("/api/add-subtitles", files={"file": ("clip.mp4", b"fixture", "video/mp4"), "srt": ("captions.srt", b"1\n00:00:00,000 --> 00:00:01,000\nHello\n", "text/plain")})
    assert response.status_code == 503
    assert response.json()["detail"] == "The service is temporarily unavailable. Please try again."


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="Requires real FFmpeg")
def test_real_plain_renderer_preserves_timing_audio_and_dimensions(tmp_path):
    video = tmp_path / "clip.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=blue:s=320x180:r=24:d=2", "-f", "lavfi", "-i", "sine=frequency=440:duration=2", "-c:v", "libx264", "-c:a", "aac", "-shortest", str(video)], check=True, timeout=30)
    srt = tmp_path / "captions.srt"
    srt.write_text("1\n00:00:00,250 --> 00:00:01,250\nSynthetic subtitle\n")
    output = tmp_path / "result.mp4"
    subtitle_renderer.render_plain_subtitles(str(video), str(srt), str(output), video_tools_service._run_ffmpeg)
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(output)], capture_output=True, text=True, check=True)
    info = json.loads(probe.stdout)
    assert {stream["codec_type"] for stream in info["streams"]} == {"video", "audio"}
    assert (info["streams"][0]["width"], info["streams"][0]["height"]) == (320, 180)
    assert float(info["format"]["duration"]) == pytest.approx(2, abs=.1)
    def bright_pixels(at):
        frame = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(at), "-i", str(output), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        return sum(frame[i] > 150 and frame[i+1] > 150 and frame[i+2] > 150 for i in range(0, len(frame), 3))
    assert bright_pixels(.1) < 10
    assert bright_pixels(.6) > 100
    assert bright_pixels(1.7) < 10
