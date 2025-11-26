import logging
import os
import azure.functions as func
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")

AOAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AOAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AOAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

search_client = SearchClient(
    endpoint=SEARCH_ENDPOINT,
    index_name=SEARCH_INDEX,
    credential=AzureKeyCredential(SEARCH_KEY),
)

aoai_client = AzureOpenAI(
    api_key=AOAI_KEY,
    api_version="2024-02-15-preview",
    azure_endpoint=AOAI_ENDPOINT,
)

app = func.FunctionApp()

@app.function_name(name="ragQuery")
@app.route(route="ragQuery", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def rag_query(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        question = body.get("question")
        business_context = body.get("businessContext", "")

        if not question:
            return func.HttpResponse("Missing question", status_code=400)

        # — 1. Retrieval —
        search_text = f"{question} {business_context}".strip()
        results = search_client.search(search_text, top=5)

        docs = []
        for r in results:
            docs.append({
                "id": r["id"],
                "title": r.get("title", ""),
                "content": r.get("content", "")[:2000],
                "url": r.get("url", "")
            })

        context_chunks = "\n\n".join(
            [f"Source {i+1} – {d['title']}:\n{d['content']}" for i, d in enumerate(docs)]
        )

        # — 2. LLM Completion —
        completion = aoai_client.chat.completions.create(
            model=AOAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "Answer only using the context provided."},
                {"role": "user", "content": f"Question: {question}\n\nContext:\n{context_chunks}"}
            ],
            temperature=0.2,
        )

        answer = completion.choices[0].message.content

        # — 3. Citations —
        citations = [
            {"sourceId": d["id"], "snippet": d["content"][:250]}
            for d in docs
        ]

        resp = {
            "answer": answer,
            "citations": citations,
            "rawDocuments": docs
        }

        return func.HttpResponse(str(resp), mimetype="application/json", status_code=200)

    except Exception as ex:
        logging.exception("Error in RAG query")
        return func.HttpResponse(f"Error: {ex}", status_code=500)
