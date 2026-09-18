from PIL import Image

from ..utils.filenames import temp_output


def heic_to_jpg(input_path: str, quality: int = 90) -> str:
    """Convert HEIC/HEIF image to JPEG using Pillow.

    Pillow decodes HEIF through the pillow-heif opener that `backend.app.utils`
    registers on import; an undecodable file makes `Image.open` raise.
    """
    output_path = temp_output("converted", "jpg")

    with Image.open(input_path) as img:
        # Convert to RGB (HEIC may have alpha channel)
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(str(output_path), "JPEG", quality=quality, optimize=True)

    return str(output_path)
