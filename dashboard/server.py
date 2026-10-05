#!/usr/bin/env python3
import json,subprocess,time,urllib.request,threading,os
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PI="100.69.147.121"
CACHE={}
LOCK=threading.Lock()

def fetch(url,timeout=3,headers=None):
    h={"Accept":"application/json","User-Agent":"The-Control-Layer-Private-Command-Bridge"}
    if headers:h.update(headers)
    r=urllib.request.Request(url,headers=h)
    with urllib.request.urlopen(r,timeout=timeout) as x:return json.loads(x.read().decode())

def ssh(cmd,timeout=5):
    return subprocess.check_output(["ssh","-o","BatchMode=yes","-o","ConnectTimeout=2",PI,cmd],stderr=subprocess.DEVNULL,timeout=timeout).decode()

def pi_health():
    try:return fetch("http://127.0.0.1:8879/health",2)
    except:return {"status":"HOLD","reason":"pi_health_unreachable"}

def metrics():
    try:
        raw=ssh("""python3 - <<'PY'
import json,subprocess
m={}
x=subprocess.check_output(["free","-b"]).decode().splitlines(); a=x[1].split(); s=x[2].split()
m["memory_used"]=int(a[2]);m["memory_total"]=int(a[1]);m["memory_available"]=int(a[6]);m["swap_used"]=int(s[2]);m["swap_total"]=int(s[1])
u=open("/proc/loadavg").read().split();m["load"]={"one":float(u[0]),"five":float(u[1]),"fifteen":float(u[2])}
d=subprocess.check_output(["df","-P","/","/mnt/storage"]).decode().splitlines();r=d[1].split();h=d[2].split()
m["root_used_percent"]=int(r[4][:-1]);m["hdd_used_percent"]=int(h[4][:-1]);m["hdd_free_gib"]=round(int(h[3])/1024/1024,1)
rows=subprocess.check_output(["docker","ps","--format","{{.Names}}|{{.Status}}"]).decode().splitlines()
m["containers"]=[{"name":q.split("|",1)[0],"status":q.split("|",1)[1]} for q in rows]
print(json.dumps(m))
PY""")
        return json.loads(raw)
    except:return {"error":"Pi metrics unavailable"}

def ha_inventory():
    try:
        raw=ssh("""python3 - <<'PY'
import json
base="/mnt/storage/services/homeassistant/config/.storage/"
er=json.load(open(base+"core.entity_registry"))
dr=json.load(open(base+"core.device_registry"))
ar={}
try: ar=json.load(open(base+"core.area_registry"))
except: pass
areas={x.get("id"):x.get("name") for x in ar.get("data",{}).get("areas",[])}
devices={x.get("id"):x for x in dr.get("data",{}).get("devices",[])}
out=[]
for e in er.get("data",{}).get("entities",[]):
    did=e.get("device_id"); dev=devices.get(did,{})
    dom=(e.get("entity_id") or ".").split(".",1)[0]
    if dom not in {"light","switch","scene","script","climate","lock","camera","media_player","cover","fan","sensor","binary_sensor","automation","person","alarm_control_panel","button"}: continue
    out.append({"entity_id":e.get("entity_id"),"domain":dom,"name":e.get("name") or e.get("original_name") or e.get("entity_id"),"area":areas.get(e.get("area_id")) or areas.get(dev.get("area_id")) or "Unassigned","device":dev.get("name") or "—","disabled":e.get("disabled_by") is not None})
print(json.dumps({"entities":out,"areas":sorted(set(x["area"] for x in out))}))
PY""")
        return json.loads(raw)
    except:return {"entities":[],"areas":[]}

def github():
    try:
        runs=fetch("https://api.github.com/repos/damiengolden3674/the-control-layer-public/actions/runs?per_page=8",3).get("workflow_runs",[])
        cs=fetch("https://api.github.com/repos/damiengolden3674/the-control-layer-public/commits?per_page=1",3)
        good=sum(r.get("conclusion")=="success" for r in runs)
        return {"default_branch":"main","latest_commit":cs[0]["sha"][:12] if cs else "—","ci_health":round(100*good/max(1,len(runs))),"runs":[{"name":r.get("name"),"status":r.get("status"),"conclusion":r.get("conclusion"),"html_url":r.get("html_url")} for r in runs]}
    except:return {"default_branch":"main","latest_commit":"—","ci_health":0,"runs":[]}

