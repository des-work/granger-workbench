"""[4] Reference & Utilities — the 'why didn't I have this already' bucket.

File hashing/checksums, text encode/decode, hash identification, regex tester,
and password strength/entropy.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import math
import re
import urllib.parse

from . import core, ui


# --------------------------------------------------------------------------- #
#  File hashing / checksums
# --------------------------------------------------------------------------- #

def hash_file(ctx=None) -> None:
    ui.clear(); ui.title_bar("File Hash / Checksum", "MD5 / SHA-1 / SHA-256")
    path = ui.ask_open_file("Choose a file to hash")
    if not path:
        return
    algos = {"MD5": hashlib.md5(), "SHA1": hashlib.sha1(), "SHA256": hashlib.sha256()}
    try:
        import os
        size = os.path.getsize(path)
        read = 0
        with open(path, "rb") as fh:
            while chunk := fh.read(1024 * 1024):
                for h in algos.values():
                    h.update(chunk)
                read += len(chunk)
                if size:
                    pct = read * 100 // size
                    print(f"\r  hashing... {pct:3d}%", end="", flush=True)
        print()
    except Exception as exc:
        ui.popup_error(f"Could not read file:\n{exc}"); return

    r = core.Report("File Hash")
    r.section(path)
    r.line(f"  size   {size:,} bytes")
    for name, h in algos.items():
        r.line(f"  {name:<7} {h.hexdigest()}")
    body = r.text()
    ui.show_text(body, "Ultra-PC — File Hash")

    # Offer to verify against an expected checksum
    if ui.ask_yesno("Verify against an expected checksum?", "Verify"):
        expected = (ui.ask_string("Paste the expected hash:") or "").strip().lower()
        if expected:
            match = next((n for n, h in algos.items()
                          if h.hexdigest().lower() == expected), None)
            if match:
                ui.popup_info(f"MATCH — {match} checksum verified.", "Verify")
            else:
                ui.popup_error("NO MATCH — file does not match the expected hash.", "Verify")
    ui.pause()


# --------------------------------------------------------------------------- #
#  Text encode / decode
# --------------------------------------------------------------------------- #

def text_codec(ctx=None) -> None:
    ui.clear(); ui.title_bar("Encode / Decode", "base64 / hex / url / rot13")
    ops = [
        ("1", "Text -> Base64"), ("2", "Base64 -> Text"),
        ("3", "Text -> Hex"),    ("4", "Hex -> Text"),
        ("5", "URL encode"),     ("6", "URL decode"),
        ("7", "ROT13"),
    ]
    choice = ui.menu("Encode / Decode", "pick a transform", ops, "Back")
    if choice == "0" or not choice:
        return
    s = ui.ask_string("Enter the input text:")
    if s is None:
        return
    try:
        if choice == "1":  out = base64.b64encode(s.encode()).decode()
        elif choice == "2": out = base64.b64decode(s).decode("utf-8", "replace")
        elif choice == "3": out = s.encode().hex()
        elif choice == "4": out = bytes.fromhex(s.strip()).decode("utf-8", "replace")
        elif choice == "5": out = urllib.parse.quote(s)
        elif choice == "6": out = urllib.parse.unquote(s)
        elif choice == "7": out = s.encode().decode("ascii", "ignore").translate(
            str.maketrans(
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm"))
        else:
            return
    except (binascii.Error, ValueError, UnicodeDecodeError) as exc:
        ui.popup_error(f"Could not transform input:\n{exc}"); return
    ui.show_text(f"INPUT:\n{s}\n\nOUTPUT:\n{out}", "Ultra-PC — Result")
    ui.pause()


# --------------------------------------------------------------------------- #
#  Hash identifier
# --------------------------------------------------------------------------- #

_HASH_SHAPES = {
    32: ["MD5", "NTLM", "MD4"],
    40: ["SHA-1"],
    56: ["SHA-224"],
    64: ["SHA-256"],
    96: ["SHA-384"],
    128: ["SHA-512"],
}


def hash_id(ctx=None) -> None:
    ui.clear(); ui.title_bar("Hash Identifier", "guess a hash type by shape")
    h = (ui.ask_string("Paste a hash:") or "").strip()
    if not h:
        return
    if not re.fullmatch(r"[0-9a-fA-F]+", h):
        ui.popup_error("Not pure hex — could be base64 or bcrypt-style.\n"
                       "bcrypt: starts with $2a$/$2b$.  Argon2: starts with $argon2.")
        return
    candidates = _HASH_SHAPES.get(len(h))
    if candidates:
        ui.popup_info(f"Length {len(h)} hex chars → likely: {', '.join(candidates)}", "Hash ID")
    else:
        ui.popup_info(f"Length {len(h)} hex chars — no common match.", "Hash ID")
    ui.pause()


# --------------------------------------------------------------------------- #
#  Regex tester
# --------------------------------------------------------------------------- #

def regex_tester(ctx=None) -> None:
    ui.clear(); ui.title_bar("Regex Tester", "test a pattern against sample text")
    pattern = ui.ask_string("Enter the regex pattern:")
    if not pattern:
        return
    sample = ui.ask_string("Enter the test text:")
    if sample is None:
        return
    try:
        rx = re.compile(pattern)
    except re.error as exc:
        ui.popup_error(f"Invalid pattern:\n{exc}"); return
    matches = list(rx.finditer(sample))
    lines = [f"Pattern: {pattern}", f"Text:    {sample}", "",
             f"{len(matches)} match(es):"]
    for i, m in enumerate(matches, 1):
        lines.append(f"  [{i}] '{m.group(0)}' at {m.start()}-{m.end()}")
        for gi, g in enumerate(m.groups(), 1):
            lines.append(f"        group {gi}: {g!r}")
    ui.show_text("\n".join(lines), "Ultra-PC — Regex")
    ui.pause()


# --------------------------------------------------------------------------- #
#  Password strength / entropy
# --------------------------------------------------------------------------- #

def password_entropy(ctx=None) -> None:
    ui.clear(); ui.title_bar("Password Entropy", "strength estimate (offline)")
    pw = ui.ask_string("Enter a password to evaluate (not stored):")
    if not pw:
        return
    pool = 0
    if re.search(r"[a-z]", pw): pool += 26
    if re.search(r"[A-Z]", pw): pool += 26
    if re.search(r"[0-9]", pw): pool += 10
    if re.search(r"[^a-zA-Z0-9]", pw): pool += 33
    bits = len(pw) * math.log2(pool) if pool else 0
    if bits < 40:   verdict = "WEAK — crackable quickly"
    elif bits < 60: verdict = "FAIR — okay for low-value accounts"
    elif bits < 80: verdict = "STRONG"
    else:           verdict = "VERY STRONG"
    # rough offline crack-time at 10^10 guesses/sec
    guesses = pool ** len(pw) if pool else 0
    seconds = guesses / 1e10 / 2
    ui.popup_info(
        f"Length: {len(pw)}\nCharacter pool: {pool}\nEntropy: {bits:.1f} bits\n"
        f"Verdict: {verdict}\n\n"
        f"Est. offline crack time (10^10/s): {_human_time(seconds)}",
        "Password Entropy")
    ui.pause()


def _human_time(seconds: float) -> str:
    if seconds < 1: return "instant"
    for unit, size in (("years", 31557600), ("days", 86400), ("hours", 3600),
                       ("minutes", 60)):
        if seconds >= size:
            v = seconds / size
            if unit == "years" and v > 1e6:
                return f"{v:.2e} years (effectively uncrackable)"
            return f"{v:.1f} {unit}"
    return f"{seconds:.0f} seconds"


# --------------------------------------------------------------------------- #
#  Registration
# --------------------------------------------------------------------------- #

def register() -> core.Category:
    cat = core.Category("ref", "Reference & Utilities")
    cat.add("hash", "File hash / checksum + verify", hash_file)
    cat.add("codec", "Encode / decode (base64/hex/url/rot13)", text_codec)
    cat.add("hashid", "Identify a hash type", hash_id)
    cat.add("regex", "Regex tester", regex_tester)
    cat.add("pw", "Password strength / entropy", password_entropy)
    return cat
