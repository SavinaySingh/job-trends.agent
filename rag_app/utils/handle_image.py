import io
from PIL import Image
import google.ai.generativelanguage as glm


def handle_image(file_data):
    parts = []
    if file_data:
        image_file = file_data.read()
        with io.BytesIO(image_file) as img_io:
            img = Image.open(img_io)
            image_format = img.format
        if image_format:
            mime = f"image/{image_format.lower()}"
            parts.append(
                glm.Part(inline_data=glm.Blob(mime_type=mime, data=image_file))
            )
    return parts
