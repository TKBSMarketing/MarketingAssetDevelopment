import os, sys, requests
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
TOKEN = os.getenv('META_ACCESS_TOKEN')
ACCOUNT_ID = os.getenv('META_AD_ACCOUNT_ID')

r = requests.get(f'https://graph.facebook.com/v21.0/act_{ACCOUNT_ID}/campaigns', params={
    'access_token': TOKEN,
    'fields': 'name,status,objective',
    'limit': 50
})
print(f'Account: act_{ACCOUNT_ID}')
print(f'Campaigns:')
for c in r.json().get('data', []):
    print(f"  {c['name']} | {c['status']}")
