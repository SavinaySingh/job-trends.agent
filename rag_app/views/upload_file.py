import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from google.generativeai.generative_models import GenerativeModel
from rag_app.utils.update_knowledge import process_and_update_index


@csrf_exempt
def upload_file(request):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_file = request.FILES["file"]
        save_path = os.path.join("data/knowledge_source", uploaded_file.name)

        with open(save_path, "wb+") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # Initialize Gemini LLM if needed (for PDFs/PNGs)
        os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]
        llm = GenerativeModel("gemini-2.0-flash")

        # Trigger pipeline
        try:
            process_and_update_index(save_path, llm=llm)
            return JsonResponse({"message": "File uploaded and processed successfully"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "No file uploaded"}, status=400)
