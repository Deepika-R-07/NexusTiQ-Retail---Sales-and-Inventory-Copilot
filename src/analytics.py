from collections import defaultdict


def build_metrics(products, stores, sales):
    """
    Build deterministic sales, inventory and attention metrics.

    All calculations are performed locally from the supplied CSV data.
    Gemini is not used for numerical calculations.
    """

    pmap = {p["product_id"]: p for p in products}
    smap = {s["store_id"]: s for s in stores}

    # Product + store sales
    by_ps = defaultdict(int)

    # Product + month sales
    by_pm = defaultdict(int)

    # Store + month sales
    by_sm = defaultdict(int)

    for r in sales:
        by_ps[(r["product_id"], r["store_id"])] += r["quantity"]
        by_pm[(r["product_id"], r["date"][:7])] += r["quantity"]
        by_sm[(r["store_id"], r["date"][:7])] += r["quantity"]

    months = sorted(
        {r["date"][:7] for r in sales}
    )

    latest = months[-1] if months else None
    previous = months[-2] if len(months) > 1 else None

    attention = []

    for p in products:

        total = sum(
            by_ps[(p["product_id"], s["store_id"])]
            for s in stores
        )

        latest_qty = (
            by_pm[(p["product_id"], latest)]
            if latest
            else 0
        )

        prev_qty = (
            by_pm[(p["product_id"], previous)]
            if previous
            else 0
        )

        change = (
            None
            if prev_qty == 0
            else round(
                (latest_qty - prev_qty) / prev_qty * 100,
                1
            )
        )

        # Latest-month velocity.
        # Dataset represents a monthly period,
        # so 4 weeks is used as a deterministic approximation.
        weekly_velocity = (
            latest_qty / 4.0
            if latest_qty
            else 0
        )

        if weekly_velocity:
            days_cover = (
                p["stock"] / weekly_velocity * 7
            )
        else:
            days_cover = 999

        # ---------------------------------------------------------
        # 1. CRITICAL STOCK-OUT
        # ---------------------------------------------------------

        if p["stock"] <= 0:
            attention.append({
                "type": "STOCKOUT",
                "severity": "critical",
                "product": p["name"],
                "product_id": p["product_id"],
                "evidence": {
                    "stock": p["stock"],
                    "reorder_point": p["reorder_point"]
                },
                "action": (
                    "Immediate replenishment required; "
                    "confirm supplier availability."
                )
            })

        # ---------------------------------------------------------
        # 2. LOW STOCK
        # ---------------------------------------------------------

        elif p["stock"] <= p["reorder_point"]:
            attention.append({
                "type": "LOW_STOCK",
                "severity": "high",
                "product": p["name"],
                "product_id": p["product_id"],
                "evidence": {
                    "stock": p["stock"],
                    "reorder_point": p["reorder_point"]
                },
                "action": (
                    "Replenish now and confirm supplier "
                    "lead time."
                )
            })

        # ---------------------------------------------------------
        # 3. STOCK-OUT RISK
        # ---------------------------------------------------------

        elif days_cover <= p["lead_time_days"] + 3:
            attention.append({
                "type": "STOCKOUT_RISK",
                "severity": "high",
                "product": p["name"],
                "product_id": p["product_id"],
                "evidence": {
                    "stock": p["stock"],
                    "weekly_velocity": round(
                        weekly_velocity,
                        1
                    ),
                    "estimated_days_cover": round(
                        days_cover,
                        1
                    ),
                    "lead_time_days": p["lead_time_days"]
                },
                "action": (
                    "Place a replenishment order before "
                    "the projected stock-out window."
                )
            })

        # ---------------------------------------------------------
        # 4. NO MOVEMENT
        # ---------------------------------------------------------

        if latest_qty == 0 and p["stock"] > 0:
            attention.append({
                "type": "NO_MOVEMENT",
                "severity": "medium",
                "product": p["name"],
                "product_id": p["product_id"],
                "evidence": {
                    "stock": p["stock"],
                    "units_sold_latest_month": 0
                },
                "action": (
                    "Review shelf placement, promotion and "
                    "assortment; consider a small markdown."
                )
            })

        # ---------------------------------------------------------
        # 5. SALES DROP
        # ---------------------------------------------------------

        elif (
            latest_qty > 0
            and change is not None
            and change <= -30
        ):
            attention.append({
                "type": "SALES_DROP",
                "severity": "medium",
                "product": p["name"],
                "product_id": p["product_id"],
                "evidence": {
                    "latest_units": latest_qty,
                    "previous_units": prev_qty,
                    "change_pct": change
                },
                "action": (
                    "Check price, availability and local demand "
                    "before increasing stock."
                )
            })

        # ---------------------------------------------------------
        # 6. SALES SPIKE
        # ---------------------------------------------------------

        elif (
            latest_qty > 0
            and change is not None
            and change >= 40
        ):
            attention.append({
                "type": "SALES_SPIKE",
                "severity": "medium",
                "product": p["name"],
                "product_id": p["product_id"],
                "evidence": {
                    "latest_units": latest_qty,
                    "previous_units": prev_qty,
                    "change_pct": change
                },
                "action": (
                    "Check whether the spike is sustained and "
                    "protect availability with a small replenishment."
                )
            })

        # ---------------------------------------------------------
        # 7. OVERSTOCK
        # ---------------------------------------------------------

        if total < 3 and p["stock"] > 20:
            attention.append({
                "type": "OVERSTOCK",
                "severity": "low",
                "product": p["name"],
                "product_id": p["product_id"],
                "evidence": {
                    "stock": p["stock"],
                    "units_sold_all_period": total
                },
                "action": (
                    "Avoid reordering; test a promotion or "
                    "reduce shelf allocation."
                )
            })

    return {
        "months": months,
        "latest_month": latest,
        "previous_month": previous,
        "attention": attention,
        "products": products,
        "stores": stores,
        "sales_count": len(sales),
    }


