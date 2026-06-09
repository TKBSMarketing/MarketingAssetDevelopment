import os, sys, requests, json
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
TOKEN = os.getenv('META_ACCESS_TOKEN')
ACCOUNT_ID = os.getenv('META_AD_ACCOUNT_ID')
BASE = 'https://graph.facebook.com/v21.0'

print(f'Account ID: act_{ACCOUNT_ID}')
print(f'Token: {TOKEN[:15]}...{TOKEN[-10:]}')

# Test 1: Can the token access this account?
print('\n=== TEST 1: Account Access ===')
r = requests.get(f'{BASE}/act_{ACCOUNT_ID}', params={
    'access_token': TOKEN,
    'fields': 'name,account_status,currency'
})
print(f'Status: {r.status_code}')
print(json.dumps(r.json(), indent=2))

# Test 2: What accounts does this token have access to?
print('\n=== TEST 2: All Accessible Ad Accounts ===')
r2 = requests.get(f'{BASE}/me/adaccounts', params={
    'access_token': TOKEN,
    'fields': 'name,account_id,account_status',
    'limit': 50
})
print(f'Status: {r2.status_code}')
data = r2.json()
if 'data' in data:
    for acct in data['data']:
        marker = ' <-- THIS ONE' if str(ACCOUNT_ID) in acct.get('id', '') else ''
        print(f"  {acct.get('id')} | {acct.get('name', 'Unknown')} | Status: {acct.get('account_status')}{marker}")
else:
    print(json.dumps(data, indent=2))
