#!/usr/bin/env python3
"""
Caelestia Clipboard Manager  v3
─────────────────────────────────────────────────────────────────────────────
• Reads ~/.local/state/caelestia/scheme.json for live Material 3 colours
• Click any row  →  copy + auto-paste into previously focused window  →  close
• ✕ button deletes an entry without copying
• History pre-fetched on background thread → window opens instantly
• Escape on search: clears text first press, closes window second press
• Scrollbar never overlaps the delete button

Dependencies: python-gobject gtk4 cliphist wl-copy wtype
  Install wtype:  sudo pacman -S wtype
─────────────────────────────────────────────────────────────────────────────
"""


import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gdk, GLib, Gio, Pango

import subprocess
import json
import threading
import time
import sys
from pathlib import Path

CACHE_PATH = Path("/tmp/caelestia_clipboard_cache")

# ─────────────────────────────────────────────────────────────────────────────
# Colour engine
# ─────────────────────────────────────────────────────────────────────────────

SCHEME_PATH = Path.home() / ".local/state/caelestia/scheme.json"

_FB = {
    "primary":              "d4b4c8",
    "onPrimary":            "3b1f30",
    "primaryContainer":     "533546",
    "onPrimaryContainer":   "f2d0e4",
    "secondary":            "c9bcc2",
    "onSecondary":          "31262b",
    "secondaryContainer":   "483c41",
    "onSecondaryContainer": "e6d7dd",
    "error":                "ffb4ab",
    "onError":              "690005",
    "errorContainer":       "7a1921",
    "onErrorContainer":     "ffdad6",
    "surface":              "141214",
    "onSurface":            "eddfe5",
    "surfaceVariant":       "4d3f44",
    "onSurfaceVariant":     "d0c0c6",
    "surfaceContainer":     "1e191c",
    "surfaceContainerHigh": "281f26",
    "outline":              "9a8c91",
    "outlineVariant":       "4d3f44",
}


def _c(key: str, C: dict) -> str:
    return C.get(key, _FB.get(key, "888888"))


def _rgba(hex6: str, a: float = 1.0) -> str:
    h = hex6.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{a:.3f})"


def load_colours() -> dict:
    try:
        if SCHEME_PATH.exists():
            raw = json.loads(SCHEME_PATH.read_text())
            return {**_FB, **raw.get("colours", {})}
    except Exception:
        pass
    return _FB.copy()


