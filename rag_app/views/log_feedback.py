import json
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

FEEDBACK_LOG_PATH = "data/rlhf_feedback_log.jsonl"


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
