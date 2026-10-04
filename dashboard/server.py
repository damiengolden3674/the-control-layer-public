#!/usr/bin/env python3
import json,subprocess,time,urllib.request,threading
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
ROOT=Path(__file__).resolve().parent
CACHE={"pi":None,"pi_at":0,"ssh":None,"ssh_at":0,"gh":None,"gh_at":0}; LOCK=threading.Lock()
def fetch(url,timeout=3):
 r=urllib.request.Request(url,headers={"Accept":"application/vnd.github+json","User-Agent":"The-Control-Layer-Dashboard"})
 with urllib.request.urlopen(r,timeout=timeout) as x:return json.loads(x.read().decode())
def pi_health():
 try:return fetch("http://127.0.0.1:8879/health",2)
 except:return {"status":"HOLD","reason":"pi_health_unreachable"}
def ssh_metrics():
 cmd=r'''ssh -o BatchMode=yes -o ConnectTimeout=2 100.69.147.121 'python3 -c "import json,subprocess; m={}; 
x=subprocess.check_output(["free","-b"]).decode().splitlines(); a=x[1].split(); s=x[2].split(); m.update(memory_used=int(a[2]),memory_total=int(a[1]),memory_available=int(a[6]),swap_used=int(s[2]),swap_total=int(s[1])); 
u=open("/proc/loadavg").read().split(); m["load"]={"one":float(u[0]),"five":float(u[1]),"fifteen":float(u[2])}; 
d=subprocess.check_output(["df","-P","/","/mnt/storage"]).decode().splitlines(); r=d[1].split(); h=d[2].split(); m.update(root_used_percent=int(r[4][:-1]),hdd_used_percent=int(h[4][:-1]),hdd_free_gib=round(int(h[3])/1024/1024,1)); 
rows=subprocess.check_output(["docker","ps","--format","{{.Names}}|{{.Status}}"]).decode().splitlines(); m["containers"]= [{"name":q.split("|",1)[0],"status":q.split("|",1)[1],"memory":"—"} for q in rows]; print(json.dumps(m))"' '''
 try:return json.loads(subprocess.check_output(cmd,shell=True,stderr=subprocess.DEVNULL,timeout=5).decode())
 except:return {"error":"SSH metrics unavailable"}
def get_pi():
 with LOCK:
  if CACHE["pi"] is None or time.time()-CACHE["pi_at"]>2:CACHE["pi"],CACHE["pi_at"]=pi_health(),time.time()
  return CACHE["pi"]
def get_ssh():
 with LOCK:
  if CACHE["ssh"] is None or time.time()-CACHE["ssh_at"]>5:CACHE["ssh"],CACHE["ssh_at"]=ssh_metrics(),time.time()
  return CACHE["ssh"]
def get_gh():
 with LOCK:
  if CACHE["gh"] is None or time.time()-CACHE["gh_at"]>15:
   try:
    runs=fetch("https://api.github.com/repos/damiengolden3674/the-control-layer-public/actions/runs?per_page=8",3).get("workflow_runs",[])
    cs=fetch("https://api.github.com/repos/damiengolden3674/the-control-layer-public/commits?per_page=1",3)
    good=sum(1 for r in runs if r.get("conclusion")=="success")
    CACHE["gh"]={"default_branch":"main","latest_commit":cs[0]["sha"][:12] if cs else "—","ci_health":round(100*good/max(1,len(runs))),"runs":[{"name":r.get("name"),"status":r.get("status"),"conclusion":r.get("conclusion"),"html_url":r.get("html_url")} for r in runs]}
   except:CACHE["gh"]={"default_branch":"main","latest_commit":"—","ci_health":0,"runs":[]}
   CACHE["gh_at"]=time.time()
  return CACHE["gh"]
def snapshot():
 p=get_pi();s=get_ssh();return {"timestamp":time.time(),"pi":{"health":p,"memory":{"used_percent":100*s["memory_used"]/max(1,s["memory_total"]) if "memory_total" in s else None,"swap_used_percent":100*s["swap_used"]/max(1,s["swap_total"]) if "swap_total" in s else None},"storage":{"used_percent":s.get("hdd_used_percent"),"free_gib":s.get("hdd_free_gib")},"load":s.get("load",{}),"containers":s.get("containers",[])},"home":{"google_nest":"CONFIGURED • NEST SDM + GOOGLE SMART HOME","automations":[{"name":"Security ESCALATE Pipeline","trigger":"control_layer_escalate_request","action":"iPhone authentication → EXECUTE/HOLD","governance":"HUMAN-GATED"},{"name":"Sunset Living Room","trigger":"sunset + person.damien = home","action":"turn on living-room Hue lights","governance":"EXECUTE AFTER VALIDATION"},{"name":"Away Energy Reclaim","trigger":"person.damien = away for 10m","action":"turn off living-room Hue lights","governance":"EXECUTE AFTER VALIDATION"},{"name":"Google/Nest continuity","trigger":"HA startup / entity changes","action":"retain Nabu Casa synchronization path","governance":"NO CONFIG CHANGE"}]},"github":get_gh()}
def act(name):
 if name=="reconcile":cmd="sudo -n systemctl start control-layer-ecosystem-reconciler.service"
 elif name=="refresh-proof":cmd="sudo -n systemctl start control-layer-telemetry.service"
 else:return {"status":"ESCALATE","message":f"{name} is consequential and remains gated; no production mutation was performed."}
 try:subprocess.run(cmd,shell=True,timeout=5,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);return {"status":"EXECUTE","message":f"{name} executed within the dashboard authority ceiling."}
 except:return {"status":"HOLD","message":f"{name} could not be verified/executed; no bypass attempted."}
class H(BaseHTTPRequestHandler):
 def send(self,code,body,typ="application/json"):
  b=body if isinstance(body,bytes) else body.encode();self.send_response(code);self.send_header("Content-Type",typ);self.send_header("Cache-Control","no-store");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
 def do_GET(self):
  if self.path=="/api/snapshot":self.send(200,json.dumps(snapshot(),separators=(",",":")));return
  if self.path=="/api/health":self.send(200,json.dumps({"status":"NOMINAL","authority":"HUMAN_PRIMARY","aggregation":"MAC"}));return
  if self.path.startswith("/assets/") and (ROOT/self.path.lstrip("/")).is_file():self.send(200,(ROOT/self.path.lstrip("/")).read_bytes(),"image/png");return
  if self.path in ("/","/index.html"):self.send(200,(ROOT/"index.html").read_bytes(),"text/html; charset=utf-8");return
  self.send(404,json.dumps({"status":"HOLD","reason":"not_found"}))
 def do_POST(self):
  if self.path!="/api/action":self.send(404,json.dumps({"status":"HOLD"}));return
  try:n=int(self.headers.get("Content-Length","0"));self.send(200,json.dumps(act(json.loads(self.rfile.read(n) or b"{}").get("action"))))
  except:self.send(400,json.dumps({"status":"HOLD","message":"invalid request"}))
 def log_message(self,*a):pass
ThreadingHTTPServer(("127.0.0.1",8878),H).serve_forever()
