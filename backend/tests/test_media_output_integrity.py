"""Decode real tool outputs; a 200 and nonempty download are not sufficient."""
import io
import json
import shutil
import subprocess
from pathlib import Path

import pytest
from PIL import Image

from backend.app.services.favicon_service import generate_favicon
from backend.app.services.video_tools_service import video_to_pdf


@pytest.mark.parametrize("size", [(120, 60), (40, 100), (8, 8)])
def test_favicon_contains_three_square_icons_without_distorting_artwork(tmp_path, size):
    source = tmp_path / "mark.png"
    Image.new("RGBA", size, (200, 40, 80, 255)).save(source)
    output = Path(generate_favicon(str(source)))
    try:
        with Image.open(output) as icon:
            assert icon.format == "ICO"
            assert icon.ico.sizes() == {(16, 16), (32, 32), (48, 48)}
            largest = icon.ico.getimage((48, 48)).convert("RGBA")
            assert largest.getpixel((24, 24)) == (200, 40, 80, 255)
            if size[0] != size[1]:
                assert largest.getpixel((0, 0))[3] == 0
                bounds = largest.getbbox()
                assert abs((bounds[2] - bounds[0]) / (bounds[3] - bounds[1]) - size[0] / size[1]) < 0.04
    finally:
        output.unlink(missing_ok=True)


@pytest.fixture(scope="module")
def media_fixtures(tmp_path_factory):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg or not shutil.which("ffprobe"):
        pytest.skip("Real media-output regression requires ffmpeg and ffprobe")
    directory = tmp_path_factory.mktemp("media-integrity")
    # Long GOP guarantees there is no keyframe at the selected start/end.
    subprocess.run([ffmpeg, "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=10:duration=3", "-f", "lavfi", "-i", "sine=frequency=440:duration=3", "-c:v", "libx264", "-g", "100", "-c:a", "aac", "-shortest", str(directory / "clip.mp4")], check=True, timeout=30)
    return directory


def inspect_download(response, destination):
    assert response.status_code == 200, response.text[:300] if response.status_code != 200 else ""
    destination.write_bytes(response.content)
    result = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(destination)], capture_output=True, check=True, timeout=15)
    return json.loads(result.stdout)


@pytest.mark.parametrize("start,end", [("00:00:00", "00:00:02"), ("00:00:00.400", "00:00:01.500")])
def test_video_trim_retains_video_and_audio_between_keyframes(client, media_fixtures, tmp_path, start, end):
    response = client.post("/api/trim-media", files={"file": ("clip.mp4", (media_fixtures / "clip.mp4").read_bytes(), "video/mp4")}, data={"start": start, "end": end})
    info = inspect_download(response, tmp_path / "trimmed.mp4")
    assert {stream["codec_type"] for stream in info["streams"]} == {"audio", "video"}
    video = next(stream for stream in info["streams"] if stream["codec_type"] == "video")
    assert (video["width"], video["height"]) == (160, 90)
    duration = float(end.split(":")[-1]) - float(start.split(":")[-1])
    assert abs(float(info["format"]["duration"]) - duration) <= 0.15
    # Exercise decoding, not just container headers.
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(tmp_path / "trimmed.mp4"), "-map", "0:v:0", "-frames:v", "1", "-f", "null", "-"], check=True, timeout=15)


def test_trim_keeps_silent_video_usable(client, media_fixtures, tmp_path):
    source = tmp_path / "silent.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(media_fixtures / "clip.mp4"), "-an", "-c:v", "copy", str(source)], check=True, timeout=15)
    response = client.post("/api/trim-media", files={"file": ("silent.mp4", source.read_bytes(), "video/mp4")}, data={"start": "00:00:00.500", "end": "00:00:01.500"})
    info = inspect_download(response, tmp_path / "result.mp4")
    assert [stream["codec_type"] for stream in info["streams"]] == ["video"]


