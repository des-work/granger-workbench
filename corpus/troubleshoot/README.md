# Fix-It curated corpus (version-controlled master)

The hand-authored troubleshooting docs for `python ultra.py fix` — decision-tree
runbooks and platform quick-references (Linux / Cisco IOS / Windows). This repo
copy is the **backup/master**; the *live* corpus that Fix-It indexes lives at:

```
C:\Ultra-PC-Knowledge\troubleshoot\
```

The live dir also holds the re-downloadable parts that are NOT tracked here:
19 core RFCs (`rfc/`), 6,859 tldr pages (`tldr/pages/`), and the embedding
index (`_fix-index.json`).

## Restore / deploy to a fresh machine

```powershell
# 1. copy the curated docs into place
Copy-Item -Recurse corpus\troubleshoot\* C:\Ultra-PC-Knowledge\troubleshoot\

# 2. refetch the re-downloadable parts (RFCs + tldr) — see fixit.py docstring,
#    or skip: Fix-It works with the curated docs alone.

# 3. build the embedding index (needs Ollama + nomic-embed-text)
python ultra.py fix index
```

## Editing workflow

Edit the copy in `C:\Ultra-PC-Knowledge\troubleshoot\` (what the index reads),
then re-run `python ultra.py fix index` and copy the changed file back here to
commit. Keep sections under `##` headings — the indexer chunks on headings
(fence-aware), so one symptom per section retrieves cleanly.