def product_performance(
    products,
    sales,
    product_name=None,
    month=None
):
    """
    Calculate performance for one product.

    Supports:
    - Product name
    - Product ID
    - Partial/fuzzy product search
    - Month filtering
    """

    target = None

    # ---------------------------------------------------------
    # Find product
    # ---------------------------------------------------------

    if product_name:

        q = product_name.strip().lower()

        exact = [
            p
            for p in products
            if (
                p["name"].lower() == q
                or p["product_id"].lower() == q
            )
        ]

        fuzzy = [
            p
            for p in products
            if (
                q in p["name"].lower()
                or q in p["product_id"].lower()
            )
        ]

        matches = exact or fuzzy

        if len(matches) != 1:
            return {
                "status": (
                    "ambiguous"
                    if matches
                    else "not_found"
                ),
                "matches": [
                    p["name"]
                    for p in matches
                ]
            }

        target = matches[0]

    # ---------------------------------------------------------
    # Determine latest month
    # ---------------------------------------------------------

    if month is None:

        months = sorted(
            {r["date"][:7] for r in sales}
        )

        month = (
            months[-1]
            if months
            else None
        )

    # ---------------------------------------------------------
    # If no product was selected
    # ---------------------------------------------------------

    if target is None:
        return {
            "status": "not_found",
            "matches": []
        }

    # ---------------------------------------------------------
    # Filter sales
    # ---------------------------------------------------------

    rows = [
        r
        for r in sales
        if (
            r["product_id"] == target["product_id"]
            and (
                month is None
                or r["date"].startswith(month)
            )
        )
    ]

    # ---------------------------------------------------------
    # Calculate metrics
    # ---------------------------------------------------------

    units = sum(
        r["quantity"]
        for r in rows
    )

    revenue = sum(
        r["quantity"] * r["unit_price"]
        for r in rows
    )

    return {
        "status": "ok",
        "product": target,
        "month": month,
        "units": units,
        "revenue": round(revenue, 2),
        "transactions": len(rows)
    }


