"""Minimal KC100 local client. Usage: kc100.py <ip> <module> <method> [json-args]  (e.g. led get_status)"""
import base64, hashlib, json, os, ssl, sys, urllib.parse, urllib.request, uuid

def enc(b):
    k = 171; o = bytearray()
    for c in b:
        k ^= c; o.append(k)
    return bytes(o)

def dec(b):
    k = 171; o = bytearray()
    for c in b:
        o.append(c ^ k); k = c
    return bytes(o)

def call(ip, module, method, args=None, auth=None):
    msg = {"smartlife.cam.ipcamera." + module: {method: args or {}}, "context": {"source": str(uuid.uuid4())}}
    body = urllib.parse.urlencode({"content": base64.b64encode(enc(json.dumps(msg, separators=(",", ":")).encode())).decode()}).encode()
    req = urllib.request.Request(f"https://{ip}:10443/data/LINKIE.json", body)
    if auth:
        req.add_header("Authorization", "Basic " + base64.b64encode(auth.encode()).decode())
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    ctx.set_ciphers("DEFAULT:@SECLEVEL=0")
    with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
        return json.loads(dec(base64.b64decode(r.read())))

if __name__ == "__main__":
    # KC_USER = Kasa email, KC_PASS = Kasa password; the camera expects basic auth with the MD5 hex of the password
    ip, mod, meth = sys.argv[1:4]
    h = hashlib.md5(os.environ["KC_PASS"].encode()).hexdigest()
    if os.environ.get("KC_UPPER"):
        h = h.upper()
    print(call(ip, mod, meth, json.loads(sys.argv[4]) if len(sys.argv) > 4 else None, os.environ["KC_USER"] + ":" + h))
