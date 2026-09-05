"""Run once before submission to create the committed Gemini embedding index.
Requires GEMINI_API_KEY. The judge does not need to run this script.
"""
import json
from pathlib import Path
from google import genai

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'data/documents'
OUT=ROOT/'data/embedding_index.json'
key=__import__('os').getenv('GEMINI_API_KEY')
if not key:
    raise SystemExit('Set GEMINI_API_KEY first.')
client=genai.Client(api_key=key)
items=[]
for path in sorted(DOCS.glob('*.md')):
    text=path.read_text(encoding='utf-8')
    r=client.models.embed_content(model='gemini-embedding-001', contents=text)
    items.append({'id':path.stem,'source':path.name,'text':text,'embedding':r.embeddings[0].values})
OUT.write_text(json.dumps(items), encoding='utf-8')
print(f'Wrote {len(items)} embeddings to {OUT}')