def snapshot():
    p=pi_health();m=metrics(); inv=ha_inventory()
    checks=(p.get("live_ecosystem") or {}).get("checks") or {}
    rt=p.get("runtime_checks") or {}
    return {
      "timestamp":time.time(),
      "governance":{"authority":"HUMAN PRIMARY","hierarchy":"HUMAN → FRONTIER AI → CONTROL LAYER → CAPABILITY FABRIC → GOVERNED EXECUTOR → ECOSYSTEM → PROOF","decision":"EXECUTE" if p.get("status")=="NOMINAL" else "HOLD","principle":"INTELLIGENCE ≠ AUTHORITY"},
      "pi":{"health":p,"memory":{"used_percent":100*m.get("memory_used",0)/max(1,m.get("memory_total",1)),"swap_used_percent":100*m.get("swap_used",0)/max(1,m.get("swap_total",1))},"storage":{"used_percent":m.get("hdd_used_percent"),"free_gib":m.get("hdd_free_gib")},"root_used_percent":m.get("root_used_percent"),"load":m.get("load",{}),"containers":m.get("containers",[])},
      "home":{"runtime":rt,"inventory":inv,"google_nest":"CONFIGURED • NEST SDM + GOOGLE SMART HOME","automations":[{"name":"Security ESCALATE Pipeline","trigger":"security / consequential action","action":"iPhone approval → EXECUTE / HOLD","governance":"HUMAN-GATED"},{"name":"Sunset Living Room","trigger":"sunset + home","action":"Hue living-room scene/lights","governance":"VALIDATED"},{"name":"Away Energy Reclaim","trigger":"away ≥10m","action":"energy reclaim","governance":"VALIDATED"},{"name":"Google/Nest continuity","trigger":"HA / SDM lifecycle","action":"preserve synchronization","governance":"NO CONFIG CHANGE"}]},
      "ai":{"openai":p.get("providers",{}).get("OPENAI",{}),"anthropic":p.get("providers",{}).get("ANTHROPIC",{}),"google":"REMOVED"},
      "github":github(),
      "proof":{"transport":(p.get("transport_proof") or {}).get("authorized_transport_verified",False),"verified_at":(p.get("transport_proof") or {}).get("verified_at"),"sanitized":True}
    }

def action(payload):
    a=payload.get("action","")
    if a in {"light_on","light_off","scene_activate","media_play","media_pause","climate_set","fan_on","fan_off"}:
        return {"status":"HOLD","message":"Control intent created but not executed: HA command credential is not exposed to the dashboard. Intelligence ≠ Authority.","requires":"AUTHORIZED_HA_CONTROL_CHANNEL"}
    if a in {"lock","unlock","camera_privacy","security_disarm"}:
        return {"status":"ESCALATE","message":"Sensitive action requires Human Primary / iPhone approval. No mutation performed.","requires":"IPHONE_APPROVAL"}
    if a=="reconcile":
        try:
            subprocess.run("ssh -o BatchMode=yes -o ConnectTimeout=2 "+PI+" 'sudo -n systemctl start control-layer-ecosystem-reconciler.service'",shell=True,timeout=5,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            return {"status":"EXECUTE","message":"Ecosystem reconciliation started; verification follows."}
        except:return {"status":"HOLD","message":"Reconciliation could not be verified."}
    return {"status":"HOLD","message":"Unknown or unapproved command."}

class H(BaseHTTPRequestHandler):
    def send(self,code,body,typ="application/json"):
        b=body if isinstance(body,bytes) else body.encode();self.send_response(code);self.send_header("Content-Type",typ);self.send_header("Cache-Control","no-store");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
    def do_GET(self):
        if self.path in ("/api/dashboard/snapshot","/api/snapshot"): self.send(200,json.dumps(snapshot(),separators=(",",":")));return
        if self.path=="/api/health": self.send(200,json.dumps({"status":"NOMINAL","authority":"HUMAN_PRIMARY","surface":"PRIVATE_COMMAND_BRIDGE"}));return
        if self.path.startswith("/assets/"):
            f=ROOT/self.path.lstrip("/")
            if f.is_file():self.send(200,f.read_bytes(),"image/png");return
        if self.path in ("/","/index.html","/dashboard","/dashboard/"):self.send(200,(ROOT/"index.html").read_bytes(),"text/html; charset=utf-8");return
        self.send(404,json.dumps({"status":"HOLD"}))
    def do_POST(self):
        if self.path not in ("/api/dashboard/action","/api/action"):self.send(404,json.dumps({"status":"HOLD"}));return
        try:
            n=int(self.headers.get("Content-Length","0")); self.send(200,json.dumps(action(json.loads(self.rfile.read(n) or b"{}"))))
        except Exception as e:self.send(400,json.dumps({"status":"HOLD","message":"invalid request"}))
    def log_message(self,*a):pass
ThreadingHTTPServer(("127.0.0.1",8878),H).serve_forever()
