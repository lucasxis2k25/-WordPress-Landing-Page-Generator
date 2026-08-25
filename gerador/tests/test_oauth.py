import urllib.request
import urllib.parse
import hmac
import hashlib
import time
import base64
import json

CK = 'ck_784c7e773683c8a0ffc5cdf6d27cd3c1f1ea2485'
CS = 'cs_659c08187c016bd05fbb7cff64139db7e850af05'
URL = 'https://DemoStore.com.br/wp-json/wc/v3/products'

def get_oauth_url(url, method='GET', extra_params=None):
    params = {
        'oauth_consumer_key': CK,
        'oauth_timestamp': str(int(time.time())),
        'oauth_nonce': str(int(time.time() * 1000)),
        'oauth_signature_method': 'HMAC-SHA1'
    }
    if extra_params:
        params.update(extra_params)
        
    sorted_params = sorted(params.items())
    param_string = '&'.join([f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(v, safe='')}" for k, v in sorted_params])
    
    base_string = f"{method.upper()}&{urllib.parse.quote(url, safe='')}&{urllib.parse.quote(param_string, safe='')}"
    secret = f"{CS}&"
    
    signature = base64.b64encode(hmac.new(secret.encode(), base_string.encode(), hashlib.sha1).digest()).decode()
    params['oauth_signature'] = signature
    
    final_query = '&'.join([f"{k}={urllib.parse.quote(v, safe='')}" for k, v in params.items()])
    return f"{url}?{final_query}"

auth_url = get_oauth_url(URL, extra_params={'slug': 'ventilador-exaustor-axial-250mm-fs-2-250-em'})
print(f"Testing OAuth URL: {auth_url}")

req = urllib.request.Request(auth_url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        print(f"[SUCCESS!] Returned {len(data)} products:")
        for p in data:
            print(f"  ID: {p['id']} - Name: {p['name']} - Slug: {p['slug']}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.read().decode()}")
except Exception as e:
    print(f"Error: {e}")
