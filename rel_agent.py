import json, base64, time, subprocess, hashlib, urllib.request, urllib.error
def lg(m):
    open("/tmp/rel.log", "a").write(time.strftime("[%H:%M:%S]") + m + "\n")

REPO = "Setyoanugrah/molab-state"
G, O = "relay/cmd", "relay/out"
TK = open("/tmp/gh.tk").read().strip()
H = {"Authorization": "token " + TK, "Accept": "application/vnd.github+json",
     "User-Agent": "relay"}

def api(path, method="GET", body=None, etag=None):
    hd = dict(H)
    if etag:
        hd["If-None-Match"] = etag
    req = urllib.request.Request("https://api.github.com/" + path,
        headers=hd, data=json.dumps(body).encode() if body else None,
        method=method)
    try:
        r = urllib.request.urlopen(req)
        bt = r.read()
        return r.status, bt, r.headers.get("ETag")
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers.get("ETag") if e.headers else None

def put(path, content, msg="relay"):
    st, b, _ = api("repos/%s/contents/%s?ref=main" % (REPO, path))
    sha = json.loads(b)["sha"] if st == 200 else None
    body = {"message": msg, "content": base64.b64encode(content.encode()).decode()}
    if sha:
        body["sha"] = sha
    st, b, _ = api("repos/%s/contents/%s" % (REPO, path), "PUT", body)
    return st

seen = ""
etag = None
while True:
    st, b, e2 = api("repos/%s/contents/%s?ref=main" % (REPO, G), etag=etag)
    if st == 200:
        etag = e2
        content_b64 = json.loads(b).get("content", "").replace("\n", "")
        content = base64.b64decode(content_b64).decode("utf-8", "replace")
        h = hashlib.sha256(content.encode()).hexdigest()[:16]
        if h != seen:
            lg("cmd sha %s" % h)
            seen = h
            content = content.rstrip("\n")
            lines = content.rsplit("\n", 1)
            callid = "0"
            if len(lines) == 2 and lines[1].startswith("#CALL:"):
                content, callid = lines[0], lines[1][6:]
            lg("callid " + callid)
            open("/tmp/cmd.sh", "w").write(content)
            try:
                p = subprocess.run(["bash", "/tmp/cmd.sh"], capture_output=True, timeout=110)
                out = p.stdout + (b"\n==STDERR==\n" + p.stderr if p.stderr else b"")
            except subprocess.TimeoutExpired as t:
                out = (t.stdout or b"") + b"\n==TIMEOUT 110s=="
            lg("exec done output %dB" % len(out))
            r2 = put(O, "RESULT:%s|%s" % (callid, base64.b64encode(out[:700000]).decode()))
            lg("put rc %s" % r2)
    time.sleep(3)

lg('agent-start')
