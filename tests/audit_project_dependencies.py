# Audit project dependencies and repository artifacts without modifying the project.
from __future__ import annotations
import ast,json,re
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BACKEND=ROOT/"backend"; FRONTEND=ROOT/"frontend"
IGNORE={".git",".venv","node_modules",".next",".vercel","__pycache__","dist","build"}
MAP={"google-genai":{"google"},"pillow":{"PIL"},"python-dotenv":{"dotenv"},"typing-extensions":{"typing_extensions"},"fonttools":{"fontTools"},"pyasn1-modules":{"pyasn1_modules"}}
INDIRECT={"uvicorn","starlette","pydantic-core","typing-inspection","annotated-doc","annotated-types","anyio","certifi","cffi","charset-normalizer","click","cryptography","distro","h11","httpcore","idna","pyasn1","pyasn1-modules","pycparser","pydyf","pyee","pyphen","sniffio","tenacity","tinycss2","tinyhtml5","typing-extensions","urllib3","webencodings","websockets","zopfli","brotli","greenlet"}
HEAVY={"playwright","weasyprint","pillow","fonttools","cryptography","google-genai"}

def files(base,suffixes=None):
    if not base.exists(): return []
    return [p for p in base.rglob("*") if p.is_file() and not any(x in IGNORE for x in p.parts) and (not suffixes or p.suffix.lower() in suffixes)]
def rel(p): return str(p.relative_to(ROOT))
def norm(s): return re.sub(r"[-_.]+","-",s).lower()
def reqname(line):
    line=line.strip()
    if not line or line.startswith(("#","-")): return None
    m=re.match(r"([A-Za-z0-9_.-]+)",line); return norm(m.group(1)) if m else None
def imports(p):
    try: tree=ast.parse(p.read_text(encoding="utf-8"))
    except Exception: return set()
    out=set()
    for n in ast.walk(tree):
        if isinstance(n,ast.Import): out|={a.name.split(".")[0] for a in n.names}
        elif isinstance(n,ast.ImportFrom) and n.module: out.add(n.module.split(".")[0])
    return out
def refs(needle, pool):
    out=[]
    for p in pool:
        try: text=p.read_text(encoding="utf-8").lower()
        except Exception: continue
        if needle.lower() in text: out.append(rel(p))
    return out
def subprocess_modules(p):
    """Find literal `-m backend...` module invocations in subprocess command lists."""
    try:
        tree = ast.parse(p.read_text(encoding="utf-8"))
    except Exception:
        return set()
    out = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.List, ast.Tuple)):
            continue
        values = []
        for elt in node.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                values.append(elt.value)
            else:
                values.append(None)
        for i, value in enumerate(values[:-1]):
            if value == "-m":
                target = values[i + 1]
                if isinstance(target, str) and target.startswith("backend."):
                    out.add(target)
    return out

def runtime_entry_modules():
    """Resolve imports plus Python subprocess module entry points used by the pipeline."""
    py = files(BACKEND, {".py"})
    mods = {".".join(p.relative_to(ROOT).with_suffix("").parts): p for p in py}
    edges = defaultdict(set)

    for mod, p in mods.items():
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for n in ast.walk(tree):
            names = []
            if isinstance(n, ast.Import):
                names = [a.name for a in n.names]
            elif isinstance(n, ast.ImportFrom) and n.module:
                names = [n.module]
            for imp in names:
                for target in mods:
                    if imp == target or imp.startswith(target + ".") or target.startswith(imp + "."):
                        edges[mod].add(target)

        for target in subprocess_modules(p):
            if target in mods:
                edges[mod].add(target)

    seen = set()
    stack = [x for x in ("backend.main", "backend.pipelines.run_cv_job") if x in mods]
    while stack:
        mod = stack.pop()
        if mod in seen:
            continue
        seen.add(mod)
        stack.extend(edges[mod] - seen)
    return sorted(seen), mods

def runtime_external_imports():
    """Collect external top-level imports from all statically resolved runtime modules."""
    runtime_mods, mods = runtime_entry_modules()
    local_roots = {"backend"}
    standard = set(getattr(__import__("sys"), "stdlib_module_names", set()))
    external = set()
    by_module = {}
    for mod in runtime_mods:
        found = imports(mods[mod])
        ext = {name for name in found if name not in local_roots and name not in standard}
        by_module[mod] = ext
        external |= ext
    return runtime_mods, external, by_module

def runtime():
    py=files(BACKEND,{".py"}); mods={".".join(p.relative_to(ROOT).with_suffix("").parts):p for p in py}; edges=defaultdict(set)
    for mod,p in mods.items():
        try: tree=ast.parse(p.read_text(encoding="utf-8"))
        except Exception: continue
        for n in ast.walk(tree):
            names=[]
            if isinstance(n,ast.Import): names=[a.name for a in n.names]
            elif isinstance(n,ast.ImportFrom) and n.module: names=[n.module]
            for imp in names:
                for target in mods:
                    if imp==target or imp.startswith(target+".") or target.startswith(imp+"."): edges[mod].add(target)
    seen=set(); stack=[x for x in ("backend.main","backend.pipelines.run_cv_job") if x in mods]
    while stack:
        m=stack.pop()
        if m in seen: continue
        seen.add(m); stack.extend(edges[m]-seen)
    return sorted(seen)
