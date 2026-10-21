"""Dev Kit — token-saving code assets: project scaffolds (stacks) + a snippet
vault of reusable code patterns. Same idea as the design vault: pre-can what
Claude would otherwise regenerate from scratch, reference it by id/command.

    python ultra.py stacks list
    python ultra.py stacks new python-cli ./myapp
    python ultra.py snip [query]          # search code snippets
    python ultra.py snip show <id>        # print one, paste-ready

Curated content lives here as data and is written to disk + catalogued by
sync() (shared vault under C:\\Ultra-PC-Assets\\code). Stdlib-only.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from . import core, ui
from . import assets  # reuse the vault root + theming

CODE_DIR = assets.ASSETS_DIR / "code"
STACK_DIR = CODE_DIR / "stacks"
SNIP_DIR = CODE_DIR / "snippets"
CATALOG = CODE_DIR / "DEV-KIT.md"

# --------------------------------------------------------------------------- #
#  Stacks — project scaffolds. Each is a dict of {relative_path: file_text}.
#  Minimal-but-real boilerplate so a new project is copy + tweak, not generate.
# --------------------------------------------------------------------------- #

_GITIGNORE_PY = "__pycache__/\n*.pyc\n.venv/\nvenv/\n.env\ndist/\nbuild/\n*.egg-info/\n"
_GITIGNORE_NODE = "node_modules/\ndist/\n.env\n.env.local\n*.log\n.DS_Store\n"

STACKS: dict[str, dict] = {
    "python-cli": {
        "desc": "Python CLI with argparse, pyproject, and a tidy package layout.",
        "tags": ["python", "cli", "argparse"],
        "files": {
            "pyproject.toml": (
                "[project]\nname = \"myapp\"\nversion = \"0.1.0\"\n"
                "requires-python = \">=3.10\"\ndependencies = []\n\n"
                "[project.scripts]\nmyapp = \"myapp.cli:main\"\n\n"
                "[build-system]\nrequires = [\"setuptools\"]\n"
                "build-backend = \"setuptools.build_meta\"\n"),
            "myapp/__init__.py": "__version__ = \"0.1.0\"\n",
            "myapp/cli.py": (
                "import argparse\nimport sys\n\n\n"
                "def main(argv=None) -> int:\n"
                "    p = argparse.ArgumentParser(prog=\"myapp\", description=\"...\")\n"
                "    p.add_argument(\"name\", nargs=\"?\", default=\"world\")\n"
                "    p.add_argument(\"-v\", \"--verbose\", action=\"store_true\")\n"
                "    args = p.parse_args(argv)\n"
                "    print(f\"hello, {args.name}\")\n"
                "    return 0\n\n\n"
                "if __name__ == \"__main__\":\n"
                "    sys.exit(main())\n"),
            ".gitignore": _GITIGNORE_PY,
            "README.md": "# myapp\n\n```\npip install -e .\nmyapp --help\n```\n",
        }},
    "fastapi": {
        "desc": "FastAPI service with a health route, CORS, and a Dockerfile.",
        "tags": ["python", "api", "fastapi", "backend"],
        "files": {
            "requirements.txt": "fastapi\nuvicorn[standard]\npydantic\n",
            "app/main.py": (
                "from fastapi import FastAPI\n"
                "from fastapi.middleware.cors import CORSMiddleware\n"
                "from pydantic import BaseModel\n\n"
                "app = FastAPI(title=\"myapi\")\n"
                "app.add_middleware(CORSMiddleware, allow_origins=[\"*\"],\n"
                "                   allow_methods=[\"*\"], allow_headers=[\"*\"])\n\n\n"
                "class Item(BaseModel):\n    name: str\n    price: float\n\n\n"
                "@app.get(\"/health\")\ndef health():\n    return {\"ok\": True}\n\n\n"
                "@app.post(\"/items\")\ndef create(item: Item):\n    return item\n"),
            "Dockerfile": (
                "FROM python:3.12-slim\nWORKDIR /app\n"
                "COPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\n"
                "COPY . .\nCMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]\n"),
            ".gitignore": _GITIGNORE_PY,
            "README.md": "# myapi\n\n```\npip install -r requirements.txt\n"
                         "uvicorn app.main:app --reload\n```\n",
        }},
    "vite-react-ts": {
        "desc": "Vite + React + TypeScript SPA starter.",
        "tags": ["web", "react", "typescript", "vite", "frontend"],
        "files": {
            "package.json": json.dumps({
                "name": "myapp", "private": True, "version": "0.0.0", "type": "module",
                "scripts": {"dev": "vite", "build": "tsc && vite build", "preview": "vite preview"},
                "dependencies": {"react": "^18.3.0", "react-dom": "^18.3.0"},
                "devDependencies": {"@vitejs/plugin-react": "^4.3.0",
                                    "typescript": "^5.5.0", "vite": "^5.4.0",
                                    "@types/react": "^18.3.0", "@types/react-dom": "^18.3.0"},
            }, indent=2) + "\n",
            "index.html": (
                "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"UTF-8\">\n"
                "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
                "<title>myapp</title>\n</head>\n<body>\n<div id=\"root\"></div>\n"
                "<script type=\"module\" src=\"/src/main.tsx\"></script>\n</body>\n</html>\n"),
            "tsconfig.json": json.dumps({
                "compilerOptions": {"target": "ES2020", "useDefineForClassFields": True,
                    "lib": ["ES2020", "DOM", "DOM.Iterable"], "module": "ESNext",
                    "skipLibCheck": True, "moduleResolution": "bundler",
                    "jsx": "react-jsx", "strict": True, "noUnusedLocals": True},
                "include": ["src"]}, indent=2) + "\n",
            "vite.config.ts": (
                "import { defineConfig } from 'vite'\n"
                "import react from '@vitejs/plugin-react'\n\n"
                "export default defineConfig({ plugins: [react()] })\n"),
            "src/main.tsx": (
                "import React from 'react'\nimport ReactDOM from 'react-dom/client'\n"
                "import App from './App'\n\n"
                "ReactDOM.createRoot(document.getElementById('root')!).render(\n"
                "  <React.StrictMode><App /></React.StrictMode>,\n)\n"),
            "src/App.tsx": (
                "export default function App() {\n"
                "  return <main style={{ fontFamily: 'system-ui', padding: 32 }}>\n"
                "    <h1>myapp</h1>\n    <p>Edit src/App.tsx and save.</p>\n"
                "  </main>\n}\n"),
            ".gitignore": _GITIGNORE_NODE,
            "README.md": "# myapp\n\n```\nnpm install\nnpm run dev\n```\n",
        }},
    "static-site": {
        "desc": "Zero-build static site wired to the Ultra-PC design tokens.",
        "tags": ["web", "static", "html", "design-vault"],
        "files": {
            "index.html": (
                "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"UTF-8\">\n"
                "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
                "<title>my site</title>\n<link rel=\"stylesheet\" href=\"styles.css\">\n"
                "</head>\n<body>\n  <main class=\"wrap\">\n    <h1>Hello</h1>\n"
                "    <p>Swap the <code>:root</code> tokens for any Ultra-PC style — "
                "run <code>python ultra.py assets kit &lt;style&gt;</code>.</p>\n"
                "    <button class=\"btn\">Get started</button>\n  </main>\n"
                "<script src=\"script.js\"></script>\n</body>\n</html>\n"),
            "styles.css": (
                ":root{--bg:#ceecff;--surface:#fff;--accent:#2b8fd6;--accent2:#96cd6e;"
                "--text:#0b3c5d;--border:#9fd0f0;--radius:16px}\n"
                "*{box-sizing:border-box;margin:0}\n"
                "body{font-family:system-ui;color:var(--text);background:var(--bg);"
                "min-height:100vh;display:grid;place-items:center;padding:2rem}\n"
                ".wrap{max-width:640px;background:var(--surface);border:1px solid var(--border);"
                "border-radius:var(--radius);padding:2.4rem}\n"
                ".btn{margin-top:1.4rem;padding:.7rem 1.5rem;border:0;border-radius:999px;"
                "background:var(--accent);color:#fff;font-weight:600;cursor:pointer}\n"),
            "script.js": "console.log('ready')\n",
            ".gitignore": "",
        }},
    "node-express-ts": {
        "desc": "Node + Express + TypeScript API with health route and error mw.",
        "tags": ["node", "api", "express", "typescript", "backend"],
        "files": {
            "package.json": json.dumps({
                "name": "myapi", "version": "0.1.0", "type": "module",
                "scripts": {"dev": "tsx watch src/index.ts", "build": "tsc",
                            "start": "node dist/index.js"},
                "dependencies": {"express": "^4.19.0"},
                "devDependencies": {"typescript": "^5.5.0", "tsx": "^4.16.0",
                                    "@types/express": "^4.17.0", "@types/node": "^20.0.0"},
            }, indent=2) + "\n",
            "tsconfig.json": json.dumps({"compilerOptions": {
                "target": "ES2022", "module": "ESNext", "moduleResolution": "bundler",
                "outDir": "dist", "strict": True, "esModuleInterop": True,
                "skipLibCheck": True}, "include": ["src"]}, indent=2) + "\n",
            "src/index.ts": (
                "import express from 'express'\n\n"
                "const app = express()\napp.use(express.json())\n\n"
                "app.get('/health', (_req, res) => res.json({ ok: true }))\n\n"
                "app.use((err: any, _req: any, res: any, _next: any) => {\n"
                "  console.error(err)\n"
                "  res.status(err.status || 500).json({ error: err.message })\n})\n\n"
                "const port = process.env.PORT || 3000\n"
                "app.listen(port, () => console.log(`:${port}`))\n"),
            ".gitignore": _GITIGNORE_NODE,
            "README.md": "# myapi\n\n```\nnpm install\nnpm run dev\n```\n",
        }},
    "next-app": {
        "desc": "Next.js (App Router) + TypeScript starter.",
        "tags": ["web", "next", "react", "typescript", "ssr", "frontend"],
        "files": {
            "package.json": json.dumps({
                "name": "mynext", "version": "0.1.0", "private": True,
                "scripts": {"dev": "next dev", "build": "next build", "start": "next start"},
                "dependencies": {"next": "^14.2.0", "react": "^18.3.0", "react-dom": "^18.3.0"},
                "devDependencies": {"typescript": "^5.5.0", "@types/react": "^18.3.0",
                                    "@types/node": "^20.0.0"},
            }, indent=2) + "\n",
            "app/layout.tsx": (
                "export const metadata = { title: 'mynext' }\n\n"
                "export default function RootLayout({ children }: { children: React.ReactNode }) {\n"
                "  return <html lang=\"en\"><body>{children}</body></html>\n}\n"),
            "app/page.tsx": (
                "export default function Home() {\n"
                "  return <main style={{ padding: 32, fontFamily: 'system-ui' }}>\n"
                "    <h1>mynext</h1>\n  </main>\n}\n"),
            "next.config.mjs": "export default {}\n",
            ".gitignore": _GITIGNORE_NODE + ".next/\n",
            "README.md": "# mynext\n\n```\nnpm install\nnpm run dev\n```\n",
        }},
    "cloudflare-worker": {
        "desc": "Cloudflare Worker (TypeScript) with wrangler config.",
        "tags": ["cloudflare", "worker", "typescript", "edge", "serverless"],
        "files": {
            "wrangler.jsonc": json.dumps({
                "name": "myworker", "main": "src/index.ts",
                "compatibility_date": "2025-01-01"}, indent=2) + "\n",
            "src/index.ts": (
                "export default {\n"
                "  async fetch(request: Request): Promise<Response> {\n"
                "    const url = new URL(request.url)\n"
                "    if (url.pathname === '/health') return Response.json({ ok: true })\n"
                "    return new Response('hello from the edge')\n"
                "  },\n}\n"),
            "package.json": json.dumps({
                "name": "myworker", "version": "0.0.0",
                "scripts": {"dev": "wrangler dev", "deploy": "wrangler deploy"},
                "devDependencies": {"wrangler": "^3.60.0", "typescript": "^5.5.0"},
            }, indent=2) + "\n",
            ".gitignore": _GITIGNORE_NODE + ".wrangler/\n",
            "README.md": "# myworker\n\n```\nnpm install\nnpm run dev\n```\n",
        }},
    "python-package": {
        "desc": "Pip-installable Python library with src layout + pytest.",
        "tags": ["python", "library", "package", "pytest"],
        "files": {
            "pyproject.toml": (
                "[project]\nname = \"mypkg\"\nversion = \"0.1.0\"\n"
                "requires-python = \">=3.10\"\ndependencies = []\n\n"
                "[project.optional-dependencies]\ndev = [\"pytest\"]\n\n"
                "[build-system]\nrequires = [\"setuptools\"]\n"
                "build-backend = \"setuptools.build_meta\"\n\n"
                "[tool.setuptools.packages.find]\nwhere = [\"src\"]\n"),
            "src/mypkg/__init__.py": "from .core import add\n__all__ = [\"add\"]\n",
            "src/mypkg/core.py": "def add(a: int, b: int) -> int:\n    return a + b\n",
            "tests/test_core.py": "from mypkg import add\n\n\n"
                                  "def test_add():\n    assert add(2, 3) == 5\n",
            ".gitignore": _GITIGNORE_PY,
            "README.md": "# mypkg\n\n```\npip install -e .[dev]\npytest\n```\n",
        }},
    "flask": {
        "desc": "Minimal Flask web app with a template and JSON route.",
        "tags": ["python", "web", "flask", "backend"],
        "files": {
            "requirements.txt": "flask\n",
            "app.py": (
                "from flask import Flask, jsonify, render_template\n\n"
                "app = Flask(__name__)\n\n\n"
                "@app.get('/')\ndef home():\n    return render_template('index.html')\n\n\n"
                "@app.get('/api/health')\ndef health():\n    return jsonify(ok=True)\n\n\n"
                "if __name__ == '__main__':\n    app.run(debug=True)\n"),
            "templates/index.html": "<!doctype html>\n<h1>Flask is running</h1>\n",
            ".gitignore": _GITIGNORE_PY,
            "README.md": "# flask app\n\n```\npip install -r requirements.txt\n"
                         "python app.py\n```\n",
        }},
    "go-api": {
        "desc": "Go HTTP API using net/http (no deps).",
        "tags": ["go", "api", "backend", "http"],
        "files": {
            "go.mod": "module myapi\n\ngo 1.22\n",
            "main.go": (
                "package main\n\nimport (\n\t\"encoding/json\"\n\t\"log\"\n\t\"net/http\"\n)\n\n"
                "func main() {\n"
                "\thttp.HandleFunc(\"/health\", func(w http.ResponseWriter, r *http.Request) {\n"
                "\t\tjson.NewEncoder(w).Encode(map[string]bool{\"ok\": true})\n\t})\n"
                "\tlog.Println(\"listening on :8080\")\n"
                "\tlog.Fatal(http.ListenAndServe(\":8080\", nil))\n}\n"),
            ".gitignore": "bin/\n*.exe\n",
            "README.md": "# myapi (Go)\n\n```\ngo run .\n```\n",
        }},
    "bash-tool": {
        "desc": "Robust bash script (strict mode, args, usage) — thumbdrive-kit style.",
        "tags": ["bash", "shell", "cli", "script"],
        "files": {
            "tool.sh": (
                "#!/usr/bin/env bash\nset -euo pipefail\n\n"
                "usage() { echo \"usage: $0 [-v] <name>\"; exit 1; }\n\n"
                "verbose=0\nwhile getopts \":vh\" opt; do\n"
                "  case $opt in\n    v) verbose=1 ;;\n    h|*) usage ;;\n  esac\ndone\n"
                "shift $((OPTIND - 1))\n[ $# -ge 1 ] || usage\nname=\"$1\"\n\n"
                "[ \"$verbose\" = 1 ] && echo \"verbose on\"\n"
                "echo \"hello, $name\"\n"),
            "README.md": "# tool.sh\n\n```\nchmod +x tool.sh\n./tool.sh -v world\n```\n",
        }},
    "chrome-extension": {
        "desc": "Chrome/Edge extension (Manifest V3) with popup + background.",
        "tags": ["extension", "chrome", "manifest-v3", "browser"],
        "files": {
            "manifest.json": json.dumps({
                "manifest_version": 3, "name": "myext", "version": "0.1.0",
                "action": {"default_popup": "popup.html"},
                "background": {"service_worker": "background.js"},
                "permissions": ["storage", "activeTab"]}, indent=2) + "\n",
            "popup.html": ("<!doctype html>\n<body style=\"width:220px;font:14px system-ui;padding:12px\">\n"
                           "<h3>myext</h3><button id=\"go\">Run</button>\n"
                           "<script src=\"popup.js\"></script>\n</body>\n"),
            "popup.js": ("document.getElementById('go').onclick = () => {\n"
                         "  chrome.tabs.query({ active: true, currentWindow: true },\n"
                         "    ([tab]) => console.log('tab', tab?.url))\n}\n"),
            "background.js": "chrome.runtime.onInstalled.addListener(() => console.log('installed'))\n",
            "README.md": "# myext\n\nLoad unpacked at chrome://extensions (Developer mode).\n",
        }},
    "streamlit": {
        "desc": "Streamlit data app (charts + widgets) starter.",
        "tags": ["python", "data", "streamlit", "dashboard"],
        "files": {
            "requirements.txt": "streamlit\npandas\n",
            "app.py": (
                "import streamlit as st\nimport pandas as pd\n\n"
                "st.title('my data app')\n"
                "n = st.slider('rows', 5, 100, 20)\n"
                "df = pd.DataFrame({'x': range(n), 'y': [i * i for i in range(n)]})\n"
                "st.line_chart(df, x='x', y='y')\nst.dataframe(df)\n"),
            ".gitignore": _GITIGNORE_PY,
            "README.md": "# data app\n\n```\npip install -r requirements.txt\n"
                         "streamlit run app.py\n```\n",
        }},
}

# --------------------------------------------------------------------------- #
#  Snippets — reusable code patterns Claude would otherwise rewrite each time.
# --------------------------------------------------------------------------- #

SNIPPETS: dict[str, dict] = {
    "py-retry": {"lang": "python", "tags": ["retry", "backoff", "resilience"],
        "desc": "Retry a callable with exponential backoff + jitter.",
        "code": """import random, time

