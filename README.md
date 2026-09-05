TRACK_ID=PS03

Retail Sales and Inventory Copilot:



Demo link:https://drive.google.com/file/d/1bt2KOaqgbL3FLKlSb3Cf0jqxOq51vSLk/view?usp=sharing


An AI-powered decision-support application that helps retail store managers monitor sales, identify inventory risks, understand store performance, and make faster inventory decisions using deterministic analytics and a grounded Gemini-powered AI Copilot.


Overview

Retail managers often need to make decisions using sales data, inventory levels, product performance, and store-level information. Manually analyzing this information can be time-consuming and may cause important risks such as stock-outs, overstocking, declining sales, or products with no movement to be missed.

The Retail Sales and Inventory Copilot brings these insights together in one dashboard and converts raw retail data into actionable business recommendations.

The system combines:

- Deterministic sales and inventory analytics
- Automated risk detection
- Inventory runway calculations
- Store intelligence
- Evidence-based AI recommendations
- Gemini LLM reasoning
- Gemini embeddings for local document retrieval
- Graceful fallback when AI services are unavailable

Problem Statement

Retail store managers need a simple way to answer questions such as:

- Which products require immediate attention?
- Which products are at risk of stock-out?
- Which products are overstocked?
- Which products have declining sales?
- Which products are performing well?
- How much inventory may be required in the coming days?
- Which stores and products are contributing most to sales?
- What action should the manager take?

The application provides these answers through a manager-friendly decision dashboard.

Solution

The application follows a hybrid architecture where deterministic analytics handle numerical calculations and risk detection, while Gemini is used for natural-language reasoning and recommendations.

The overall flow is:

CSV Data → Deterministic Analytics → Risk Detection → Evidence Layer → Gemini Copilot → Manager Action

This separation ensures that important business calculations are not delegated entirely to the LLM.

Key Features

 1. Executive Overview

Provides a quick view of:

- Latest revenue
- Revenue change
- Number of attention items
- Top-performing products
- Current inventory risks
- Key business insights

 2. Risk Center

Automatically detects important inventory and sales risks such as:

- Stock-outs
- Low stock
- Stock-out risk
- Sales drops
- Sales spikes
- No-movement inventory
- Overstock

Each risk is presented with useful context to support manager decisions.

3. Inventory Intelligence

Provides:

- Current stock
- Reorder point
- Weekly sales velocity
- Days of inventory cover
- Inventory health
- Minimum top-up quantity
- Inventory runway projections

Supported planning horizons include:

- 7 days
- 14 days
- 30 days
- 60 days
- 90 days

4. Sales Intelligence

Helps managers understand:

- Product sales performance
- Latest-month units
- Previous-month units
- Revenue
- Sales change percentage
- Sales spikes
- Sales declines
- Product-level performance

 5. Store Intelligence

Provides store-level information including:

- Store sales
- Store units
- Revenue contribution
- Top-performing products
- Store performance comparison

6. Inventory Capital Risk

Highlights inventory that may be tying up working capital because of:

- Overstock
- No sales movement
- Excess inventory

The system uses available inventory and sales data instead of inventing unavailable cost information.

7. Planning

Provides forward-looking inventory planning based on:

- Current stock
- Historical sales velocity
- Reorder points
- Expected demand
- Inventory runway

8. AI Copilot

Managers can ask natural-language questions such as:

- "What needs attention today?"
- "Which products are at stock-out risk?"
- "Which products are overstocked?"
- "How is Coffee Beans performing?"
- "What should I replenish?"
- "Which store is performing best?"

The Copilot uses Gemini to generate concise manager-friendly answers grounded in the available business evidence.

AI and Grounding Architecture

The AI layer is designed to avoid unsupported recommendations.

The system provides Gemini with evidence collected from:

- Sales data
- Product data
- Store data
- Deterministic analytics
- Local business documents

Gemini is instructed to:

1. Answer only from supplied evidence.
2. Never invent numerical values.
3. Never invent products, stores, sales, or business conditions.
4. Cite factual claims using evidence IDs.
5. Clearly state when available data is insufficient.
6. Separate assumptions from factual findings.
7. Provide recommendations supported by available evidence.

Example evidence format:

[E1] Coffee Beans has 8 units in stock and a reorder point of 12.

[E2] Coffee Beans sales decreased from 15 units to 5 units.

The AI response can reference these evidence items when explaining its recommendation.

Technology Stack

 Backend

- Python
- Flask
- Pandas-compatible CSV data processing
- Deterministic analytics modules

 AI

- Google Gemini API
- Gemini LLM
- Gemini Embeddings
- `gemini-embedding-001`

 Frontend

- HTML
- CSS
- JavaScript
- Responsive single-page dashboard

 Data

- CSV datasets
- Markdown business documents
- Local retrieval index

Project Structure