@pytest.mark.parametrize("portrait", [False, True])
def test_video_pdf_places_each_frame_on_its_own_page_within_page_bounds(media_fixtures, tmp_path, portrait):
    import fitz
    source = media_fixtures / "clip.mp4"
    if portrait:
        rotated = tmp_path / "portrait.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(source), "-vf", "transpose=1", "-an", str(rotated)], check=True, timeout=20)
        source = rotated
    output = Path(video_to_pdf(str(source), frames=3))
    try:
        with fitz.open(output) as document:
            assert len(document) == 3
            for page in document:
                images = page.get_image_info()
                assert len(images) == 1
                rectangle = fitz.Rect(images[0]["bbox"])
                assert page.rect.contains(rectangle)
                assert rectangle.width > 0 and rectangle.height > 0
    finally:
        output.unlink(missing_ok=True)


@pytest.mark.parametrize("endpoint", ["trim-media", "audio-trim"])
@pytest.mark.parametrize("extension", ["mp3", "wav", "aac", "flac", "ogg", "m4a"])
def test_audio_only_trim_preserves_container_and_codec(client, media_fixtures, tmp_path, extension, endpoint):
    source = tmp_path / f"sound.{extension}"
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(media_fixtures / "clip.mp4"), "-vn", str(source)], check=True, timeout=20)
    source_info = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(source)]))
    response = client.post(f"/api/{endpoint}", files={"file": (source.name, source.read_bytes(), "application/octet-stream")}, data={"start": "00:00:00.500", "end": "00:00:01.500"})
    info = inspect_download(response, tmp_path / f"result.{extension}")
    assert [stream["codec_type"] for stream in info["streams"]] == ["audio"]
    assert info["streams"][0]["codec_name"] == source_info["streams"][0]["codec_name"]
    assert 0.85 <= float(info["format"]["duration"]) <= 1.2
    assert response.headers["content-type"].startswith("audio/")

def stream_seconds(info, kind):
    return float(next(stream for stream in info["streams"] if stream["codec_type"] == kind)["duration"])


@pytest.fixture(scope="module")
def speed_clip(media_fixtures):
    # 30 fps keeps the video's duration within a few frames of the exact value at 4x.
    path = media_fixtures / "speed.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=30:duration=2", "-f", "lavfi", "-i", "sine=frequency=440:duration=2", "-c:v", "libx264", "-c:a", "aac", "-shortest", str(path)], check=True, timeout=30)
    return path


# The slider's 0.25x end and the 4x preset, sent with two decimals as the page does.
@pytest.mark.parametrize("speed,seconds", [("0.25", 8.0), ("4.00", 0.5)])
def test_video_speed_accepts_both_ends_of_its_range(client, speed_clip, tmp_path, speed, seconds):
    response = client.post("/api/video-speed", files={"file": ("clip.mp4", speed_clip.read_bytes(), "video/mp4")}, data={"speed": speed})
    info = inspect_download(response, tmp_path / "speed.mp4")
    # Per stream: audio left at the old tempo would still pass a check of the file's duration.
    assert abs(stream_seconds(info, "video") - seconds) <= 0.15
    assert abs(stream_seconds(info, "audio") - seconds) <= 0.15


@pytest.mark.parametrize("speed", ["0.24", "4.01"])
def test_video_speed_rejects_speeds_outside_its_range(client, speed_clip, speed):
    response = client.post("/api/video-speed", files={"file": ("clip.mp4", speed_clip.read_bytes(), "video/mp4")}, data={"speed": speed})
    assert response.status_code == 422


def test_video_speed_changes_a_video_without_audio(client, speed_clip, tmp_path):
    source = tmp_path / "silent.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(speed_clip), "-an", "-c:v", "copy", str(source)], check=True, timeout=15)
    response = client.post("/api/video-speed", files={"file": ("silent.mp4", source.read_bytes(), "video/mp4")}, data={"speed": "2"})
    info = inspect_download(response, tmp_path / "result.mp4")
    assert [stream["codec_type"] for stream in info["streams"]] == ["video"]
    assert abs(stream_seconds(info, "video") - 1.0) <= 0.15