def build_css(C: dict) -> str:
    bg     = _c("surface",              C)
    bg_hi  = _c("surfaceContainerHigh", C)
    bg_lo  = _c("surfaceContainer",     C)
    fg     = _c("onSurface",            C)
    fg_dim = _c("onSurfaceVariant",     C)
    pri    = _c("primary",              C)
    pri_c  = _c("primaryContainer",     C)
    err    = _c("error",                C)
    err_c  = _c("errorContainer",       C)
    on_ec  = _c("onErrorContainer",     C)
    sec_c  = _c("secondaryContainer",   C)
    on_sc  = _c("onSecondaryContainer", C)
    ol     = _c("outline",              C)
    ol_var = _c("outlineVariant",       C)

    return f"""
* {{
    font-family: "Rubik", "Inter", "Cantarell", sans-serif;
    font-size: 14px;
    outline: none;
    -gtk-icon-style: symbolic;
}}

window {{
    background-color: rgba(20,18,20,0.85); /* transparent */
    color: #{fg};
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.08);
}}

/* ── Header ──────────────────────────────────────────────────────────── */
.header {{
    background-color: #{bg_lo};
    padding: 14px 16px 10px 16px;
    border-bottom: 1px solid {_rgba(ol_var, 0.45)};
    border-radius: 20px 20px 0 0;
}}
.app-title {{
    font-size: 15px;
    font-weight: 600;
    color: #{fg};
    letter-spacing: 0.015em;
}}
.count-badge {{
    font-size: 11px;
    font-weight: 500;
    color: #{fg_dim};
    background-color: {_rgba(ol_var, 0.3)};
    border-radius: 10px;
    padding: 2px 8px;
}}
.close-btn {{
    background-color: {_rgba(ol_var, 0.28)};
    color: #{fg_dim};
    border: none;
    border-radius: 12px;
    padding: 4px 10px;
    font-size: 12px;
    min-width: 0;
    min-height: 0;
    transition: background-color 140ms ease, color 140ms ease;
}}
.close-btn:hover {{
    background-color: #{err_c};
    color: #{on_ec};
}}

/* ── Search ──────────────────────────────────────────────────────────── */
searchentry {{
    background-color: #{bg_hi};
    color: #{fg};
    border: 1.5px solid {_rgba(ol_var, 0.55)};
    border-radius: 24px;
    padding: 7px 14px;
    font-size: 13.5px;
    caret-color: #{pri};
    transition: border-color 180ms ease;
}}
searchentry:focus {{
    border-color: #{pri};
    box-shadow: 0 0 0 2px {_rgba(pri, 0.12)};
}}
searchentry text {{ color: #{fg}; }}
searchentry placeholder {{ color: {_rgba(fg_dim, 0.55)}; }}

/* ── Scrollbar ───────────────────────────────────────────────────────── */
scrolledwindow {{ background: transparent; }}
scrollbar {{
    background: transparent;
    border: none;
    min-width: 4px;
    margin: 4px 2px;
}}
scrollbar slider {{
    background-color: {_rgba(ol, 0.3)};
    border-radius: 4px;
    min-width: 4px;
    margin: 0;
    transition: background-color 200ms ease;
}}
scrollbar slider:hover {{ background-color: {_rgba(pri, 0.5)}; }}

/* ── ListBox: strip ALL GTK default row chrome ───────────────────────── */
list {{
    background: transparent;
    padding: 6px 0;
}}
row {{
    background: transparent;
    padding: 0;
    border: none;
    outline: none;
    box-shadow: none;
}}
row:hover    {{ background: transparent; }}
row:selected {{ background: transparent; }}
row:focus    {{ background: transparent; }}
row:active   {{ background: transparent; }}

/* ── Row wrapper box ─────────────────────────────────────────────────── */
/* Not a button — click handled by GestureClick on this box.
   The ✕ del-btn sits OUTSIDE the gesture area via event propagation stop. */
.clip-row {{
    border-radius: 14px;
    border: 1px solid transparent;
    margin: 2px 8px;
    /* margin-end leaves room so the overlay scrollbar never covers del-btn */
    margin-end: 20px;
    transition: background-color 120ms ease, border-color 120ms ease;
}}
.clip-row:hover {{
    background-color: {_rgba(pri_c, 0.2)};
    border-color: {_rgba(ol_var, 0.45)};
}}

/* ── Row internals ───────────────────────────────────────────────────── */
.clip-index {{
    font-size: 11px;
    font-weight: 600;
    color: {_rgba(fg_dim, 0.65)};
    min-width: 22px;
}}
.clip-label {{
    color: #{fg};
    font-size: 13px;
    font-weight: 400;
}}

/* ── Delete button ───────────────────────────────────────────────────── */
.del-btn {{
    background-color: {_rgba(err_c, 0.6)};
    border: none;
    border-radius: 12px;
    min-width: 32px;
    min-height: 32px;
    padding: 6px;
    transition: all 120ms ease;
}}

.del-btn:hover {{
    background-color: #{err_c};
}}

/* ── Footer ──────────────────────────────────────────────────────────── */
.footer {{
    background-color: #{bg_lo};
    border-top: 1px solid {_rgba(ol_var, 0.45)};
    border-radius: 0 0 20px 20px;
    padding: 10px 16px;
}}
.status-lbl {{
    font-size: 11.5px;
    color: {_rgba(fg_dim, 0.7)};
}}
.clear-btn {{
    background-color: {_rgba(sec_c, 0.65)};
    color: #{on_sc};
    border: none;
    border-radius: 16px;
    padding: 6px 16px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.03em;
    transition: background-color 130ms ease;
}}
.clear-btn:hover {{
    background-color: {_rgba(err_c, 0.85)};
    color: #{on_ec};
}}

/* ── Empty state ─────────────────────────────────────────────────────── */
.empty-lbl {{
    color: {_rgba(fg_dim, 0.55)};
    font-size: 13px;
    font-style: italic;
    padding: 40px 0;
}}
"""