retail-sales-inventory-copilot/
│
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
├── tests_smoke.py
├── .gitignore
│
├── src/
│   ├── __init__.py
│   ├── server.py
│   ├── data.py
│   ├── analytics.py
│   ├── copilot.py
│   ├── gemini.py
│   ├── retrieval.py
│   └── config.py
│
├── frontend/
│   └── index.html
│
├── data/
│   ├── products.csv
│   ├── stores.csv
│   ├── sales.csv
│   │
│   └── documents/
│       ├── inventory_policy.md
│       └── analysis_notes.md
│
└── scripts/
    └── build_index.py

Data Used:

The project uses generated retail data containing:

Product information
Store information
Historical sales
Inventory levels
Reorder points
Monthly sales activity

The dataset is intentionally small and focused so that the complete application can be run locally without external data services.

Generated Documents

The project also contains local business documents used to ground the AI Copilot.

Examples include:

Inventory policy
Business analysis notes

These documents are used as supporting evidence for AI-generated recommendations.

Gemini API Configuration

The application uses the Gemini API for:

Natural-language Copilot responses
Document embeddings

The application expects the Gemini API key through the environment variable:

GEMINI_API_KEY

Do not store the API key in the source code, README, GitHub repository, or .env files committed to Git.

How to Run
1. Clone the repository
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd retail-sales-inventory-copilot
2. Install dependencies
pip install -r requirements.txt
3. Configure Gemini API Key

Set the environment variable:

Windows PowerShell
$env:GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
Linux / macOS
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
4. Start the application
python app.py

The application runs on:

http://localhost:8000

The backend and frontend are served together through the Python application.

One-Command Startup

After installing the dependencies and configuring the Gemini API key, the application can be started with:

python app.py

No separate frontend server or build command is required.

Health Check

The application provides a health endpoint:

http://localhost:8000/api/health

It returns information about:

Application status
Port
Number of sales records
Number of products
Number of stores
Latest data month
Testing

A lightweight smoke test is included:

python tests_smoke.py

The test validates important deterministic analytics and application behavior.

Example Manager Questions

The AI Copilot can be tested with questions such as:

What needs attention today?
Which products are at stock-out risk?
Which products are overstocked?
How is Coffee Beans performing?
Which product has the biggest sales increase?
Which store is performing best?

The application also handles unsupported questions by indicating when the available business data is insufficient rather than inventing an answer.

Example Business Insights

The current generated dataset can identify situations such as:

Coffee Beans having low stock
Coffee Beans experiencing a sales decline
Green Tea experiencing a sales increase
Shampoo experiencing a significant sales decline
Notebook having no recent movement and excess stock
USB Cable having low stock
Water Bottle showing strong sales growth
Desk Lamp having no recent movement and excess stock

These insights are calculated from the supplied data rather than generated by the LLM.

Engineering Approach

The application separates deterministic business logic from AI reasoning.

Deterministic Layer

The deterministic layer is responsible for:

Revenue calculations
Sales comparisons
Inventory calculations
Days of cover
Sales velocity
Risk detection
Reorder calculations
Inventory runway
Store-level metrics
AI Layer

Gemini is responsible for:

Understanding natural-language questions
Summarizing supplied evidence
Explaining business findings
Generating manager-friendly recommendations

This architecture reduces the risk of hallucinated business numbers.

Error Handling

The application is designed to fail safely.

If the Gemini API is unavailable or the API key is not configured:

The application remains usable.
Deterministic analytics continue to work.
The user receives a clear warning.
The system does not invent AI-generated information.

If an unsupported question is asked:

The system uses available evidence.
If sufficient evidence is unavailable, it clearly indicates that the data is insufficient.
Decision-Making Workflow

The application supports the following manager workflow:

Monitor
   ↓
Identify Risk
   ↓
Analyze Evidence
   ↓
Understand Business Impact
   ↓
Ask AI Copilot
   ↓
Take Action

This allows managers to move from raw data to an actionable decision without manually analyzing multiple datasets.

Product Value

The Retail Sales and Inventory Copilot helps managers:

Detect inventory risks earlier
Reduce stock-out risk
Identify slow-moving inventory
Identify sales changes
Understand store performance
Prioritize inventory actions
Make evidence-based decisions
Save time during daily retail operations
Safety and Grounding

The application is designed around grounded AI principles.

Gemini does not receive unrestricted authority over business decisions.

Instead:

Business Data
     ↓
Deterministic Calculations
     ↓
Evidence
     ↓
Gemini Reasoning
     ↓
Grounded Recommendation

The system is explicitly instructed not to fabricate unsupported facts.

When evidence is insufficient, the Copilot should state that the available data cannot answer the question confidently.

Future Enhancements

Potential future improvements include:

Supplier lead-time integration
Store-specific replenishment recommendations
Unit-cost-based working-capital analysis
Purchase-order recommendations
More advanced demand forecasting
Promotion impact analysis
Seasonal demand analysis
Multi-store inventory transfer recommendations
User authentication and role-based access


