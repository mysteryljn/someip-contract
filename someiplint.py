#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
def lint(spec):
    errors=[]; ids={}
    def add(kind,ident,where):
        key=(kind,ident)
        if key in ids: errors.append("%s: duplicate %s id %s (also %s)"%(where,kind,ident,ids[key]))
        else: ids[key]=where
    if not isinstance(spec.get("service_id"),int) or not 0<=spec["service_id"]<=0xffff: errors.append("service_id must be uint16")
    version=spec.get("version",{})
    if not isinstance(version.get("major"),int) or version.get("major",0)<0 or not isinstance(version.get("minor"),int) or version.get("minor",0)<0: errors.append("version must contain non-negative major/minor")
    for i,m in enumerate(spec.get("methods",[])):
        where="methods[%d]"%i; add("method",m.get("id"),where)
        if not isinstance(m.get("id"),int) or not 0<=m["id"]<=0xffff: errors.append(where+": method id must be uint16")
        if m.get("reliability") not in ("reliable","unreliable"): errors.append(where+": reliability is required")
        if not isinstance(m.get("name"),str) or not m["name"]: errors.append(where+": name is required")
    for i,e in enumerate(spec.get("events",[])):
        where="events[%d]"%i; add("event",e.get("id"),where)
        if not isinstance(e.get("id"),int) or not 0<=e["id"]<=0xffff: errors.append(where+": event id must be uint16")
        if e.get("reliability") not in ("reliable","unreliable"): errors.append(where+": reliability is required")
    method_ids={m.get("id") for m in spec.get("methods",[])}; event_ids={e.get("id") for e in spec.get("events",[])}
    for ident in sorted(method_ids & event_ids): errors.append("method/event id collision %s"%ident)
    return errors
def main(argv=None):
    p=argparse.ArgumentParser(description="Validate a SOME/IP service contract"); p.add_argument("spec",type=Path); a=p.parse_args(argv)
    try: errors=lint(json.loads(a.spec.read_text(encoding="utf-8")))
    except (OSError,json.JSONDecodeError) as e: print("error: "+str(e)); return 2
    if errors: print("\n".join("ERROR "+e for e in errors)); return 1
    print("OK: SOME/IP contract passed"); return 0
if __name__=="__main__": raise SystemExit(main())
