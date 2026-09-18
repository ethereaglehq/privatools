"""Build frame-accurate video trims without discarding non-keyframe footage."""

from .video_tools_service import VP9_SPEED

VIDEO_ENCODERS = {
    ".mp4": ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-movflags", "+faststart"],
    ".mov": ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac"],
    ".mkv": ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac"],
    ".webm": ["-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "32", *VP9_SPEED, "-c:a", "libopus"],
    ".avi": ["-c:v", "mpeg4", "-q:v", "2", "-c:a", "libmp3lame"],
}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"}


def trim_command(input_path: str, output_path: str, extension: str, start: str, duration: float) -> list[str]:
    """Keep the original container and audio-only codec behavior.

    Output-side seeking with stream copy can discard every video packet until
    the next keyframe. Video is decoded and re-encoded so a selected interval
    inside a long GOP still contains footage. Audio-only files retain copying.
    FLAC is re-encoded losslessly to rebuild its sample-count header; stream
    copying retains the original duration. Optional mapping also supports
    silent video without requiring an audio track.
    """
    extension = extension.lower()
    if extension not in VIDEO_ENCODERS and extension not in AUDIO_EXTENSIONS:
        raise ValueError("Please upload a supported video or audio file.")
    command = ["ffmpeg", "-y", "-ss", start, "-i", input_path, "-t", f"{duration:.6f}"]
    if extension in VIDEO_ENCODERS:
        command += ["-map", "0:v:0?", "-map", "0:a:0?", *VIDEO_ENCODERS[extension]]
    else:
        command += ["-map", "0:a:0", "-vn", "-c:a", "flac" if extension == ".flac" else "copy"]
    return [*command, output_path]
