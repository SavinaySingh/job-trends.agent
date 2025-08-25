import io
import os
import json
from django.shortcuts import render
from django.http import JsonResponse
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
from rag_app.services.crawler import WebCrawler
from rag_app.services.web_searcher import WebSearcher
from rag_app.prompt import WEB_CONTEXT_NOTE, KNOWLEDGE_BASE_CONTEXT_PROMPT
from rag_app.config import GOOGLE_API_KEY
from rag_app.services.evaluation import FeedbackLogger
from .utils.is_web_search import should_use_web_search

# Configure Gemini API
configure(api_key=GOOGLE_API_KEY)

# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


# Load Annoy index + embeddings
VECTOR_DIM = 384
ANNOY_INDEX_PATH = "annoy_st_index.ann"
DOC_MAPPING_PATH = "data/doc_mapping.json"
FEEDBACK_LOG_PATH = "data/rlhf_feedback_log.jsonl"


annoy_index = AnnoyIndex(VECTOR_DIM, "angular")
annoy_index.load(ANNOY_INDEX_PATH)

# Load mapping of index -> text chunk
with open(DOC_MAPPING_PATH, "r") as f:
    doc_text_mapping = json.load(f)


@csrf_exempt
def chat_page(request, *args, **kwargs):
    return render(request, "index.html")


# Max number of conversation turns to keep
MAX_CONTEXT_HISTORY = 5


@csrf_exempt
def main_processor(request, *args, **kwargs):
    text_data = request.POST.get("text")
    file_data = request.FILES.get("file")
    use_web_search = request.POST.get("web_search", "false").lower() == "true"

    parts = []
    model = "gemini-2.0-flash"

    # Initialize Gemini model
    gemini_model = GenerativeModel(model)

    # Initialize searcher and crawler
    searcher = WebSearcher()
    crawler = WebCrawler()

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

        # 3. Vector-based retrieval from existing knowledge base
        query_embedding = embedding_model.encode(text_data)
        top_k = 5
        nearest_ids = annoy_index.get_nns_by_vector(query_embedding, top_k)
        context_docs = [
            doc_text_mapping[str(i)] for i in nearest_ids if str(i) in doc_text_mapping
        ]

        # 4. Web search and crawling (if needed)
        web_results = []
        crawled_content = []

        if use_web_search or should_use_web_search(text_data):
            print("🔍 Performing web search...")
            search_results = searcher.search(text_data, num_results=5)

            if search_results:
                # Crawl the top search results
                urls_to_crawl = [
                    result["url"] for result in search_results[:3]
                ]  # Crawl top 3
                crawled_content = crawler.crawl_multiple_urls(urls_to_crawl)

                # Save crawled data for future use
                if crawled_content:
                    crawler.save_crawled_data(crawled_content)

                # Prepare web results for context
                for i, result in enumerate(search_results):
                    web_result_text = f"Title: {result['title']}\nSnippet: {result['snippet']}\nURL: {result['url']}"

                    # Add crawled content if available
                    if i < len(crawled_content) and crawled_content[i]:
                        web_result_text += (
                            f"\nContent: {crawled_content[i]['content'][:1000]}..."
                        )

                    web_results.append(web_result_text)

        # 5. Combine all context sources
        all_context = []
        if context_docs:
            all_context.extend(context_docs)
        if web_results:
            all_context.extend(web_results)

        print(
            f"📚 Retrieved {len(context_docs)} local docs, {len(web_results)} web results."
        )

        # 6. Add recent history from session buffer
        history_blocks = []
        for turn in chat_history:
            history_blocks.append(f"User: {turn['user']}\nAssistant: {turn['bot']}")
        history_prompt = "\n\n".join(history_blocks)

        # 7. Construct system prompt with context
        system_prompt = KNOWLEDGE_BASE_CONTEXT_PROMPT.format(
            history_prompt=history_prompt,
            context_docs=(
                "\n---\n".join(context_docs)
                if context_docs
                else "No local context found."
            ),
            web_context_note=WEB_CONTEXT_NOTE if web_results else "",
            web_results="\n---\n".join(web_results) if web_results else "",
        )
        parts.insert(0, glm.Part(text=system_prompt))

        # 8. Generate response
        response = gemini_model.generate_content(glm.Content(parts=parts))
        reply_text = str(response.parts[0].text)

        # 9. Save this turn to session memory
        chat_history.append({"user": text_data, "bot": reply_text})
        request.session["chat_history"] = list(chat_history)

        # Log the conversation turn
        log_feedback = FeedbackLogger(log_path=FEEDBACK_LOG_PATH)
        similar_query = log_feedback.check_similarity_and_log(
            text_data, all_context, reply_text
        )

        # 10. Return enhanced response
        response_data = {
            "response": markdown.markdown(reply_text),
            "context_docs": context_docs,
            "web_search_performed": bool(web_results),
            "web_results_count": len(web_results),
            "crawled_pages": len(crawled_content),
        }

        if web_results:
            response_data["search_sources"] = [
                {"title": result.get("title", ""), "url": result.get("url", "")}
                for result in searcher.search(text_data, num_results=3)
            ]

        return JsonResponse(response_data)

    return JsonResponse({"response": "No input received."})


@csrf_exempt
def crawl_urls(request):
    """Endpoint to manually crawl specific URLs"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            urls = data.get("urls", [])

            if not urls:
                return JsonResponse({"error": "No URLs provided"}, status=400)

            crawler = WebCrawler()
            crawled_data = crawler.crawl_multiple_urls(urls)

            # Save crawled data
            if crawled_data:
                filepath = crawler.save_crawled_data(crawled_data)

                # Optionally update the knowledge base with crawled content
                # You can extend this to add crawled content to your Annoy index

                return JsonResponse(
                    {
                        "message": f"Successfully crawled {len(crawled_data)} URLs",
                        "crawled_count": len(crawled_data),
                        "saved_to": filepath,
                        "results": [
                            {
                                "url": item["url"],
                                "title": item["title"],
                                "content_length": item["content_length"],
                            }
                            for item in crawled_data
                        ],
                    }
                )
            else:
                return JsonResponse(
                    {"error": "No content could be crawled"}, status=400
                )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "POST method required"}, status=400)


# Keep all your existing functions unchanged
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
