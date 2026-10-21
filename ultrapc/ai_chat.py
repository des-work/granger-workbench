"""The Local AI chat popup — a roomy, Frutiger-Aero styled window for RAG chat
over the offline vault.

Left: streaming conversation in glossy chat bubbles.  Right: pictures + sources
pulled from the local vault.  All work happens off the UI thread and is
marshalled back via a queue so the window stays responsive.
"""

from __future__ import annotations

import threading
import webbrowser
from queue import Queue, Empty

from . import ai, knowledge, core
from . import theme as T


def open_chat_window() -> None:
    import tkinter as tk
    from tkinter import ttk

    if not ai.available():
        _simple_error("No local AI detected.\n\nStart Ollama (it listens on "
                      "127.0.0.1:11434) and try again.")
        return
    if not knowledge.local_zims():
        _simple_error("The Knowledge Vault is empty.\n\nDownload at least one "
                      "corpus first (Knowledge Vault -> Download corpora).")
        return

    root = tk.Tk()
    root.title("Ultra-PC — Offline Knowledge Explorer")
    root.geometry("1200x820")
    root.minsize(940, 600)
    root.configure(bg=T.SKY_HEX)
    T.Scene(root)   # scenic sky-and-grass background

    from . import chat_store
    models = ai.list_models() or ["qwen2.5:14b"]
    default = ai.default_model()
    q: Queue = Queue()
    history: list[dict] = []
    photo_refs: list = []
    busy = {"on": False}
    current_q = {"value": ""}    # tracked so thumbs know which query they're rating
    session_id = chat_store.new_session()
    turn_buf = {"q": "", "sources": [], "images": []}

    # ---- glossy header --------------------------------------------------- #
    header = T.HeaderBar(root, height=58)
    header.pack(fill="x", side="top")

    def _paint_header(_e=None):
        header.delete("txt")
        header.create_text(20, 16, anchor="w", text="Ultra-PC  Knowledge Explorer",
                           fill="white", font=(T.FONT, 16, "bold"), tags="txt")
        header.create_text(21, 38, anchor="w",
                           text="ask · learn · offline — powered by your own AI",
                           fill="#dff1ff", font=(T.FONT, 9), tags="txt")
        w = header.winfo_width()
        header.create_text(w - 18, 29, anchor="e", text="● offline",
                           fill="#bff5c8", font=(T.FONT, 11, "bold"), tags="txt")
    header.bind("<Configure>", lambda e: (header._redraw(e), _paint_header()), add="+")

    # ---- control strip --------------------------------------------------- #
    strip = tk.Frame(root, bg=T.GLASS)
    strip.pack(fill="x", side="top")
    tk.Label(strip, text="  Model:", bg=T.GLASS, fg=T.INK,
             font=(T.FONT, 10, "bold")).pack(side="left", pady=6)
    model_var = tk.StringVar(value=default)
    model_cb = ttk.Combobox(strip, textvariable=model_var, values=models, width=28,
                            state="readonly")
    model_cb.pack(side="left", padx=6)

    def _save_model(*_):
        # persist the pick so it sticks next launch + the CLI honors it
        c = core.load_config(); c["chat_model"] = model_var.get(); core.save_config(c)
    model_cb.bind("<<ComboboxSelected>>", _save_model)

    # context-window picker (larger = more of the vault fed to the model)
    tk.Label(strip, text="  Context:", bg=T.GLASS, fg=T.INK,
             font=(T.FONT, 10, "bold")).pack(side="left", pady=6)
    ctx_var = tk.StringVar(value=str(core.load_config().get("num_ctx", 8192)))
    ctx_cb = ttk.Combobox(strip, textvariable=ctx_var, width=7, state="readonly",
                          values=["2048", "4096", "8192", "16384", "32768"])
    ctx_cb.pack(side="left", padx=6)

    def _save_ctx(*_):
        c = core.load_config()
        try:
            c["num_ctx"] = int(ctx_var.get())
        except ValueError:
            pass
        core.save_config(c)
    ctx_cb.bind("<<ComboboxSelected>>", _save_ctx)

    sem_var = tk.BooleanVar(value=core.load_config().get("use_semantic", True))
    have_embed = ai.embed_model() is not None

    def _toggle_sem():
        c = core.load_config(); c["use_semantic"] = bool(sem_var.get()); core.save_config(c)

    tk.Checkbutton(strip, text="Semantic search", variable=sem_var,
                   command=_toggle_sem, bg=T.GLASS, fg=T.INK,
                   activebackground=T.GLASS, selectcolor="#ffffff",
                   font=(T.FONT, 10), state=("normal" if have_embed else "disabled")
                   ).pack(side="left", padx=(14, 0))
    if not have_embed:
        sem_var.set(False)

    # "◀ previous chats" — persistent session browser
    def open_sessions_dialog():
        _sessions_dialog(root, chat_store, on_load=_load_session)

    tk.Button(strip, text="◀ previous chats", command=open_sessions_dialog,
              bg=T.GLASS, fg=T.INK, font=(T.FONT, 9), relief="flat",
              activebackground="#dff1ff", cursor="hand2"
              ).pack(side="right", padx=(0, 8))

    # ---- main content (glass cards float on the scene, with a wide margin
    #      so the Frutiger sky/grass aesthetic actually shows) --------------- #
    content = tk.Frame(root, bg=T.SKY_HEX)
    content.pack(fill="both", expand=True, padx=22, pady=(16, 14))
    pw = tk.PanedWindow(content, orient="horizontal", sashwidth=14,
                        bg=T.SKY_HEX, bd=0)
    pw.pack(fill="both", expand=True)

    # conversation panel — a depth Card (drop shadow + rounded glass surface)
    left_card = T.Card(pw, radius=18, pad=13, surface="#f8fcff")
    left = left_card.body
    convo = tk.Text(left, wrap="word", font=(T.FONT, 11), padx=14, pady=12,
                    state="disabled", background="#f8fcff", relief="flat",
                    bd=0, spacing2=2)
    cscroll = tk.Scrollbar(left, command=convo.yview)
    convo.configure(yscrollcommand=cscroll.set)
    cscroll.pack(side="right", fill="y")
    convo.pack(side="left", fill="both", expand=True)
    convo.tag_configure("user", background="#d3ebff", foreground=T.INK,
                        font=(T.FONT, 11, "bold"), relief="flat",
                        lmargin1=10, lmargin2=10, rmargin=10, spacing1=8,
                        spacing3=6, borderwidth=6)
    convo.tag_configure("assistant", background="#ffffff", foreground="#152935",
                        lmargin1=10, lmargin2=10, rmargin=10, spacing1=2,
                        spacing3=8, borderwidth=6, relief="flat")
    convo.tag_configure("meta", foreground="#5a7a90",
                        font=(T.FONT, 9, "italic"), lmargin1=10, spacing1=4)
    pw.add(left_card, minsize=470, width=700, stretch="always")

    # media + sources panel — a green-accented depth Card
    right_card = T.Card(pw, radius=18, pad=13, surface="#f8fcff",
                        accent=((150, 205, 110), (43, 143, 214)))
    right = right_card.body
    tk.Label(right, text="  Pictures & sources", bg="#f8fcff", fg=T.INK,
             font=(T.FONT, 11, "bold")).pack(anchor="w", pady=(6, 0))
    tk.Label(right, text="  ▲ helpful  ·  ▼ not relevant  ·  click image → article",
             bg="#f8fcff", fg="#4a7fa5", font=(T.FONT, 8, "italic")
             ).pack(anchor="w", pady=(0, 4))
    mcanvas = tk.Canvas(right, background="#f8fcff", highlightthickness=0, bd=0)
    mscroll = tk.Scrollbar(right, command=mcanvas.yview)
    mcanvas.configure(yscrollcommand=mscroll.set)
    mscroll.pack(side="right", fill="y")
    mcanvas.pack(side="left", fill="both", expand=True)
    media = tk.Frame(mcanvas, background="#f8fcff")
    mcanvas.create_window((0, 0), window=media, anchor="nw")
    media.bind("<Configure>",
               lambda e: mcanvas.configure(scrollregion=mcanvas.bbox("all")))
    pw.add(right_card, minsize=280, width=430)

    # ---- input dock ------------------------------------------------------ #
    dock = tk.Frame(root, bg=T.GLASS, highlightbackground=T.GLASS_EDGE,
                    highlightthickness=2)
    dock.pack(fill="x", side="bottom", padx=14, pady=(0, 14))
    ebox = tk.Frame(dock, bg="#ffffff", highlightbackground=T.GLASS_EDGE,
                    highlightthickness=1)
    ebox.pack(side="left", fill="x", expand=True, padx=8, pady=8)
    entry = tk.Text(ebox, height=3, wrap="word", font=(T.FONT, 11), relief="flat",
                    bd=0, bg="#ffffff", padx=8, pady=6)
    entry.pack(fill="both", expand=True)
    send_btn = T.GelButton(dock, "Ask ▸", None, width=120, height=46, bg=T.GLASS)
    send_btn.pack(side="right", padx=(4, 10), pady=8)

    # ---- helpers --------------------------------------------------------- #
    def add(text, tag):
        convo.configure(state="normal")
        convo.insert("end", text, tag)
        convo.see("end")
        convo.configure(state="disabled")

    def clear_media():
        for w in media.winfo_children():
            w.destroy()
        photo_refs.clear()

    def add_image(pil_img, caption, article_path="", article_url=""):
        from PIL import ImageTk
        from . import ratings
        photo = ImageTk.PhotoImage(pil_img)
        photo_refs.append(photo)
        card = tk.Frame(media, background="#ffffff", highlightbackground=T.GLASS_EDGE,
                        highlightthickness=1)
        card.pack(fill="x", padx=8, pady=6)

        # image (clickable → opens article in browser)
        img_lbl = tk.Label(card, image=photo, background="#ffffff",
                           cursor="hand2" if article_url else "")
        img_lbl.pack(padx=4, pady=4)
        if article_url:
            img_lbl.bind("<Button-1>", lambda e, u=article_url: webbrowser.open(u))

        # caption + thumbs row
        foot = tk.Frame(card, background="#ffffff")
        foot.pack(fill="x", padx=6, pady=(0, 4))
        if article_path:
            up = tk.Label(foot, text="▲", fg="#3fb950", cursor="hand2",
                          background="#eaf6ff", font=(T.FONT, 9, "bold"),
                          padx=4, pady=0, width=2)
            up.pack(side="left", padx=(0, 1))
            dn = tk.Label(foot, text="▼", fg="#f85149", cursor="hand2",
                          background="#eaf6ff", font=(T.FONT, 9, "bold"),
                          padx=4, pady=0, width=2)
            dn.pack(side="left", padx=(0, 6))

            def vote(stars, chosen, other):
                q = current_q.get("value", "")
                if not q:
                    return
                ratings.rate(q, [article_path], stars, mode="image_thumbs")
                if stars >= 4:
                    chosen.configure(background="#c8f7d1", fg="#155724",
                                     text="✓", cursor="")
                else:
                    chosen.configure(background="#f7c8c8", fg="#721c24",
                                     text="✓", cursor="")
                chosen.unbind("<Button-1>")
                other.configure(fg="#c0c8d0", cursor="")
                other.unbind("<Button-1>")

            up.bind("<Button-1>", lambda e: vote(5, up, dn))
            dn.bind("<Button-1>", lambda e: vote(1, dn, up))
        if caption:
            tk.Label(foot, text=caption[:80], wraplength=280, justify="left",
                     font=(T.FONT, 8), fg="#4a6577", background="#ffffff").pack(
                side="left")

    def add_source(title, url, path):
        from . import ratings
        row = tk.Frame(media, background="#f6fcff")
        row.pack(anchor="w", fill="x", padx=10, pady=1)

        up_btn = tk.Label(row, text="▲", fg="#3fb950", cursor="hand2",
                          background="#eaf6ff", font=(T.FONT, 9, "bold"),
                          padx=4, pady=0, width=2, borderwidth=1, relief="flat")
        up_btn.pack(side="left", padx=(0, 1))
        down_btn = tk.Label(row, text="▼", fg="#f85149", cursor="hand2",
                            background="#eaf6ff", font=(T.FONT, 9, "bold"),
                            padx=4, pady=0, width=2, borderwidth=1, relief="flat")
        down_btn.pack(side="left", padx=(0, 6))

        lbl = tk.Label(row, text="🔗 " + title, fg="#0b6fbf", cursor="hand2",
                       wraplength=320, justify="left", background="#f6fcff",
                       font=(T.FONT, 9, "underline"))
        lbl.pack(side="left", anchor="w")
        lbl.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))

        def vote(stars, chosen, other):
            question = current_q.get("value", "")
            if not question:
                return
            ratings.rate(question, [path], stars, mode="thumbs")
            # visual: chosen goes solid + shows checkmark, other dims + disables
            if stars >= 4:
                chosen.configure(background="#c8f7d1", fg="#155724",
                                 text="✓", cursor="")
            else:
                chosen.configure(background="#f7c8c8", fg="#721c24",
                                 text="✓", cursor="")
            chosen.unbind("<Button-1>")
            other.configure(fg="#c0c8d0", cursor="")
            other.unbind("<Button-1>")

        up_btn.bind("<Button-1>", lambda e: vote(5, up_btn, down_btn))
        down_btn.bind("<Button-1>", lambda e: vote(1, down_btn, up_btn))

    def submit(event=None):
        if busy["on"]:
            return "break"
        text = entry.get("1.0", "end").strip()
        if not text:
            return "break"
        entry.delete("1.0", "end")
        busy["on"] = True
        current_q["value"] = text        # so per-source thumbs know which query
        send_btn.set_enabled(False); send_btn.set_text("…")
        clear_media()
        add(f"\n  You\n", "meta")
        add(f"{text}\n", "user")
        threading.Thread(target=worker, args=(text, model_var.get()),
                         daemon=True).start()
        return "break"

    def worker(question, model):
        q.put(("meta", "\n  Searching your local vault…\n"))
        r = ai.retrieve(question, history=history)      # history-aware retrieval
        n = len(r["sources"]); mode = r.get("mode", "keyword")
        if r.get("followup"):
            q.put(("meta", "  (follow-up detected — continuing the previous topic)\n"))
        q.put(("meta", f"  Found {n} article(s) via {mode} search · thinking with "
                       f"{model}…\n"))
        messages = ai.build_messages(question, r["passages"], history[-6:])
        q.put(("astart",))
        answer = ""
        for tok in ai.chat_stream(model, messages):
            answer += tok
            q.put(("token", tok))
        q.put(("aend",))
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})
        for s in r["sources"]:
            q.put(("source", s["title"], s["url"], s.get("path", "")))
        for img in r["images"]:
            im = ai.fetch_image(img["url"])
            if im is not None:
                q.put(("image", im, img.get("alt", ""),
                       img.get("article_path", ""), img.get("article_url", "")))
        # persist the completed turn so this chat lives on across sessions
        try:
            chat_store.save_turn(session_id, question, answer,
                                 r.get("sources") or [], r.get("images") or [])
        except Exception:
            pass
        q.put(("done",))

    def pump():
        try:
            while True:
                item = q.get_nowait()
                kind = item[0]
                if kind == "meta":
                    add(item[1], "meta")
                elif kind == "astart":
                    add("  Local AI\n", "meta"); add("", "assistant")
                elif kind == "token":
                    add(item[1], "assistant")
                elif kind == "aend":
                    add("\n", "assistant")
                elif kind == "source":
                    add_source(item[1], item[2], item[3] if len(item) > 3 else "")
                elif kind == "image":
                    add_image(item[1], item[2],
                              item[3] if len(item) > 3 else "",
                              item[4] if len(item) > 4 else "")
                elif kind == "done":
                    busy["on"] = False
                    send_btn.set_enabled(True); send_btn.set_text("Ask ▸")
        except Empty:
            pass
        root.after(60, pump)

    def _load_session(sid):
        """Replay a saved chat into the current window."""
        nonlocal session_id
        turns = chat_store.load_session(sid)
        if not turns:
            return
        # clear conversation + media, then replay
        convo.configure(state="normal")
        convo.delete("1.0", "end")
        convo.configure(state="disabled")
        clear_media()
        history.clear()
        session_id = sid
        for t in turns:
            add(f"\n  You  \x1b[2m({t.get('ts','')})\x1b[0m\n", "meta")
            add(f"{t.get('q','')}\n", "user")
            add("  Local AI\n", "meta"); add(t.get("a", "") + "\n", "assistant")
            history.append({"role": "user", "content": t.get("q", "")})
            history.append({"role": "assistant", "content": t.get("a", "")})
            for s in t.get("sources", []) or []:
                add_source(s.get("title", ""), s.get("url", ""),
                           s.get("path", ""))
        add("\n  " + f"loaded {len(turns)} turn(s). Continue asking below.\n",
            "meta")

    send_btn.command = submit
    entry.bind("<Return>", submit)
    entry.bind("<Shift-Return>", lambda e: None)
    entry.focus_set()
    add("  Welcome! Ask me anything — I'll pull matching Wikipedia articles and "
        "pictures from your local vault and answer with your own model. "
        "No internet required.\n", "meta")
    _paint_header()
    root.after(60, pump)
    # landing splash: scenic title card + loading animation, then reveal the app
    root.after(180, lambda: T.run_splash(
        root, on_done=lambda: entry.focus_set(),
        title="Ultra-PC", subtitle="Knowledge Explorer"))
    root.mainloop()