def retry(fn, tries=5, base=0.5, cap=10.0):
    for i in range(tries):
        try:
            return fn()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(min(cap, base * 2 ** i) + random.random() * 0.1)"""},
    "py-argparse": {"lang": "python", "tags": ["cli", "argparse"],
        "desc": "argparse subcommand skeleton.",
        "code": """import argparse

def main(argv=None):
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("greet"); g.add_argument("name")
    args = p.parse_args(argv)
    if args.cmd == "greet":
        print(f"hi {args.name}")"""},
    "py-env": {"lang": "python", "tags": ["config", "env", "settings"],
        "desc": "Typed settings from environment variables with defaults.",
        "code": """import os

class Settings:
    debug = os.getenv("DEBUG", "0") == "1"
    port = int(os.getenv("PORT", "8000"))
    db_url = os.getenv("DATABASE_URL", "sqlite:///app.db")

settings = Settings()"""},
    "py-fastapi-crud": {"lang": "python", "tags": ["fastapi", "crud", "api"],
        "desc": "In-memory CRUD routes for FastAPI.",
        "code": """from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
db: dict[int, dict] = {}

class Item(BaseModel):
    name: str

@app.post("/items")
def create(item: Item):
    i = len(db) + 1; db[i] = item.dict(); return {"id": i, **db[i]}