# ─────────────────────────────────────────────────────────────────────────────
# cliphist helper
# ─────────────────────────────────────────────────────────────────────────────

def _cliphist_list() -> list[str]:
    try:
        r = subprocess.run(
            ["cliphist", "list"],
            capture_output=True, text=True, timeout=8,
        )
        return [l for l in r.stdout.splitlines() if l.strip()]
    except FileNotFoundError:
        return ["[cliphist not found – install cliphist]"]
    except subprocess.TimeoutExpired:
        return ["[cliphist timed out]"]


# ─────────────────────────────────────────────────────────────────────────────
# Application
# ─────────────────────────────────────────────────────────────────────────────

class ClipboardApp(Gtk.Application):

    def __init__(self):
        super().__init__(
            application_id="org.caelestia.clipboard",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self._css = Gtk.CssProvider()
        self._history: list[str] = []
        self._scheme_mtime = None

    # ── CSS live-reload ──────────────────────────────────────────────────────

    def _reload_css(self):
        self._css.load_from_string(build_css(load_colours()))

    def _watch_scheme(self):
        def _poll():
            try:
                mt = SCHEME_PATH.stat().st_mtime
            except FileNotFoundError:
                mt = None
            if mt != self._scheme_mtime:
                self._scheme_mtime = mt
                GLib.idle_add(self._reload_css)
            return True  # keep polling
        GLib.timeout_add_seconds(3, _poll)

    # ── Pre-fetch history in parallel with window construction ───────────────
    # Your keybind spawns a fresh process each time (pkill fuzzel || script.sh)
    # so there's no warm cache. cliphist list takes ~100ms. We fire it on a
    # thread immediately so it runs while GTK is drawing the window chrome,
    # making the perceived open time nearly instant.

    def _prefetch(self):
        # Load instantly from cache first
        if CACHE_PATH.exists():
            try:
                cached = CACHE_PATH.read_text().splitlines()
                self._history = cached
                self._repopulate()
            except Exception:
                pass

        # Then update in background
        def _worker():
            data = _cliphist_list()
            try:
                CACHE_PATH.write_text("\n".join(data))
            except Exception:
                pass
            GLib.idle_add(self._on_fetched, data)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_fetched(self, data: list[str]):
        self._history = data
        # Re-apply current search filter (user may have typed already)
        self._repopulate()

    # ── GTK lifecycle ────────────────────────────────────────────────────────

    def do_activate(self):
        display = Gdk.Display.get_default()
        Gtk.StyleContext.add_provider_for_display(
            display, self._css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
        self._reload_css()
        self._watch_scheme()
        self._prefetch()       # fire history fetch NOW, parallel to UI build
        self._build_window()

    def _build_window(self):
        self.win = Gtk.ApplicationWindow(application=self)
        self.win.set_title("Clipboard Manager")
        self.win.set_default_size(560, 560)
        self.win.set_resizable(True)
        self.win.set_decorated(False)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.win.set_child(root)

        # ── Header
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        header.add_css_class("header")

        title_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        title_lbl = Gtk.Label(label="Clipboard History")
        title_lbl.add_css_class("app-title")
        title_lbl.set_xalign(0)
        title_lbl.set_hexpand(True)

        self._count_lbl = Gtk.Label(label="…")
        self._count_lbl.add_css_class("count-badge")

        close_btn = Gtk.Button(label="✕")
        close_btn.add_css_class("close-btn")
        close_btn.connect("clicked", lambda _: self.win.close())

        title_row.append(title_lbl)
        title_row.append(self._count_lbl)
        title_row.append(close_btn)

        # ── Search
        # FIX: Key controller goes ON THE SEARCH WIDGET, not the window.
        # In GTK4 the SearchEntry consumes keyboard events first. If we attach
        # to the window, Escape is swallowed by the entry's internal handler
        # before it ever reaches our controller. Attaching directly to the
        # entry widget gives us first-dibs via CAPTURE phase.
        self._search = Gtk.SearchEntry()
        self._search.set_placeholder_text("Search clipboard history…")
        self._search.connect("search-changed", self._on_search)

        kc = Gtk.EventControllerKey()
        kc.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        kc.connect("key-pressed", self._on_key)
        self._search.add_controller(kc)

        header.append(title_row)
        header.append(self._search)
        root.append(header)

        # ── List
        self._listbox = Gtk.ListBox()
        self._listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self._listbox.set_show_separators(False)

        # OVERLAY scrolling: scrollbar floats on top of content, never
        # pushes content or reserves permanent space beside the delete button.
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_overlay_scrolling(True)

        # Add inner padding container (IMPORTANT)
        scroll_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scroll_box.set_margin_end(12)   # 👈 KEY FIX (adjust 12–20 as you like)

        scroll_box.append(self._listbox)
        scroll.set_child(scroll_box)
        root.append(scroll)

        # ── Footer
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        footer.add_css_class("footer")

        self._status_lbl = Gtk.Label(label="Loading…")
        self._status_lbl.add_css_class("status-lbl")
        self._status_lbl.set_hexpand(True)
        self._status_lbl.set_xalign(0)

        clear_btn = Gtk.Button(label="Clear All")
        clear_btn.add_css_class("clear-btn")
        clear_btn.connect("clicked", self._clear_all)

        footer.append(self._status_lbl)
        footer.append(clear_btn)
        root.append(footer)

        self.win.present()
        self.win.set_opacity(0.92)  # adjust 0.85–0.95
        self._search.grab_focus()

    # ── Keyboard handler ─────────────────────────────────────────────────────
    # Attached to the search entry in CAPTURE phase so we intercept Escape
    # before GTK's internal SearchEntry handler clears/consumes it.

    def _on_key(self, ctrl, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            if self._search.get_text():
                self._search.set_text("")
                self._search.grab_focus()
            else:
                self.win.close()
            return True  # consumed — stop further propagation
        return False

    # ── Search handler ───────────────────────────────────────────────────────

    def _on_search(self, entry):
        # Always repopulate from cached self._history.
        # If prefetch hasn't finished yet, self._history is [] and we show
        # the loading state; _on_fetched will call _repopulate when ready.
        self._repopulate()

    def _repopulate(self):
        query = self._search.get_text().lower().strip() if hasattr(self, "_search") else ""
        self._populate(self._history, query)

    # ── List rendering ───────────────────────────────────────────────────────

    def _clear_listbox(self):
        child = self._listbox.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self._listbox.remove(child)
            child = nxt

    def _populate(self, history: list[str], query: str):
        self._clear_listbox()
        filtered = [i for i in history if not query or query in i.lower()]

        if not filtered:
            lbl = Gtk.Label(
                label="No results." if query else "Clipboard is empty."
            )
            lbl.add_css_class("empty-lbl")
            self._listbox.append(lbl)
        else:
            for idx, item in enumerate(filtered):
                self._listbox.append(self._make_row(idx + 1, item))

        total = len(history)
        shown = len(filtered)
        self._count_lbl.set_label(f"{shown} / {total}" if query else str(total))
        self._status_lbl.set_label(
            f"{shown} result{'s' if shown != 1 else ''} for \"{query}\""
            if query else
            f"{total} entr{'ies' if total != 1 else 'y'} — click any to copy & paste"
        )

    def _make_row(self, idx: int, item: str) -> Gtk.ListBoxRow:
        # ── FIX: row is a Box + GestureClick, NOT a nested Button.
        #
        # The previous version put del_btn inside a row_btn (Button inside
        # Button). In GTK4, clicking del_btn fired _on_delete_clicked but
        # ALSO triggered row_btn's clicked signal (the gesture bubble), which
        # called _on_row_clicked and immediately closed the window — so delete
        # appeared broken (window closed before cliphist delete ran visibly).
        #
        # Solution: the row box has a GestureClick. The del_btn is a sibling
        # in the same box. del_btn's own clicked signal calls
        # gesture.set_state(DENIED) to stop the row gesture from firing.

        lbrow = Gtk.ListBoxRow()
        lbrow.set_activatable(False)
        lbrow.set_selectable(False)

        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row_box.add_css_class("clip-row")
        row_box.set_margin_start(0)
        row_box.set_margin_end(0)

        # Padding inside the row box
        row_box.set_margin_top(0)
        row_box.set_margin_bottom(0)

        # Inner content padding via a nested box so the gesture covers it all
        inner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        inner.set_hexpand(True)
        inner.set_margin_start(12)
        inner.set_margin_end(8)
        inner.set_margin_top(9)
        inner.set_margin_bottom(9)

        idx_lbl = Gtk.Label(label=str(idx))
        idx_lbl.add_css_class("clip-index")
        idx_lbl.set_xalign(1)
        idx_lbl.set_valign(Gtk.Align.CENTER)

        display = item.partition("\t")[2] or item
        preview = display.replace("\n", " ").replace("\r", "").strip()
        if len(preview) > 88:
            preview = preview[:88] + "…"

        clip_lbl = Gtk.Label(label=preview)
        clip_lbl.add_css_class("clip-label")
        clip_lbl.set_xalign(0)
        clip_lbl.set_hexpand(True)
        clip_lbl.set_valign(Gtk.Align.CENTER)
        clip_lbl.set_ellipsize(Pango.EllipsizeMode.END)

        inner.append(idx_lbl)
        inner.append(clip_lbl)

        # Delete button — sits OUTSIDE inner, directly in row_box
        # so it's a sibling of the gesture target, not nested inside it.
        icon = Gtk.Image.new_from_icon_name("user-trash-symbolic")
        del_btn = Gtk.Button()
        del_btn.set_child(icon)
        del_btn.add_css_class("del-btn")
        del_btn.set_valign(Gtk.Align.CENTER)
        del_btn.set_margin_end(10)

        # GestureClick on the inner content area only (not del_btn)
        gesture = Gtk.GestureClick.new()
        gesture.connect("released", self._on_row_gesture, item)
        inner.add_controller(gesture)

        # When del_btn is clicked, deny the row gesture so it doesn't
        # also trigger copy. This is the clean GTK4-native way.
        def _on_del(btn, captured_item, captured_gesture):
            captured_gesture.set_state(Gtk.EventSequenceState.DENIED)
            self._on_delete_clicked(btn, captured_item)

        del_btn.connect("clicked", _on_del, item, gesture)

        row_box.append(inner)
        row_box.append(del_btn)
        lbrow.set_child(row_box)
        return lbrow

    # ── Actions ──────────────────────────────────────────────────────────────

    def _on_row_gesture(self, gesture, n_press, x, y, item: str):
        if n_press != 1:
            return
        gesture.set_state(Gtk.EventSequenceState.CLAIMED)
        self.win.close()

        def _do():
            try:
                decoded = subprocess.run(
                    ["cliphist", "decode"],
                    input=item, text=True,
                    capture_output=True, timeout=5,
                )
                subprocess.run(
                    ["wl-copy", "--"],
                    input=decoded.stdout, text=True, timeout=5,
                )
                # Wait for focus to return to the target window after ours closes
                time.sleep(0.05)
                subprocess.run(
                    ["wtype", "-M", "ctrl", "v", "-m", "ctrl"],
                    timeout=3,
                )
            except FileNotFoundError:
                pass  # wtype not installed; clipboard is set, paste manually
            except Exception as e:
                print(f"[clipboard] copy/paste error: {e}", file=sys.stderr)

        threading.Thread(target=_do, daemon=True).start()

    def _on_delete_clicked(self, btn, item: str):
        def _do():
            try:
                subprocess.run(
                    ["cliphist", "delete"],
                    input=item, text=True, timeout=5,
                )
                new = _cliphist_list()
                GLib.idle_add(self._on_fetched, new)
            except Exception as e:
                print(f"[clipboard] delete error: {e}", file=sys.stderr)

        threading.Thread(target=_do, daemon=True).start()

    def _clear_all(self, btn):
        def _do():
            try:
                subprocess.run(["cliphist", "wipe"], timeout=5)
                GLib.idle_add(self._on_fetched, [])
            except Exception as e:
                print(f"[clipboard] wipe error: {e}", file=sys.stderr)

        threading.Thread(target=_do, daemon=True).start()


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = ClipboardApp()
    sys.exit(app.run(sys.argv))