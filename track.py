#!/usr/bin/env python3
"""Usage: track.py set <id> <state> [note] | init. States: pending running done failed"""
import json, sys, time, pathlib
F = pathlib.Path(__file__).with_name("status.json")
TASKS = [("F1","Fix: validator","sonnet"),("F2","Fix: harness","sonnet"),("F3","Fix: packaging/CLI","sonnet"),("F4","Fix: ingest/manifest","sonnet"),("F5","Fix: template","sonnet")]
def load():
    return json.loads(F.read_text()) if F.exists() else {"tasks":[{"id":i,"title":t,"model":m,"state":"pending","note":"","start":None,"end":None} for i,t,m in TASKS],"log":[]}
d = load(); a = sys.argv[1:]
if a and a[0]=="set":
    for t in d["tasks"]:
        if t["id"]==a[1]:
            t["state"]=a[2]; t["note"]=" ".join(a[3:])
            if a[2]=="running": t["start"]=time.time()
            if a[2] in("done","failed"): t["end"]=time.time()
            d["log"].append([time.time(),a[1],a[2],t["note"]])
d["updated"]=time.time(); F.write_text(json.dumps(d))
