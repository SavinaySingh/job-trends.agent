import io
import os
import json
from django.shortcuts import render
from django.http import JsonResponse
from dotenv import load_dotenv
from PIL import Image
from annoy import AnnoyIndex
from sentence_transformers import SentenceTransformer
import google.ai.generativelanguage as glm
from google.generativeai.client import configure
from google.generativeai.generative_models import GenerativeModel

# Load keys and configs
load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
configure(api_key=GOOGLE_API_KEY)

# Load Annoy index + embeddings
VECTOR_DIM = 384
ANNOY_INDEX_PATH = "annoy_st_index.ann"
DOC_MAPPING_PATH = "doc_mapping.json"  # mapping index -> text

annoy_index = AnnoyIndex(VECTOR_DIM, "angular")
annoy_index.load(ANNOY_INDEX_PATH)

# Load mapping of index -> text chunk
with open(DOC_MAPPING_PATH, "r") as f:
    doc_text_mapping = json.load(f)

# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def chat_page(request, *args, **kwargs):
    return render(request, "index.html")


def main_processor(request, *args, **kwargs):
    text_data = request.POST.get("text")
    file_data = request.FILES.get("file")
    parts = []
    model = "gemini-2.0-flash"

    # Handle image input (optional)
    if file_data is not None:
        image_file = file_data.read()
        with io.BytesIO(image_file) as img_io:
            img = Image.open(img_io)
            image_format = img.format
        if image_format:
            mime = f"image/{image_format.lower()}"
            parts.append(
                glm.Part(inline_data=glm.Blob(mime_type=mime, data=image_file))
            )

    # RAG: get top documents using Annoy vector search
    context_docs = []
    if text_data:
        parts.append(glm.Part(text=text_data))

        # Embed query
        query_embedding = embedding_model.encode(text_data)

        # Retrieve top K chunks
        top_k = 5
        nearest_ids = annoy_index.get_nns_by_vector(query_embedding, top_k)

        # Get associated text
        context_docs = [
            doc_text_mapping[str(i)] for i in nearest_ids if str(i) in doc_text_mapping
        ]

        # Prepend context to the prompt
        context_text = "\n---\n".join(context_docs)
        print(f"Context for RAG: {context_text}")
        parts.insert(
            0, glm.Part(text=f"Use the following context to answer:\n{context_text}")
        )

    # Generate using Gemini
    gemini_model = GenerativeModel(model)
    response = gemini_model.generate_content(glm.Content(parts=parts))

    response_data = {"response": str(response.parts[0].text)}
    return JsonResponse(response_data)