def _sessions_dialog(parent, store, on_load) -> None:
    """Small modal listing recent chat sessions with a search box + Load button."""
    import tkinter as tk
    win = tk.Toplevel(parent)
    win.title("Previous chats")
    win.geometry("560x420")
    win.configure(bg=T.GLASS)
    win.transient(parent)
    tk.Label(win, text="Search past chats", bg=T.GLASS, fg=T.INK,
             font=(T.FONT, 11, "bold")).pack(anchor="w", padx=10, pady=(10, 2))

    entry = tk.Entry(win, font=(T.FONT, 10))
    entry.pack(fill="x", padx=10, pady=(0, 6))

    frame = tk.Frame(win, bg="#ffffff", highlightbackground=T.GLASS_EDGE,
                     highlightthickness=1)
    frame.pack(fill="both", expand=True, padx=10, pady=(0, 8))
    listbox = tk.Listbox(frame, font=(T.FONT, 10), bd=0, activestyle="none")
    listbox.pack(side="left", fill="both", expand=True)
    scroll = tk.Scrollbar(frame, command=listbox.yview)
    listbox.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")

    sid_by_index: list[str] = []

    def refresh(query=""):
        listbox.delete(0, "end")
        sid_by_index.clear()
        if query.strip():
            hits = store.search(query.strip())
            for h in hits:
                listbox.insert("end",
                               f"{h['ts']}  {h['q'][:70]}  …{h['snippet'][:70]}")
                sid_by_index.append(h["sid"])
        else:
            for s in store.list_sessions(30):
                listbox.insert("end",
                               f"{s['last_ts']}  ({s['turns']}t)  "
                               f"{s['first_q'][:70]}")
                sid_by_index.append(s["sid"])

    def load():
        sel = listbox.curselection()
        if sel:
            on_load(sid_by_index[sel[0]])
            win.destroy()

    entry.bind("<KeyRelease>", lambda e: refresh(entry.get()))
    listbox.bind("<Double-Button-1>", lambda e: load())

    btns = tk.Frame(win, bg=T.GLASS)
    btns.pack(fill="x", padx=10, pady=(0, 10))
    tk.Button(btns, text="Load selected", command=load, bg=T.GLASS, fg=T.INK,
              cursor="hand2").pack(side="right", padx=2)
    tk.Button(btns, text="Close", command=win.destroy, bg=T.GLASS, fg=T.INK,
              cursor="hand2").pack(side="right", padx=2)

    refresh()


def _simple_error(msg: str) -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox
        r = tk.Tk(); r.withdraw(); r.attributes("-topmost", True)
        messagebox.showerror("Ultra-PC — Local AI", msg, parent=r); r.destroy()
    except Exception:
        print(msg)