def dashboard(products, sales):
    """
    Calculate top-level dashboard KPIs.
    """

    months = sorted(
        {r["date"][:7] for r in sales}
    )

    latest = (
        months[-1]
        if months
        else None
    )

    previous = (
        months[-2]
        if len(months) > 1
        else None
    )

    # ---------------------------------------------------------
    # Latest month revenue
    # ---------------------------------------------------------

    rev_latest = (
        sum(
            r["quantity"] * r["unit_price"]
            for r in sales
            if r["date"].startswith(latest)
        )
        if latest
        else 0
    )

    # ---------------------------------------------------------
    # Previous month revenue
    # ---------------------------------------------------------

    rev_prev = (
        sum(
            r["quantity"] * r["unit_price"]
            for r in sales
            if r["date"].startswith(previous)
        )
        if previous
        else 0
    )

    # ---------------------------------------------------------
    # Revenue percentage change
    # ---------------------------------------------------------

    pct = (
        None
        if rev_prev == 0
        else round(
            (
                (rev_latest - rev_prev)
                / rev_prev
                * 100
            ),
            1
        )
    )

    return {
        "latest_month": latest,
        "revenue_latest": round(
            rev_latest,
            2
        ),
        "revenue_previous": round(
            rev_prev,
            2
        ),
        "revenue_change_pct": pct,
        "product_count": len(products)
    }


def product_dashboard(products, sales):
    """
    Return enriched product information for the frontend.

    Provides:
    - Latest month units
    - Previous month units
    - Latest revenue
    - Previous revenue
    - Sales change percentage
    - Weekly velocity
    - Days of inventory cover
    - Minimum top-up quantity
    """

    months = sorted(
        {r["date"][:7] for r in sales}
    )

    latest = (
        months[-1]
        if months
        else None
    )

    previous = (
        months[-2]
        if len(months) > 1
        else None
    )

    result = []

    for p in products:

        # ---------------------------------------------------------
        # Latest month sales
        # ---------------------------------------------------------

        latest_rows = [
            r
            for r in sales
            if (
                r["product_id"] == p["product_id"]
                and latest
                and r["date"].startswith(latest)
            )
        ]

        # ---------------------------------------------------------
        # Previous month sales
        # ---------------------------------------------------------

        previous_rows = [
            r
            for r in sales
            if (
                r["product_id"] == p["product_id"]
                and previous
                and r["date"].startswith(previous)
            )
        ]

        # ---------------------------------------------------------
        # Units
        # ---------------------------------------------------------

        latest_units = sum(
            r["quantity"]
            for r in latest_rows
        )

        previous_units = sum(
            r["quantity"]
            for r in previous_rows
        )

        # ---------------------------------------------------------
        # Revenue
        # ---------------------------------------------------------

        latest_revenue = sum(
            r["quantity"] * r["unit_price"]
            for r in latest_rows
        )

        previous_revenue = sum(
            r["quantity"] * r["unit_price"]
            for r in previous_rows
        )

        # ---------------------------------------------------------
        # Sales change
        # ---------------------------------------------------------

        change_pct = (
            None
            if previous_units == 0
            else round(
                (
                    latest_units
                    - previous_units
                )
                / previous_units
                * 100,
                1
            )
        )

        # ---------------------------------------------------------
        # Weekly velocity
        # ---------------------------------------------------------

        weekly_velocity = (
            latest_units / 4
            if latest_units > 0
            else 0
        )

        # ---------------------------------------------------------
        # Days cover
        # ---------------------------------------------------------

        if weekly_velocity > 0:

            days_cover = round(
                p["stock"]
                / weekly_velocity
                * 7,
                1
            )

        else:
            days_cover = None

        # ---------------------------------------------------------
        # Minimum top-up
        # ---------------------------------------------------------

        minimum_top_up = max(
            p["reorder_point"] - p["stock"],
            0
        )

        # ---------------------------------------------------------
        # Add enriched product
        # ---------------------------------------------------------

        result.append({
            **p,

            "latest_month": latest,

            "latest_units": latest_units,

            "previous_units": previous_units,

            "latest_revenue": round(
                latest_revenue,
                2
            ),

            "previous_revenue": round(
                previous_revenue,
                2
            ),

            "change_pct": change_pct,

            "weekly_velocity": round(
                weekly_velocity,
                2
            ),

            "days_cover": days_cover,

            "minimum_top_up": minimum_top_up
        })

    return result


