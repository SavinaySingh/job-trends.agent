import io
import os
from django.shortcuts import render
import google.ai.generativelanguage as glm
from PIL import Image
from django.http import JsonResponse
from dotenv import load_dotenv
from google.generativeai.client import configure
from google.generativeai.generative_models import GenerativeModel

load_dotenv()

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
configure(api_key=GOOGLE_API_KEY)


def chat_page(request, *args, **kwargs):
    return render(request, "index.html")


def main_processor(request, *args, **kwargs):
    text_data = request.POST.get("text")
    file_data = request.FILES.get("file")
    parts = []
    model = "gemini-pro"
    if file_data is not None:
        model = "gemini-1.5-flash"
        image_file = file_data.read()
        with io.BytesIO(image_file) as img_io:
            img = Image.open(img_io)
            image_format = img.format

        if image_format:
            mime = f"image/{image_format.lower()}"
            parts.append(
                glm.Part(inline_data=glm.Blob(mime_type=mime, data=image_file))
            )

    if text_data != "":
        parts.append(glm.Part(text=text_data))

    # genai.configure(api_key=GOOGLE_API_KEY)
    model = GenerativeModel(model)
    response = model.generate_content(glm.Content(parts=parts))

    response_data = {"response": str(response.parts[0].text)}

    return JsonResponse(response_data)
