import pytesseract
import io
from PIL import Image

def crop_schedule(
    image_bytes,
    x_offset=-10
):
  try:
    img = Image.open(io.BytesIO(image_bytes))

    if img is None:
        raise ValueError(f"Image not found")

    data = pytesseract.image_to_data(
        img,
        output_type=pytesseract.Output.DICT
    )

    words = [w.strip().lower() for w in data["text"]]

    top_y = None
    bottom_y = None
    left_x = None
    date_y = None
    trade_x = None

    # Find "Date" column header
    for i, word in enumerate(words):
        if word == "date":
            left_x = data["left"][i]
            date_y = data["top"][i]
            break

    # Find "Create Trade Proposals"
    for i in range(len(words) - 2):
        if (
            words[i] == "create"
            and words[i + 1] == "trade"
            and words[i + 2] == "proposals"
        ):
            top_y = max(
                data["top"][i] + data["height"][i],
                data["top"][i + 1] + data["height"][i + 1],
                data["top"][i + 2] + data["height"][i + 2],
            )

            # Fallback x-position if Date is not found
            trade_x = data["left"][i + 1]

            break

    # Fallback to just above Date
    if top_y is None and date_y is not None:
        top_y = max(0, date_y - 20)

    # If Date wasn't found, use Trade's x-position
    if left_x is None and trade_x is not None:
        left_x = trade_x

    # Find "Paid Hours"
    for i, word in enumerate(words):
        if (
            word == "paid"
            and i + 1 < len(words)
            and words[i + 1] == "hours"
        ):
            bottom_y = data["top"][i]
            break

    if left_x is None:
        raise Exception(
            "Could not find 'Date' header or fallback 'Trade' position"
        )

    if top_y is None:
        raise Exception(
            "Could not find 'Create Trade Proposals' or fallback 'Date' header"
        )

    if bottom_y is None:
        raise Exception("Could not find 'Paid Hours'")

    crop_x = max(0, left_x + x_offset)

    cropped = img.crop((crop_x, top_y, img.width, bottom_y))
    buf = io.BytesIO()
    cropped.save(buf, format="PNG")
    cropped_bytes = buf.getvalue()
    return cropped_bytes
  except Exception as e:
      raise RuntimeError("Error cropping")