def inventory_runway(
    products,
    sales,
    horizon_days=30
):
    """
    Calculate inventory runway for the selected
    planning horizon.

    Supported horizons:
    7 / 14 / 30 / 60 / 90 days
    """

    # ---------------------------------------------------------
    # Validate horizon
    # ---------------------------------------------------------

    allowed_horizons = [7, 14, 30, 60, 90]

    if horizon_days not in allowed_horizons:
        horizon_days = 30

    # ---------------------------------------------------------
    # Determine latest month
    # ---------------------------------------------------------

    months = sorted(
        {r["date"][:7] for r in sales}
    )

    latest_month = (
        months[-1]
        if months
        else None
    )

    results = []

    for p in products:

        # ---------------------------------------------------------
        # Latest month units
        # ---------------------------------------------------------

        latest_units = 0

        if latest_month:

            latest_units = sum(
                r["quantity"]
                for r in sales
                if (
                    r["product_id"]
                    == p["product_id"]
                    and r["date"].startswith(
                        latest_month
                    )
                )
            )

        # ---------------------------------------------------------
        # Velocity
        # ---------------------------------------------------------

        weekly_velocity = (
            latest_units / 4.0
            if latest_units
            else 0
        )

        daily_velocity = (
            weekly_velocity / 7
            if weekly_velocity
            else 0
        )

        # ---------------------------------------------------------
        # Projection
        # ---------------------------------------------------------

        if daily_velocity > 0:

            days_cover = round(
                p["stock"] / daily_velocity,
                1
            )

            projected_demand = round(
                daily_velocity * horizon_days,
                1
            )

            projected_ending_stock = round(
                p["stock"] - projected_demand,
                1
            )

            exhausts_before_horizon = (
                days_cover <= horizon_days
            )

        else:

            days_cover = None

            projected_demand = 0

            projected_ending_stock = p["stock"]

            exhausts_before_horizon = False

        # ---------------------------------------------------------
        # Status
        # ---------------------------------------------------------

        if p["stock"] <= 0:

            status = "CRITICAL"

        elif latest_units == 0:

            status = "NO_MOVEMENT"

        elif exhausts_before_horizon:

            status = "AT_RISK"

        else:

            status = "HEALTHY"

        # ---------------------------------------------------------
        # Result
        # ---------------------------------------------------------

        results.append({
            "product": p["name"],
            "product_id": p["product_id"],

            "stock": p["stock"],

            "reorder_point": p["reorder_point"],

            "latest_units": latest_units,

            "weekly_velocity": round(
                weekly_velocity,
                2
            ),

            "daily_velocity": round(
                daily_velocity,
                3
            ),

            "days_cover": days_cover,

            "planning_horizon": horizon_days,

            "projected_demand": projected_demand,

            "projected_ending_stock": projected_ending_stock,

            "exhausts_before_horizon": (
                exhausts_before_horizon
            ),

            "status": status
        })

    return results


def store_intelligence(stores, products, sales):
    """
    Calculate deterministic store-level performance.

    Provides:
    - Store name
    - Total units sold
    - Total revenue
    - Top-selling product
    - Top product units

    All calculations are performed locally.
    Gemini is not used for numerical calculations.
    """

    pmap = {
        p["product_id"]: p
        for p in products
    }

    results = []

    for store in stores:

        store_id = store["store_id"]

        # ---------------------------------------------------------
        # Sales for this store
        # ---------------------------------------------------------

        rows = [
            r
            for r in sales
            if r["store_id"] == store_id
        ]

        # ---------------------------------------------------------
        # Total units
        # ---------------------------------------------------------

        units = sum(
            r["quantity"]
            for r in rows
        )

        # ---------------------------------------------------------
        # Total revenue
        # ---------------------------------------------------------

        revenue = sum(
            r["quantity"] * r["unit_price"]
            for r in rows
        )

        # ---------------------------------------------------------
        # Product sales
        # ---------------------------------------------------------

        product_units = defaultdict(int)

        for r in rows:
            product_units[
                r["product_id"]
            ] += r["quantity"]

        # ---------------------------------------------------------
        # Top product
        # ---------------------------------------------------------

        if product_units:

            top_product_id = max(
                product_units,
                key=product_units.get
            )

            top_product = pmap[
                top_product_id
            ]["name"]

            top_product_units = product_units[
                top_product_id
            ]

        else:

            top_product = "No sales"

            top_product_units = 0

        # ---------------------------------------------------------
        # Store result
        # ---------------------------------------------------------

        results.append({
            "store_id": store_id,

            "store_name": store["name"],

            "total_units": units,

            "total_revenue": round(
                revenue,
                2
            ),

            "top_product": top_product,

            "top_product_units": top_product_units
        })

    return results