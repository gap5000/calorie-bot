from io import BytesIO

import zxingcpp
from PIL import Image


def read_barcode_from_image(
    image_bytes: bytes,
) -> tuple[str | None, int]:
    try:
        image = Image.open(BytesIO(image_bytes))
        image.load()
    except (OSError, ValueError):
        return None, 0

    results = zxingcpp.read_barcodes(image)

    valid_barcodes: list[str] = []

    for result in results:
        barcode = "".join(
            character
            for character in result.text
            if character.isdigit()
        )

        if 8 <= len(barcode) <= 14:
            valid_barcodes.append(barcode)

    if not valid_barcodes:
        return None, 0

    return valid_barcodes[0], len(valid_barcodes)