def frontend_imports():
    pat=re.compile(r"""(?:from\s+|import\s*\(\s*|require\s*\(\s*)["']([^"']+)["']"""); out=set()
    for base in (FRONTEND/"app",FRONTEND/"components",FRONTEND/"lib"):
        for p in files(base,{".ts",".tsx",".js",".jsx"}):
            try: out|=set(pat.findall(p.read_text(encoding="utf-8")))
            except Exception: pass
    def pkg(s):
        if s.startswith((".","/","@/")): return None
        return "/".join(s.split("/")[:2]) if s.startswith("@") else s.split("/")[0]
    return {x for s in out if (x:=pkg(s))}
def main():
    pyfiles=files(BACKEND,{".py"}); allimp=set().union(*(imports(p) for p in pyfiles)) if pyfiles else set()
    reqs=[x for line in (BACKEND/"requirements.txt").read_text().splitlines() if (x:=reqname(line))]
    pool=files(BACKEND,{".py",".html",".css",".json"})
    rows=[]
    print(f"Repository: {ROOT}\n\n=== PYTHON DEPENDENCIES ===")
    for d in reqs:
        imps=MAP.get(d,{d.replace("-","_")}); direct=bool(imps&allimp); textual=bool(refs(d,pool))
        status="USED" if direct or textual else ("UNCERTAIN" if d in INDIRECT else "PROBABLY_UNUSED")
        rows.append((d,status,direct,textual)); print(f"{status:16} {d}")
    print("\nSpecial package evidence:")
    for d in ("playwright","weasyprint","pillow","PIL","markdown","requests","google-genai","fastapi","uvicorn","python-dotenv"):
        h=refs(d,pool); print(f"- {d}: {', '.join(h[:8]) if h else 'no textual reference found'}")
    print("\n=== RUNTIME MODULES ===")
    runtime_mods, runtime_ext, runtime_by_module = runtime_external_imports()
    for m in runtime_mods:
        ext = ", ".join(sorted(runtime_by_module[m])) or "(stdlib/local only)"
        print(f"{m} -> {ext}")
    print("\nDirect external imports across resolved runtime:")
    print(", ".join(sorted(runtime_ext)) if runtime_ext else "None resolved.")
    print("\n=== FRONTEND DEPENDENCIES ===")
    pkg=FRONTEND/"package.json"
    if pkg.exists():
        data=json.loads(pkg.read_text()); used=frontend_imports()
        for sec in ("dependencies","devDependencies"):
            for d in sorted(data.get(sec,{})):
                st="USED" if d in used else ("UNCERTAIN" if sec=="devDependencies" else "PROBABLY_UNUSED")
                print(f"{st:16} {d} ({sec})")
    print("\n=== ASSETS ===")
    src=files(ROOT,{".py",".ts",".tsx",".js",".jsx",".html",".css",".json",".md",".mjs",".cjs"}); assets=[]
    for base in (BACKEND/"assets",FRONTEND/"public"):
        for a in files(base):
            h=[x for x in refs(a.name,src) if x!=rel(a)]; assets.append((a,h))
            print(f"{'REFERENCED' if h else 'POSSIBLY_UNUSED':16} {rel(a)} ({a.stat().st_size:,} bytes)"+(f" -> {', '.join(h[:4])}" if h else ""))
    print("\n=== GENERATED / TEST ARTIFACTS ===")
    found=False
    for x in ROOT.rglob("*"):
        if ".git" in x.parts or ".venv" in x.parts or "node_modules" in x.parts: continue
        kind=None
        if x.is_dir() and x.name=="__pycache__": kind="CACHE_DIR"
        elif x.is_file() and x.suffix==".pyc": kind="PYC"
        elif x.is_file() and x.name==".DS_Store": kind="DS_STORE"
        elif x.is_file() and x.stat().st_size==0: kind="EMPTY_FILE"
        if kind: found=True; print(f"{kind:16} {rel(x)}")
    for x in files(ROOT/"workbench"):
        if x.resolve()!=Path(__file__).resolve(): found=True; print(f"{'WORKBENCH':16} {rel(x)}")
    if not found: print("None detected.")
    print("\n=== DIRECT RUNTIME REQUIREMENT EVIDENCE ===")
    for d in reqs:
        import_names = MAP.get(d, {d.replace("-", "_")})
        matched = sorted(import_names & runtime_ext)
        if matched:
            print(f"RUNTIME_DIRECT   {d} <- {', '.join(matched)}")
    print("NOTE: Framework servers, CLI tools, dynamic imports, and subprocess-only packages may still be required.")

    print("\n=== HIGH-IMPACT CLEANUP CANDIDATES ===")
    cand=[f"{d}: {s}" for d,s,_,_ in rows if d in HEAVY and s!="USED"]
    cand += [f"{rel(a)}: POSSIBLY_UNUSED ({a.stat().st_size:,} bytes)" for a,h in assets if not h and a.stat().st_size>=1_000_000]
    print("\n".join(cand) if cand else "No high-confidence high-impact candidate found statically.")
    print("\nNOTE: PROBABLY_UNUSED means review, not delete. Dynamic imports, CLI use, plugins, and transitive dependencies can be invisible.")
if __name__=="__main__": main()
