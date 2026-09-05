import sys
sys.path.insert(0, '.')
from src.data import load_data
from src.config import PRODUCTS_FILE, STORES_FILE, SALES_FILE
from src.analytics import build_metrics
p,s,sa=load_data(PRODUCTS_FILE, STORES_FILE, SALES_FILE)
m=build_metrics(p,s,sa)
assert len(p)==8 and len(s)==3 and len(sa)>20
assert any(x['type']=='STOCKOUT_RISK' for x in m['attention']) or any(x['type']=='LOW_STOCK' for x in m['attention'])
print('smoke test passed')
