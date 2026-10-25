#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
def lint(spec):
    errors=[]; ids={}
    # A syntactically valid JSON document is not necessarily a contract.  Keep
    # malformed shapes in the linting API instead of raising AttributeError
    # while trying to access ``dict`` methods below.
    if not isinstance(spec, dict):
        return ["contract must be a JSON object"]

    # ``bool`` is a subclass of ``int`` in Python, but JSON booleans are not
    # valid SOME/IP numeric identifiers or version components.
    def is_int(value):
        return type(value) is int

    def is_hashable(value):
        # JSON arrays and objects can appear where an ID is expected.  They
        # are invalid IDs, but must still produce validation errors instead of
        # crashing the linter while constructing duplicate-ID sets.
        try:
            hash(value)
        except TypeError:
            return False
        return True

    def add(kind,ident,where):
        if not is_hashable(ident):
            return
        key=(kind,ident)
        if key in ids: errors.append("%s: duplicate %s id %s (also %s)"%(where,kind,ident,ids[key]))
        else: ids[key]=where
    service_id = spec.get("service_id")
    if not is_int(service_id) or not 0<=service_id<=0xffff:
        errors.append("service_id must be uint16")
    elif service_id == 0xffff:
        # 0xFFFF is assigned to SOME/IP Service Discovery.  Treating it as
        # an application service would make its message IDs collide with SD
        # traffic on every ECU using this contract.
        errors.append("service_id 0xffff is reserved for SOME/IP Service Discovery")
    version=spec.get("version",{})
    if not isinstance(version,dict):
        errors.append("version must be an object")
        version={}
    if not is_int(version.get("major")) or version.get("major",0)<0 or not is_int(version.get("minor")) or version.get("minor",0)<0: errors.append("version must contain non-negative major/minor")
    methods=spec.get("methods",[])
    if not isinstance(methods,list):
        errors.append("methods must be an array")
        methods=[]
    for i,m in enumerate(methods):
        where="methods[%d]"%i
        if not isinstance(m,dict):
            errors.append(where+": method must be an object")
            continue
        add("method",m.get("id"),where)
        if not is_int(m.get("id")) or not 0<=m["id"]<=0xffff: errors.append(where+": method id must be uint16")
        if m.get("reliability") not in ("reliable","unreliable"): errors.append(where+": reliability is required")
        if not isinstance(m.get("name"),str) or not m["name"]: errors.append(where+": name is required")
    events=spec.get("events",[])
    if not isinstance(events,list):
        errors.append("events must be an array")
        events=[]
    for i,e in enumerate(events):
        where="events[%d]"%i
        if not isinstance(e,dict):
            errors.append(where+": event must be an object")
            continue
        add("event",e.get("id"),where)
        if not is_int(e.get("id")) or not 0<=e["id"]<=0xffff: errors.append(where+": event id must be uint16")
        if e.get("reliability") not in ("reliable","unreliable"): errors.append(where+": reliability is required")
    method_ids={m.get("id") for m in methods if isinstance(m,dict) and is_hashable(m.get("id"))}; event_ids={e.get("id") for e in events if isinstance(e,dict) and is_hashable(e.get("id"))}
    # Use a representation-based key because malformed but hashable IDs can
    # have incomparable Python types (for example, an int and a string).
    for ident in sorted(method_ids & event_ids, key=repr): errors.append("method/event id collision %s"%ident)
    return errors
def main(argv=None):
    p=argparse.ArgumentParser(description="Validate a SOME/IP service contract"); p.add_argument("spec",type=Path); a=p.parse_args(argv)
    try: errors=lint(json.loads(a.spec.read_text(encoding="utf-8")))
    except (OSError,json.JSONDecodeError) as e: print("error: "+str(e)); return 2
    if errors: print("\n".join("ERROR "+e for e in errors)); return 1
    print("OK: SOME/IP contract passed"); return 0
if __name__=="__main__": raise SystemExit(main())