@app.get("/items/{i}")
def get(i: int):
    if i not in db: raise HTTPException(404)
    return {"id": i, **db[i]}"""},
    "js-debounce": {"lang": "javascript", "tags": ["debounce", "events", "perf"],
        "desc": "Debounce a function (trailing edge).",
        "code": """function debounce(fn, ms = 300) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}"""},
    "js-throttle": {"lang": "javascript", "tags": ["throttle", "events", "perf"],
        "desc": "Throttle a function to at most once per interval.",
        "code": """function throttle(fn, ms = 200) {
  let last = 0;
  return (...args) => {
    const now = Date.now();
    if (now - last >= ms) { last = now; fn(...args); }
  };
}"""},
    "js-fetch-timeout": {"lang": "javascript", "tags": ["fetch", "timeout", "abort"],
        "desc": "fetch() with a timeout via AbortController.",
        "code": """async function fetchTimeout(url, opts = {}, ms = 8000) {
  const c = new AbortController();
  const t = setTimeout(() => c.abort(), ms);
  try {
    return await fetch(url, { ...opts, signal: c.signal });
  } finally {
    clearTimeout(t);
  }
}"""},
    "js-jwt": {"lang": "javascript", "tags": ["auth", "jwt", "node"],
        "desc": "Sign + verify JWTs (jsonwebtoken).",
        "code": """import jwt from "jsonwebtoken";
