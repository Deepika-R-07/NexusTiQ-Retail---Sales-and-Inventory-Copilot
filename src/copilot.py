from .analytics import product_performance


def evidence_from_data(products, stores, sales, metrics, query):
    q = query.lower()

    evidence = []
    eid = 1

    # Add attention alerts as evidence
    for a in metrics["attention"][:8]:
        evidence.append({
            "id": f"E{eid}",
            "type": "alert",
            "text": (
                f"{a['product']} ({a['type']}): "
                f"{a['evidence']}; action={a['action']}"
            )
        })
        eid += 1

    # Add directly relevant product performance evidence
    candidates = [
        p for p in products
        if p["name"].lower() in q
    ]

    if not candidates:
        for p in products:
            words = [
                w for w in p["name"].lower().split()
                if len(w) > 3
            ]

            if any(w in q for w in words):
                candidates.append(p)

    if candidates:
        p = candidates[0]
        result = product_performance(
            products,
            sales,
            p["name"]
        )

        evidence.append({
            "id": f"E{eid}",
            "type": "metric",
            "text": (
                f"{p['name']}: "
                f"latest month {result.get('month')}, "
                f"units={result.get('units')}, "
                f"revenue=₹{result.get('revenue'):.2f}, "
                f"current stock={p['stock']}, "
                f"reorder point={p['reorder_point']}."
            )
        })

        eid += 1

    # Global dataset evidence
    total_rev = sum(
        r["quantity"] * r["unit_price"]
        for r in sales
    )

    total_units = sum(
        r["quantity"]
        for r in sales
    )

    evidence.append({
        "id": f"E{eid}",
        "type": "dataset",
        "text": (
            f"Dataset covers {len(products)} products, "
            f"{len(stores)} stores, "
            f"{len(sales)} sales rows; "
            f"total units={total_units}; "
            f"total recorded revenue=₹{round(total_rev, 2)}; "
            f"latest month={metrics['latest_month']}."
        )
    })

    return evidence


def deterministic_answer(
    question,
    products,
    stores,
    sales,
    metrics
):
    q = question.lower()

    # ---------------------------------------------------------
    # ATTENTION / ALERT QUESTIONS
    # ---------------------------------------------------------
    if any(
        x in q
        for x in [
            "attention",
            "today",
            "need",
            "urgent",
            "alert"
        ]
    ):
        alerts = metrics["attention"][:10]

        if not alerts:
            return {
                "answer": (
                    "No attention items were detected "
                    "from the current rules and data."
                ),
                "evidence_ids": [],
                "assumptions": [],
                "confidence": "high"
            }

        lines = []
        ids = []

        for i, a in enumerate(alerts, 1):
            ids.append(f"E{i}")

            lines.append(
                f"{i}. {a['product']} — {a['type']}; "
                f"evidence: {a['evidence']}; "
                f"recommended action: {a['action']}"
            )

        return {
            "answer": "\n".join(lines),
            "evidence_ids": ids,
            "assumptions": [
                "Rules use current stock, recorded sales, "
                "a 4-week monthly velocity proxy, and "
                "supplier lead time where available."
            ],
            "confidence": "high"
        }

    # ---------------------------------------------------------
    # PRODUCT PERFORMANCE QUESTIONS
    # ---------------------------------------------------------
    for p in products:
        if p["name"].lower() in q:
            r = product_performance(
                products,
                sales,
                p["name"]
            )

            return {
                "answer": (
                    f"{p['name']} sold {r['units']} units "
                    f"and generated ₹{r['revenue']:.2f} "
                    f"in {r['month']}. "
                    f"Current stock is {p['stock']} and "
                    f"reorder point is {p['reorder_point']}."
                ),
                "evidence_ids": [],
                "assumptions": [],
                "confidence": "high"
            }

    # ---------------------------------------------------------
    # OVERSTOCK / NO MOVEMENT QUESTIONS
    # ---------------------------------------------------------
    if (
        "overstock" in q
        or "not moving" in q
        or "slow" in q
    ):
        a = [
            x for x in metrics["attention"]
            if x["type"] in (
                "OVERSTOCK",
                "NO_MOVEMENT"
            )
        ]

        if not a:
            return {
                "answer": (
                    "The current data does not identify "
                    "any products meeting the "
                    "overstock/no-movement rules."
                ),
                "evidence_ids": [],
                "assumptions": [],
                "confidence": "high"
            }

        return {
            "answer": "\n".join(
                f"{x['product']}: {x['evidence']}. "
                f"Action: {x['action']}"
                for x in a
            ),
            "evidence_ids": [],
            "assumptions": [
                "Overstock is defined as more than "
                "20 units on hand with fewer than "
                "3 units sold across the available period."
            ],
            "confidence": "high"
        }

    # ---------------------------------------------------------
    # STOCK / STOCKOUT QUESTIONS
    # ---------------------------------------------------------
    if (
        "stock" in q
        or "running out" in q
        or "stockout" in q
    ):
        a = [
            x for x in metrics["attention"]
            if x["type"] in (
                "LOW_STOCK",
                "STOCKOUT_RISK"
            )
        ]

        if not a:
            return {
                "answer": (
                    "No stock-out risk was detected "
                    "by the current deterministic rules."
                ),
                "evidence_ids": [],
                "assumptions": [],
                "confidence": "high"
            }

        return {
            "answer": "\n".join(
                f"{x['product']}: {x['type']} — "
                f"{x['evidence']}. "
                f"Action: {x['action']}"
                for x in a
            ),
            "evidence_ids": [],
            "assumptions": [
                "Stock-out risk uses on-hand stock "
                "versus reorder point and estimated "
                "days of cover based on the latest month."
            ],
            "confidence": "high"
        }

    # ---------------------------------------------------------
    # UNSUPPORTED QUESTIONS
    # ---------------------------------------------------------
    return {
        "answer": (
            "I cannot answer that reliably from the "
            "available sales and stock data. Try asking "
            "about stock-outs, overstock, sales spikes/drops, "
            "or a named product's monthly performance."
        ),
        "evidence_ids": [],
        "assumptions": [
            "No supporting metric was identified "
            "for the requested question."
        ],
        "confidence": "low"
    }