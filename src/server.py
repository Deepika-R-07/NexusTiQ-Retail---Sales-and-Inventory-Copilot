from flask import (
    Flask,
    jsonify,
    request,
    send_from_directory
)

from .config import *
from .data import load_data

from .analytics import (
    build_metrics,
    dashboard,
    product_dashboard,
    inventory_runway,
    store_intelligence
)

from .copilot import (
    evidence_from_data,
    deterministic_answer
)

from .retrieval import LocalRetriever
from .gemini import GeminiService

import json


def create_app():

    # ---------------------------------------------------------
    # CREATE FLASK APP
    # ---------------------------------------------------------

    app = Flask(
        __name__,
        static_folder=str(FRONTEND_DIR),
        static_url_path=""
    )

    # ---------------------------------------------------------
    # LOAD DATA
    # ---------------------------------------------------------

    products, stores, sales = load_data(
        PRODUCTS_FILE,
        STORES_FILE,
        SALES_FILE
    )

    # ---------------------------------------------------------
    # BUILD DETERMINISTIC METRICS
    # ---------------------------------------------------------

    metrics = build_metrics(
        products,
        stores,
        sales
    )

    # ---------------------------------------------------------
    # GEMINI
    # ---------------------------------------------------------

    gemini = GeminiService(
        GEMINI_API_KEY,
        LLM_MODEL
    )

    # ---------------------------------------------------------
    # LOCAL EMBEDDING INDEX
    # ---------------------------------------------------------

    if not INDEX_FILE.exists() and gemini.enabled:

        items = []
        texts = []

        for path in sorted(
            DOCS_DIR.glob("*.md")
        ):

            text = path.read_text(
                encoding="utf-8"
            )

            texts.append(
                (path, text)
            )

        embeddings = gemini.embed(
            [
                text
                for _, text in texts
            ]
        )

        if embeddings:

            for (
                (path, text),
                emb
            ) in zip(
                texts,
                embeddings
            ):

                items.append({
                    "id": path.stem,
                    "source": path.name,
                    "text": text,
                    "embedding": emb
                })

            try:

                INDEX_FILE.write_text(
                    json.dumps(items),
                    encoding="utf-8"
                )

            except OSError:

                pass

    # ---------------------------------------------------------
    # LOCAL RETRIEVER
    # ---------------------------------------------------------

    retriever = LocalRetriever(
        INDEX_FILE,
        gemini.embed
    )

    # =========================================================
    # FRONTEND
    # =========================================================

    @app.get("/")
    def index():

        return send_from_directory(
            FRONTEND_DIR,
            "index.html"
        )

    # =========================================================
    # SUMMARY API
    # =========================================================

    @app.get("/api/summary")
    def summary():

        d = dashboard(
            products,
            sales
        )

        d["attention_count"] = len(
            metrics["attention"]
        )

        d["gemini_enabled"] = (
            gemini.enabled
        )

        return jsonify(d)

    # =========================================================
    # ATTENTION API
    # =========================================================

    @app.get("/api/attention")
    def attention():

        return jsonify(
            metrics["attention"]
        )

    # =========================================================
    # PRODUCTS API
    # =========================================================

    @app.get("/api/products")
    def products_api():

        return jsonify(
            product_dashboard(
                products,
                sales
            )
        )

    # =========================================================
    # STORES API
    # =========================================================

    @app.get("/api/stores")
    def stores_api():

        return jsonify(
            store_intelligence(
                stores,
                products,
                sales
            )
        )

    # =========================================================
    # INVENTORY RUNWAY API
    # =========================================================

    @app.get("/api/runway")
    def runway():

        horizon = request.args.get(
            "horizon",
            default=30,
            type=int
        )

        allowed = [
            7,
            14,
            30,
            60,
            90
        ]

        if horizon not in allowed:

            return jsonify({
                "error": (
                    "Horizon must be one of "
                    "7, 14, 30, 60, or 90 days."
                )
            }), 400

        return jsonify(
            inventory_runway(
                products,
                sales,
                horizon
            )
        )

    # =========================================================
    # AI COPILOT API
    # =========================================================

    @app.post("/api/ask")
    def ask():

        body = request.get_json(
            silent=True
        ) or {}

        question = (
            body.get("question")
            or ""
        ).strip()

        if not question:

            return jsonify({
                "error":
                    "Please enter a question."
            }), 400

        # -----------------------------------------------------
        # DATA EVIDENCE
        # -----------------------------------------------------

        evidence = evidence_from_data(
            products,
            stores,
            sales,
            metrics,
            question
        )

        # -----------------------------------------------------
        # LOCAL DOCUMENT RETRIEVAL
        # -----------------------------------------------------

        retrieved = retriever.search(
            question,
            3
        )

        for i, item in enumerate(
            retrieved,
            start=len(evidence) + 1
        ):

            evidence.append({
                "id": f"E{i}",
                "type": "document",
                "text": item.get(
                    "text",
                    ""
                )
            })

        # -----------------------------------------------------
        # GROUNDED CONTEXT
        # -----------------------------------------------------

        context = "\n".join(
            f"[{e['id']}] {e['text']}"
            for e in evidence
        )

        # -----------------------------------------------------
        # GEMINI ANSWER
        # -----------------------------------------------------

        ai, warning = gemini.answer(
            question,
            context
        )

        if ai:

            result = ai

        else:

            result = deterministic_answer(
                question,
                products,
                stores,
                sales,
                metrics
            )

        # -----------------------------------------------------
        # RETURN REFERENCED EVIDENCE
        # -----------------------------------------------------

        evidence_ids = set(
            result.get(
                "evidence_ids",
                []
            )
        )

        referenced_evidence = [
            e
            for e in evidence
            if e["id"] in evidence_ids
        ]

        # If Gemini doesn't return valid IDs,
        # show a small evidence fallback.

        if not referenced_evidence:

            referenced_evidence = evidence[:4]

        result["evidence"] = (
            referenced_evidence
        )

        # -----------------------------------------------------
        # MODEL WARNING
        # -----------------------------------------------------

        if warning:

            result["warning"] = warning

        return jsonify(result)

    # =========================================================
    # HEALTH CHECK API
    # =========================================================

    @app.get("/api/health")
    def health():

        return jsonify({
            "status": "ok",
            "port": 8000,
            "records": len(sales),
            "products": len(products),
            "stores": len(stores),
            "latest_month":
                metrics.get(
                    "latest_month"
                )
        })

    # ---------------------------------------------------------
    # RETURN APP
    # ---------------------------------------------------------

    return app