const SECRET = process.env.JWT_SECRET;

export const sign = (payload) =>
  jwt.sign(payload, SECRET, { expiresIn: "7d" });

export const verify = (token) => {
  try { return jwt.verify(token, SECRET); }
  catch { return null; }
};"""},
    "js-express-error": {"lang": "javascript", "tags": ["express", "middleware", "errors"],
        "desc": "Express async wrapper + central error handler.",
        "code": """export const wrap = (fn) => (req, res, next) =>
  Promise.resolve(fn(req, res, next)).catch(next);

export function errorHandler(err, req, res, next) {
  console.error(err);
  res.status(err.status || 500).json({ error: err.message || "server error" });
}"""},
    "js-paginate": {"lang": "javascript", "tags": ["pagination", "api", "sql"],
        "desc": "Offset pagination helper (limit/offset + meta).",
        "code": """function paginate({ page = 1, size = 20 } = {}) {
  page = Math.max(1, +page); size = Math.min(100, Math.max(1, +size));
  return { limit: size, offset: (page - 1) * size, page, size };
}
// const { limit, offset } = paginate(req.query);"""},
    "zod-validate": {"lang": "typescript", "tags": ["validation", "zod", "schema"],
        "desc": "Zod schema + safe parse into a typed result.",
        "code": """import { z } from "zod";

const User = z.object({
  email: z.string().email(),
  age: z.number().int().min(0),
});
type User = z.infer<typeof User>;

const r = User.safeParse(input);
if (!r.success) return { error: r.error.flatten() };"""},
    "sql-crud": {"lang": "sql", "tags": ["sql", "crud", "schema"],
        "desc": "Table + the four CRUD statements.",
        "code": """CREATE TABLE items (
  id     INTEGER PRIMARY KEY,
  name   TEXT NOT NULL,
  price  REAL NOT NULL DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO items (name, price) VALUES (?, ?);
SELECT * FROM items WHERE id = ?;
UPDATE items SET name = ?, price = ? WHERE id = ?;
DELETE FROM items WHERE id = ?;"""},
    "regex-common": {"lang": "text", "tags": ["regex", "validation", "cheatsheet"],
        "desc": "Battle-tested common regexes (email, url, uuid, slug, ipv4).",
        "code": r"""email  ^[^@\s]+@[^@\s]+\.[^@\s]+$
url    ^https?://[^\s/$.?#].[^\s]*$
uuid   ^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$
slug   ^[a-z0-9]+(?:-[a-z0-9]+)*$
ipv4   ^(25[0-5]|2[0-4]\d|1?\d?\d)(\.(25[0-5]|2[0-4]\d|1?\d?\d)){3}$
hexcol ^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$"""},

    # ---- Python ---------------------------------------------------------- #
    "py-logging": {"lang": "python", "tags": ["logging", "setup", "observability"],
        "desc": "Sane logging config (level from env, clean format).",
        "code": """import logging, os

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)"""},
    "py-async-gather": {"lang": "python", "tags": ["asyncio", "concurrency", "await"],
        "desc": "Run coroutines concurrently with a semaphore cap.",
        "code": """import asyncio

async def run_all(coros, limit=10):
    sem = asyncio.Semaphore(limit)
    async def guarded(c):
        async with sem:
            return await c
    return await asyncio.gather(*(guarded(c) for c in coros))"""},
    "py-ttl-cache": {"lang": "python", "tags": ["cache", "ttl", "memoize"],
        "desc": "Tiny time-to-live cache decorator.",
        "code": """import time, functools

def ttl_cache(ttl=60):
    def deco(fn):
        store = {}
        @functools.wraps(fn)
        def wrap(*a):
            now = time.time()
            if a in store and now - store[a][1] < ttl:
                return store[a][0]
            v = fn(*a); store[a] = (v, now); return v
        return wrap
    return deco"""},
    "py-subprocess": {"lang": "python", "tags": ["subprocess", "shell", "run"],
        "desc": "Run a command safely, capture output, never raise.",
        "code": """import subprocess

def run(cmd, timeout=60):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except Exception as e:
        return 1, "", str(e)"""},
    "py-sqlite": {"lang": "python", "tags": ["sqlite", "db", "context"],
        "desc": "SQLite helper with row factory + context manager.",
        "code": """import sqlite3
from contextlib import contextmanager

@contextmanager
def db(path="app.db"):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    try:
        yield con; con.commit()
    finally:
        con.close()

# with db() as con: rows = con.execute("select * from t").fetchall()"""},
    "py-pytest": {"lang": "python", "tags": ["pytest", "testing", "fixture"],
        "desc": "pytest fixture + parametrize pattern.",
        "code": """import pytest

@pytest.fixture
def sample():
    return {"a": 1, "b": 2}

@pytest.mark.parametrize("x,expected", [(2, 4), (3, 9)])
def test_square(x, expected):
    assert x * x == expected"""},
    "py-timer": {"lang": "python", "tags": ["timing", "decorator", "profiling"],
        "desc": "Decorator that logs how long a function took.",
        "code": """import time, functools

def timed(fn):
    @functools.wraps(fn)
    def wrap(*a, **k):
        t = time.perf_counter()
        try: return fn(*a, **k)
        finally: print(f"{fn.__name__}: {time.perf_counter()-t:.3f}s")
    return wrap"""},
    "py-password-hash": {"lang": "python", "tags": ["auth", "password", "security", "hashlib"],
        "desc": "Salted PBKDF2 password hash + verify (stdlib only).",
        "code": """import hashlib, os, hmac

def hash_pw(pw: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 200_000)
    return salt.hex() + ":" + dk.hex()

def verify_pw(pw: str, stored: str) -> bool:
    salt_hex, dk_hex = stored.split(":")
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt_hex), 200_000)
    return hmac.compare_digest(dk.hex(), dk_hex)"""},
    "py-dataclass-json": {"lang": "python", "tags": ["dataclass", "json", "serialize"],
        "desc": "Dataclass <-> dict/JSON round-trip.",
        "code": """from dataclasses import dataclass, asdict
import json

@dataclass
class User:
    name: str
    age: int

u = User("ada", 36)
s = json.dumps(asdict(u))
back = User(**json.loads(s))"""},

    # ---- JavaScript / TypeScript ----------------------------------------- #
    "ts-result": {"lang": "typescript", "tags": ["result", "errors", "either"],
        "desc": "Result<T,E> type for error handling without exceptions.",
        "code": """type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

const Ok = <T>(value: T): Result<T> => ({ ok: true, value });
const Err = <E>(error: E): Result<never, E> => ({ ok: false, error });"""},
    "js-array-utils": {"lang": "javascript", "tags": ["array", "groupby", "chunk", "unique"],
        "desc": "groupBy, chunk, unique, and sum helpers.",
        "code": """const groupBy = (arr, key) =>
  arr.reduce((m, x) => ((m[x[key]] ??= []).push(x), m), {});
const chunk = (arr, n) =>
  Array.from({ length: Math.ceil(arr.length / n) }, (_, i) => arr.slice(i*n, i*n+n));
const unique = (arr) => [...new Set(arr)];
const sum = (arr) => arr.reduce((a, b) => a + b, 0);"""},
    "js-deep-merge": {"lang": "javascript", "tags": ["object", "merge", "clone"],
        "desc": "Recursive deep merge of plain objects.",
        "code": """function deepMerge(a, b) {
  const out = { ...a };
  for (const k of Object.keys(b)) {
    out[k] = (b[k] && typeof b[k] === "object" && !Array.isArray(b[k]))
      ? deepMerge(a[k] || {}, b[k]) : b[k];
  }
  return out;
}"""},
    "js-event-emitter": {"lang": "javascript", "tags": ["events", "pubsub", "emitter"],
        "desc": "Tiny pub/sub event emitter.",
        "code": """function emitter() {
  const map = new Map();
  return {
    on(e, fn) { (map.get(e) ?? map.set(e, []).get(e)).push(fn); },
    off(e, fn) { map.set(e, (map.get(e) || []).filter(f => f !== fn)); },
    emit(e, ...a) { (map.get(e) || []).forEach(f => f(...a)); },
  };
}"""},
    "react-usefetch": {"lang": "typescript", "tags": ["react", "hook", "fetch", "data"],
        "desc": "useFetch hook with loading/error/data state.",
        "code": """import { useEffect, useState } from "react";

export function useFetch<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let ok = true;
    fetch(url).then(r => r.json())
      .then(d => ok && setData(d))
      .catch(e => ok && setError(e))
      .finally(() => ok && setLoading(false));
    return () => { ok = false; };
  }, [url]);
  return { data, error, loading };
}"""},
    "react-uselocalstorage": {"lang": "typescript", "tags": ["react", "hook", "localstorage", "persist"],
        "desc": "useLocalStorage hook (persisted state).",
        "code": """import { useState } from "react";

export function useLocalStorage<T>(key: string, initial: T) {
  const [v, setV] = useState<T>(() => {
    try { return JSON.parse(localStorage.getItem(key) ?? "") ?? initial; }
    catch { return initial; }
  });
  const set = (val: T) => { setV(val); localStorage.setItem(key, JSON.stringify(val)); };
  return [v, set] as const;
}"""},
    "ts-api-client": {"lang": "typescript", "tags": ["fetch", "api", "client", "typed"],
        "desc": "Typed fetch wrapper that throws on non-2xx.",
        "code": """async function api<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...opts.headers },
    ...opts,
  });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json() as Promise<T>;
}"""},
    "js-intl-format": {"lang": "javascript", "tags": ["intl", "date", "currency", "format"],
        "desc": "Locale-aware date, currency, and relative-time formatting.",
        "code": """const money = (n, c = "USD") =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: c }).format(n);
const date = (d) =>
  new Intl.DateTimeFormat("en-US", { dateStyle: "medium" }).format(new Date(d));
const ago = (secs) =>
  new Intl.RelativeTimeFormat("en", { numeric: "auto" }).format(secs, "second");"""},
    "js-clipboard": {"lang": "javascript", "tags": ["clipboard", "copy", "browser"],
        "desc": "Copy text to clipboard with a fallback.",
        "code": """async function copy(text) {
  try { await navigator.clipboard.writeText(text); return true; }
  catch {
    const ta = document.createElement("textarea");
    ta.value = text; document.body.appendChild(ta); ta.select();
    document.execCommand("copy"); ta.remove(); return true;
  }
}"""},
    "js-download-blob": {"lang": "javascript", "tags": ["download", "blob", "file", "browser"],
        "desc": "Trigger a client-side file download from data.",
        "code": """function download(filename, text, type = "text/plain") {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = Object.assign(document.createElement("a"), { href: url, download: filename });
  a.click(); URL.revokeObjectURL(url);
}"""},
    "js-promise-utils": {"lang": "javascript", "tags": ["promise", "sleep", "timeout"],
        "desc": "sleep, withTimeout, and pLimit concurrency helpers.",
        "code": """const sleep = (ms) => new Promise(r => setTimeout(r, ms));

const withTimeout = (p, ms) =>
  Promise.race([p, new Promise((_, rej) => setTimeout(() => rej(new Error("timeout")), ms))]);"""},
    "node-bcrypt": {"lang": "javascript", "tags": ["auth", "bcrypt", "password", "node"],
        "desc": "Hash + compare passwords with bcrypt.",
        "code": """import bcrypt from "bcrypt";

export const hash = (pw) => bcrypt.hash(pw, 12);
export const check = (pw, digest) => bcrypt.compare(pw, digest);"""},
    "js-slugify": {"lang": "javascript", "tags": ["slug", "string", "url"],
        "desc": "Slugify a string (accents stripped, url-safe).",
        "code": """const slugify = (s) => s.toString().normalize("NFKD")
  .replace(/[\\u0300-\\u036f]/g, "")
  .toLowerCase().trim()
  .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");"""},

    # ---- DevOps / config ------------------------------------------------- #
    "dockerfile-node": {"lang": "dockerfile", "tags": ["docker", "node", "multistage"],
        "desc": "Multi-stage Node Dockerfile (small final image).",
        "code": """FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY package*.json ./
RUN npm ci --omit=dev
CMD ["node", "dist/index.js"]"""},
    "dockerfile-python": {"lang": "dockerfile", "tags": ["docker", "python", "slim"],
        "desc": "Slim Python Dockerfile.",
        "code": """FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]"""},
    "gha-ci": {"lang": "yaml", "tags": ["ci", "github-actions", "test"],
        "desc": "GitHub Actions: install + test on push (Node example).",
        "code": """name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: npm }
      - run: npm ci
      - run: npm test"""},
    "makefile": {"lang": "make", "tags": ["makefile", "tasks", "build"],
        "desc": "Common Makefile targets with .PHONY.",
        "code": """.PHONY: install dev test lint build clean
install: ; npm ci
dev:     ; npm run dev
test:    ; npm test
lint:    ; npm run lint
build:   ; npm run build
clean:   ; rm -rf dist node_modules"""},
    "bash-strict": {"lang": "bash", "tags": ["bash", "strict", "template"],
        "desc": "Bash strict-mode header + arg check.",
        "code": """#!/usr/bin/env bash
set -euo pipefail
IFS=$'\\n\\t'
[ $# -ge 1 ] || { echo "usage: $0 <arg>"; exit 1; }
main() { echo "arg: $1"; }
main "$@" """},

    # ---- SQL ------------------------------------------------------------- #
    "sql-upsert": {"lang": "sql", "tags": ["sql", "upsert", "conflict"],
        "desc": "Upsert (insert-or-update) for SQLite/Postgres.",
        "code": """INSERT INTO users (id, name, email)
VALUES (?, ?, ?)
ON CONFLICT (id) DO UPDATE
  SET name = excluded.name, email = excluded.email;"""},
    "sql-joins": {"lang": "sql", "tags": ["sql", "joins", "cheatsheet"],
        "desc": "The join types, at a glance.",
        "code": """-- rows in both:
SELECT * FROM a INNER JOIN b ON a.id = b.a_id;
-- all a, matched b (nulls if none):
SELECT * FROM a LEFT JOIN b ON a.id = b.a_id;
-- all b, matched a:
SELECT * FROM a RIGHT JOIN b ON a.id = b.a_id;
-- everything, matched where possible:
SELECT * FROM a FULL OUTER JOIN b ON a.id = b.a_id;"""},
}

