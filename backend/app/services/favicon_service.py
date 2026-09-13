from ..utils.filenames import temp_output
from ..utils.images import open_image_safe
from PIL import Image, ImageOps


def generate_favicon(input_path: str) -> str:
    """Generate a .ico favicon from any image.

    Creates a multi-size ICO file with 16x16, 32x32, and 48x48 icons.
    """
    output_path = temp_output("favicon", "ico")

    with open_image_safe(input_path, convert="RGBA") as img:
        # ICO's sizes argument preserves aspect ratio. Put rectangular artwork
        # on a transparent square first so every advertised icon is square,
        # without stretching or cropping the user's mark. A 48 px base also
        # guarantees all three sizes for very small source images.
        artwork = ImageOps.contain(img, (48, 48), Image.Resampling.LANCZOS)
        square = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
        square.alpha_composite(artwork, ((48 - artwork.width) // 2, (48 - artwork.height) // 2))
        square.save(
            str(output_path),
            format="ICO",
            sizes=[(16, 16), (32, 32), (48, 48)],
        )

    return str(output_path)
