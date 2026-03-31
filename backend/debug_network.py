"""Debug script to diagnose network/DNS issues from inside the container.

Usage:
    docker compose exec bmi-backend python backend/debug_network.py
"""
import socket
import os
import sys
import urllib.request
import urllib.error

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

# 1. resolv.conf
section("/etc/resolv.conf")
try:
    with open("/etc/resolv.conf") as f:
        print(f.read().strip())
except Exception as e:
    print(f"Could not read: {e}")

# 2. DNS resolution
section("DNS Resolution")
hosts = [
    "google.com",
    "pypi.org",
    "oai-gopoc-prod-northcentralus-001.openai.azure.com",
]
for host in hosts:
    try:
        ip = socket.gethostbyname(host)
        print(f"  {host} -> {ip}")
    except Exception as e:
        print(f"  {host} -> FAILED: {e}")

# 3. HTTP connectivity
section("HTTP Connectivity")
urls = [
    "https://google.com",
    "https://pypi.org",
    "https://oai-gopoc-prod-northcentralus-001.openai.azure.com",
]
for url in urls:
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        print(f"  {url} -> HTTP {resp.status}")
    except urllib.error.HTTPError as e:
        print(f"  {url} -> HTTP {e.code} (reachable, server returned error)")
    except Exception as e:
        print(f"  {url} -> FAILED: {type(e).__name__}: {e}")

# 4. Environment variables related to proxy/network
section("Proxy / Network Env Vars")
proxy_vars = [
    "HTTP_PROXY", "http_proxy",
    "HTTPS_PROXY", "https_proxy",
    "NO_PROXY", "no_proxy",
    "ALL_PROXY", "all_proxy",
]
found_any = False
for var in proxy_vars:
    val = os.environ.get(var)
    if val:
        print(f"  {var}={val}")
        found_any = True
if not found_any:
    print("  (none set)")

# 5. Azure OpenAI config check
section("Azure OpenAI Config (from settings)")
try:
    sys.path.insert(0, "/app")
    from backend.app.config import get_settings
    s = get_settings()
    print(f"  llm_backend       = {s.llm_backend}")
    print(f"  azure_endpoint    = {s.azure_openai_endpoint}")
    print(f"  azure_deployment  = {s.azure_openai_deployment}")
    print(f"  azure_api_version = {s.azure_openai_api_version}")
    print(f"  azure_api_key     = {'***' + s.azure_openai_api_key[-4:] if s.azure_openai_api_key else '(not set)'}")
    print(f"  ollama_base_url   = {s.ollama_base_url}")
    print(f"  ollama_model      = {s.ollama_model}")
except Exception as e:
    print(f"  Could not load settings: {e}")

# 6. Actual LLM call test
section("LLM Factory Test")
try:
    from backend.app.llm.factory import get_chat_model
    from backend.app.config import get_settings
    s = get_settings()
    
    # Test with the configured default backend
    backend_name = s.llm_backend.strip().lower()
    print(f"  Testing with default backend: {backend_name}")
    model = get_chat_model(s)
    print(f"  Model created: {type(model).__name__}")
    
    # Try a minimal invoke
    print(f"  Sending test message...")
    response = model.invoke("Say 'hello' in one word.")
    print(f"  Response: {response.content[:200]}")
    print(f"  SUCCESS")
except Exception as e:
    print(f"  FAILED: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

section("Done")