# --------------------------------------------------------------------------- #
#  Sync + catalog
# --------------------------------------------------------------------------- #

def _ensure_dirs() -> None:
    for d in (CODE_DIR, STACK_DIR, SNIP_DIR):
        d.mkdir(parents=True, exist_ok=True)


_EXT = {"python": "py", "javascript": "js", "typescript": "ts", "sql": "sql",
        "text": "txt", "bash": "sh", "dockerfile": "dockerfile", "yaml": "yml",
        "make": "mk", "go": "go"}


_COMMENT = {"python": "#", "bash": "#", "yaml": "#", "make": "#",
            "dockerfile": "#", "sql": "--", "text": "#"}  # default "//"


def sync() -> dict:
    """Write snippets to disk + regenerate the DEV-KIT.md catalog."""
    _ensure_dirs()
    for sid, s in SNIPPETS.items():
        ext = _EXT.get(s["lang"], "txt")
        c = _COMMENT.get(s["lang"], "//")
        (SNIP_DIR / f"{sid}.{ext}").write_text(
            f"{c} {sid} — {s['desc']}\n" + s["code"] + "\n", encoding="utf-8")
    _write_catalog()
    core.log("devkit", f"synced {len(STACKS)} stacks, {len(SNIPPETS)} snippets",
             "SUCCESS")
    return {"stacks": len(STACKS), "snippets": len(SNIPPETS)}


