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
import markdown
from django.views.decorators.csrf import csrf_exempt
from collections import deque
from update_knowledge import process_and_update_index
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
import mlflow
from nltk.translate.bleu_score import sentence_bleu
from rouge_score import rouge_scorer

# Load keys and configs
load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
configure(api_key=GOOGLE_API_KEY)

# Load Annoy index + embeddings
VECTOR_DIM = 384
ANNOY_INDEX_PATH = "annoy_st_index.ann"
DOC_MAPPING_PATH = "doc_mapping.json"  # mapping index -> text
FEEDBACK_LOG_PATH = "rlhf_feedback_log.jsonl"

annoy_index = AnnoyIndex(VECTOR_DIM, "angular")
annoy_index.load(ANNOY_INDEX_PATH)

# Load mapping of index -> text chunk
with open(DOC_MAPPING_PATH, "r") as f:
    doc_text_mapping = json.load(f)

# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def chat_page(request, *args, **kwargs):
    return render(request, "index.html")


# Max number of conversation turns to keep
MAX_CONTEXT_HISTORY = 5


@csrf_exempt
def main_processor(request, *args, **kwargs):
    text_data = request.POST.get("text")
    file_data = request.FILES.get("file")
    parts = []
    model = "gemini-2.0-flash"

    # Initialize Gemini model
    gemini_model = GenerativeModel(model)

    # Initialize or retrieve session memory (deque)
    if "chat_history" not in request.session:
        request.session["chat_history"] = []

    # Limit context buffer size
    chat_history = deque(request.session["chat_history"], maxlen=MAX_CONTEXT_HISTORY)

    # 1. Optional image handling
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

    # 2. Text input handling
    if text_data:
        parts.append(glm.Part(text=text_data))

        # 3. Vector-based retrieval
        query_embedding = embedding_model.encode(text_data)
        top_k = 5
        nearest_ids = annoy_index.get_nns_by_vector(query_embedding, top_k)
        context_docs = [
            doc_text_mapping[str(i)] for i in nearest_ids if str(i) in doc_text_mapping
        ]
        context_text = "\n---\n".join(context_docs)
        print(f"Retrieved {len(context_docs)} context documents.")
        # 4. Add recent history from session buffer
        history_blocks = []
        for turn in chat_history:
            history_blocks.append(f"User: {turn['user']}\nAssistant: {turn['bot']}")
        history_prompt = "\n\n".join(history_blocks)

        # 5. Add both history and context to the prompt
        system_prompt = f"""You are a helpful analyst chatbot that answers user questions based on labor market data and prior context.

            [Conversation History]
            {history_prompt}

            [Retrieved Context]
            {context_text}

            Now answer the user's new question based on the above.
            """
        parts.insert(0, glm.Part(text=system_prompt))

        # 6. Generate response
        response = gemini_model.generate_content(glm.Content(parts=parts))
        reply_text = str(response.parts[0].text)

        # 7. Save this turn to session memory
        chat_history.append({"user": text_data, "bot": reply_text})
        request.session["chat_history"] = list(chat_history)

        # Log the conversation turn
        similar_query = check_similarity_and_log(text_data, context_docs, reply_text)

        # 8. Return response
        return JsonResponse(
            {
                "response": markdown.markdown(reply_text),
                "context_docs": context_docs,  # raw text array or optionally join with "\n\n"
            }
        )

    return JsonResponse({"response": "No input received."})


@csrf_exempt
def upload_file(request):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_file = request.FILES["file"]
        save_path = os.path.join("./knowledge_source", uploaded_file.name)

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


@csrf_exempt
def log_feedback(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            # Add server timestamp if missing
            if "timestamp" not in data:
                data["timestamp"] = datetime.utcnow().isoformat() + "Z"

            # Validate required keys minimally
            required_keys = [
                "timestamp",
                "query",
                "retrieved_docs",
                "generated_response",
                "feedback_rating",
            ]
            if not all(key in data for key in required_keys):
                return JsonResponse(
                    {"error": "Missing keys in feedback data"}, status=400
                )

            # Append feedback JSON line to file
            with open(FEEDBACK_LOG_PATH, "a") as f:
                f.write(json.dumps(data) + "\n")

            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "POST method required"}, status=400)


def check_similarity_and_log(new_query, retrieved_docs, generated_response):
    try:
        new_emb = embedding_model.encode(new_query).reshape(1, -1)
        with open(FEEDBACK_LOG_PATH, "r") as f:
            for line in f:
                data = json.loads(line)
                prev_emb = embedding_model.encode(data["query"]).reshape(1, -1)
                similarity = cosine_similarity(new_emb, prev_emb)[0][0]
                if similarity > 0.8:
                    print(f"⚠️ Found similar query: {similarity:.2f}")
                    return evaluate_and_log_metrics(
                        original_query=new_query,
                        original_retrieved=retrieved_docs,
                        original_response=generated_response,
                        previous=data,
                    )
    except Exception as e:
        print("Similarity check error:", e)
    return None


def evaluate_and_log_metrics(
    original_query, original_retrieved, original_response, previous
):
    try:
        # Compute Retrieval MRR (simplified for 5 retrieved docs)
        gold_doc = previous["retrieved_docs"][0] if previous["retrieved_docs"] else ""
        mrr = 0.0
        for i, doc in enumerate(original_retrieved):
            if gold_doc.strip() in doc.strip():
                mrr = 1.0 / (i + 1)
                break

        # BLEU score (simplified single reference)
        bleu = sentence_bleu(
            [previous["generated_response"].split()], original_response.split()
        )

        # ROUGE score
        scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
        rouge = scorer.score(previous["generated_response"], original_response)
        rouge_l = rouge["rougeL"].fmeasure

        print(f"📊 MRR: {mrr:.2f} | BLEU: {bleu:.2f} | ROUGE-L: {rouge_l:.2f}")

        # 🔍 Start MLflow run
        with mlflow.start_run(run_name="SimilarityEval"):
            # ✅ Log metrics
            mlflow.log_metric("MRR", mrr)
            mlflow.log_metric("BLEU", bleu)
            mlflow.log_metric("ROUGE-L", rouge_l)

            # ✅ Log inputs as params
            mlflow.log_param("query", original_query[:100])
            mlflow.log_param("previous_query", previous["query"][:100])
            mlflow.log_param(
                "similarity_to_previous",
                cosine_similarity(
                    embedding_model.encode(original_query).reshape(1, -1),
                    embedding_model.encode(previous["query"]).reshape(1, -1),
                )[0][0],
            )

            # ✅ Save and log full trace as artifact
            trace_data = {
                "current_query": original_query,
                "previous_query": previous["query"],
                "current_response": original_response,
                "previous_response": previous["generated_response"],
                "current_retrieved_docs": original_retrieved,
                "previous_retrieved_docs": previous["retrieved_docs"],
                "metrics": {"MRR": mrr, "BLEU": bleu, "ROUGE-L": rouge_l},
            }
            os.makedirs("mlruns/tmp", exist_ok=True)
            trace_path = "mlruns/tmp/trace.json"
            with open(trace_path, "w") as f:
                json.dump(trace_data, f, indent=2)
            mlflow.log_artifact(trace_path)

        return {"similarity": True, "MRR": mrr, "BLEU": bleu, "ROUGE-L": rouge_l}
    except Exception as e:
        print("Evaluation error:", e)
    return None
