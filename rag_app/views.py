from django.shortcuts import render
import google.ai.generativelanguage as glm
import io
from PIL import Image
from django.http import JsonResponse
import os
from dotenv import load_dotenv
from google.generativeai.client import configure
from google.generativeai.generative_models import GenerativeModel

load_dotenv()

GOOGLE_API_KEY = os.getenv("API_KEY")
configure(api_key=GOOGLE_API_KEY)


def chat_page(request, *args, **kwargs):
    return render(request, "index.html")


def main_processor(request, *args, **kwargs):
    text_data = request.POST.get("text")
    file_data = request.FILES.get("file")
    parts = []
    g_mode = "gemini-pro"
    if file_data is not None:
        g_mode += "-vision"
        image_file = file_data.read()
        with io.BytesIO(image_file) as img_io:
            img = Image.open(img_io)
            image_format = img.format

        if image_format:
            # Get MIME type and extension
            mime = f"image/{image_format.lower()}"
            # extension = mimetypes.guess_extension(mime)
            parts.append(
                glm.Part(inline_data=glm.Blob(mime_type=mime, data=image_file))
            )

    if text_data != "":
        parts.append(glm.Part(text=text_data))

    # genai.configure(api_key=GOOGLE_API_KEY)
    model = GenerativeModel(g_mode)
    response = model.generate_content(glm.Content(parts=parts))

    response_data = {"response": str(response.parts[0].text)}

    return JsonResponse(response_data)