def _write_catalog() -> None:
    L = ["# Ultra-PC Dev Kit — token-saving code assets\n",
         "> Project scaffolds + reusable code snippets. **Prefer these over "
         "generating boilerplate/patterns from scratch.** Query from "
         f"`{core.ROOT}`:\n",
         "```\npython ultra.py stacks list\n"
         "python ultra.py stacks new <id> <dir>\n"
         "python ultra.py snip [query]\n"
         "python ultra.py snip show <id>\n```\n",
         "## Stacks (project scaffolds)\n"]
    for sid, s in STACKS.items():
        L.append(f"- **{sid}** — {s['desc']}  ({len(s['files'])} files) · "
                 f"_{', '.join(s['tags'])}_")
    L.append("\n## Snippets (code patterns)\n")
    for sid, s in SNIPPETS.items():
        L.append(f"- **{sid}** [{s['lang']}] — {s['desc']}")
    CATALOG.write_text("\n".join(L) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
#  CLI
# --------------------------------------------------------------------------- #

def _match(q: str, *fields: str) -> bool:
    if not q:
        return True
    q = q.lower()
    return any(q in (f or "").lower() for f in fields)


def cmd_stacks_list(query: str = "") -> int:
    hits = [(k, v) for k, v in STACKS.items()
            if _match(query, k, v["desc"], " ".join(v["tags"]))]
    if not hits:
        print(f"No stacks match '{query}'."); return 1
    for k, v in hits:
        print(f"  {k:<16} {v['desc']}")
        print(f"  {'':<16} \x1b[2m{len(v['files'])} files · {', '.join(v['tags'])}\x1b[0m")
    print(f"\n  {len(hits)} stack(s). `stacks new <id> <dir>` to scaffold.")
    return 0


def cmd_stacks_new(stack_id: str, target: str) -> int:
    s = STACKS.get(stack_id)
    if not s:
        print(f"Unknown stack '{stack_id}'. Options: {', '.join(STACKS)}"); return 2
    out = Path(target).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    for rel, text in s["files"].items():
        fp = out / rel
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(text, encoding="utf-8")
    core.log("devkit", f"scaffold {stack_id} -> {out}", "SUCCESS")
    print(f"Scaffolded '{stack_id}' ({len(s['files'])} files) into {out}")
    for rel in s["files"]:
        print(f"  {rel}")
    return 0


def cmd_snip(query: str = "") -> int:
    hits = [(k, v) for k, v in SNIPPETS.items()
            if _match(query, k, v["lang"], v["desc"], " ".join(v["tags"]))]
    if not hits:
        print(f"No snippets match '{query}'."); return 1
    for k, v in hits:
        print(f"  {k:<18} [{v['lang']:<10}] {v['desc']}")
    print(f"\n  {len(hits)} snippet(s). `snip show {hits[0][0]}` to print one.")
    return 0


def cmd_snip_show(sid: str) -> int:
    s = SNIPPETS.get(sid)
    if not s:
        print(f"Unknown snippet '{sid}'. Try: snip <query>"); return 2
    print(f"// {sid} — {s['desc']}  [{s['lang']}]")
    print(s["code"])
    return 0


# --------------------------------------------------------------------------- #
#  Menu + dispatch
# --------------------------------------------------------------------------- #

def _tool_stacks(ctx=None) -> None:
    ui.title_bar("Dev Kit — Project stacks")
    q = ui.prompt("filter (blank = all)").strip()
    print()
    cmd_stacks_list(q)
    print()
    sid = ui.prompt("scaffold which id? (blank = skip)").strip()
    if sid and sid in STACKS:
        dest = ui.ask_directory("Choose where to create the project")
        if dest:
            name = ui.ask_string("Project folder name", initial=sid) or sid
            cmd_stacks_new(sid, str(Path(dest) / assets._slug(name)))
            if ui.ask_yesno("Open the folder?"):
                core.open_in_os(Path(dest) / assets._slug(name))
    ui.pause()


def _tool_snip(ctx=None) -> None:
    ui.title_bar("Dev Kit — Code snippets")
    q = ui.prompt("filter (blank = all)").strip()
    print()
    cmd_snip(q)
    print()
    sid = ui.prompt("show which id? (blank = skip)").strip()
    if sid:
        print()
        cmd_snip_show(sid)
    ui.pause()


def _tool_sync(ctx=None) -> None:
    ui.title_bar("Dev Kit — Sync")
    m = sync()
    ui.ok(f"Wrote {m} to {CODE_DIR}")
    if ui.ask_yesno("Open the dev-kit catalog?"):
        core.open_in_os(CATALOG)
    ui.pause()


def _tool_code_index(ctx=None) -> None:
    from . import coderag
    coderag._tool_index(ctx)


def _tool_code_search(ctx=None) -> None:
    from . import coderag
    coderag._tool_search(ctx)


def register() -> core.Category:
    cat = core.Category("devkit", "Dev Kit (scaffolds, snippets, code search)")
    cat.add("stacks", "Project scaffolds (new starter projects)", _tool_stacks)
    cat.add("snip", "Code snippet vault", _tool_snip)
    cat.add("code-search", "Search YOUR repos (semantic, offline)", _tool_code_search)
    cat.add("code-index", "Index a codebase for search", _tool_code_index)
    cat.add("sync", "Sync dev-kit to disk + rebuild catalog", _tool_sync)
    return cat


def handle(argv: list[str]) -> int | None:
    """Dispatch `stacks`/`snip` subcommands from ultra.py."""
    if not argv:
        return None
    cmd = argv[0].lower()
    rest = argv[1:]
    if cmd == "stacks":
        if rest and rest[0] == "new":
            if len(rest) < 3:
                print("usage: stacks new <id> <dir>"); return 2
            return cmd_stacks_new(rest[1], rest[2])
        if rest and rest[0] in ("list", "ls"):
            return cmd_stacks_list(" ".join(rest[1:]))
        return cmd_stacks_list(" ".join(rest))
    if cmd in ("snip", "snippet"):
        if rest and rest[0] == "show":
            if len(rest) < 2:
                print("usage: snip show <id>"); return 2
            return cmd_snip_show(rest[1])
        return cmd_snip(" ".join(rest))
    if cmd == "devkit-sync":
        m = sync(); print(f"Synced {m}"); return 0
    return None
