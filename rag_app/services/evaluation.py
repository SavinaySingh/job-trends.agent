from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import mlflow
import json
from nltk.translate.bleu_score import sentence_bleu
from rouge_score import rouge_scorer
import os

# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
FEEDBACK_LOG_PATH = "data/rlhf_feedback_log.jsonl"


class FeedbackLogger:
    """Log user feedback and evaluate similarity to previous queries"""

    def __init__(self, log_path=FEEDBACK_LOG_PATH):
        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

    def check_similarity_and_log(self, new_query, retrieved_docs, generated_response):
        """Check similarity of new query to previous queries and log metrics if similar"""
        try:
            new_emb = embedding_model.encode(new_query).reshape(1, -1)
            with open(FEEDBACK_LOG_PATH, "r") as f:
                for line in f:
                    data = json.loads(line)
                    prev_emb = embedding_model.encode(data["query"]).reshape(1, -1)
                    similarity = cosine_similarity(new_emb, prev_emb)[0][0]
                    if similarity > 0.8:
                        print(f"⚠️ Found similar query: {similarity:.2f}")
                        return self._evaluate_and_log_metrics(
                            original_query=new_query,
                            original_retrieved=retrieved_docs,
                            original_response=generated_response,
                            previous=data,
                        )
        except Exception as e:
            print("Similarity check error:", e)
        return None

    def _evaluate_and_log_metrics(
        self, original_query, original_retrieved, original_response, previous
    ):
        """Evaluate metrics against previous similar query and log to MLflow"""
        try:
            # Compute Retrieval MRR (simplified for 5 retrieved docs)
            gold_doc = (
                previous["retrieved_docs"][0] if previous["retrieved_docs"] else ""
            )
            mrr = 0.0
            for i, doc in enumerate(original_retrieved):
                if gold_doc.strip() in str(doc).strip():
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

            # 🏃 Start MLflow run
            with mlflow.start_run(run_name="SimilarityEval"):
                # ✅ Log metrics
                mlflow.log_metric("MRR", mrr)
                mlflow.log_metric("BLEU", bleu)  # type: ignore
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
