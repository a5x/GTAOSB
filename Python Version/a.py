import subprocess
import tkinter as tk
import sys
import threading
import keyboard
from datetime import datetime, timedelta
import os
from PIL import Image, ImageTk
import re
import time
import json

rule_name = "GTA Online Bloquer la save"

# Durées en minutes ATTENTION
OPTIONS_MINUTES = {
    "Cayo solo": 166,
    "Cayo duo+": 46,
    "Vincent": 46,
    "Guzman": 46,
    "Bogdan": 46,
    "Casino": 46,
}

APP_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
HEURES_PATH = os.path.join(APP_DIR, "heures.txt")
THEMES_PATH = os.path.join(APP_DIR, "themes.json")

# LES THEMES VOUS POUVEZ EN AJOUTER EN VOUS PRENNENT CE QUE J'ai MIS ET METTRE VOS COULEURS
THEMES = {
    "Noir": {
        "bg": "#1e1e1e", "fg": "#e6e6e6",
        "muted": "#aaaaaa",
        "accent": "#2d7d46", "accent_active": "#215c33",
        "danger": "#7a1f1f", "danger_active": "#5b1515",
        "primary": "#d32f2f", "primary_active": "#9a2323",
        "ok": "lime", "warn": "orange",
        "list_bg": "#222222", "list_fg": "#e6e6e6", "list_sel": "#3a3a3a",
        "divider": "#444444",
    },
    "Blanc": {
        "bg": "#ffffff", "fg": "#222222",
        "muted": "#666666",
        "accent": "#2e7d32", "accent_active": "#1b5e20",
        "danger": "#c62828", "danger_active": "#8e0000",
        "primary": "#e53935", "primary_active": "#b71c1c",
        "ok": "#1b5e20", "warn": "#e65100",
        "list_bg": "#f5f5f5", "list_fg": "#222222", "list_sel": "#d0d0d0",
        "divider": "#dddddd",
    },
    "Rose": {
        "bg": "#2b1d24", "fg": "#ffdce8",
        "muted": "#ffb6cf",
        "accent": "#d81b60", "accent_active": "#ad1457",
        "danger": "#8e0038", "danger_active": "#6a002a",
        "primary": "#ec407a", "primary_active": "#c2185b",
        "ok": "#64ffda", "warn": "#ffcc80",
        "list_bg": "#3a2731", "list_fg": "#ffdce8", "list_sel": "#5a3a48",
        "divider": "#6a4a57",
    },
    "Violet": {
        "bg": "#241b2e", "fg": "#e6dfff",
        "muted": "#b8a8ff",
        "accent": "#7c4dff", "accent_active": "#5e35b1",
        "danger": "#8e24aa", "danger_active": "#6a1b9a",
        "primary": "#9c27b0", "primary_active": "#6a1b9a",
        "ok": "#80e27e", "warn": "#ffd54f",
        "list_bg": "#2f2340", "list_fg": "#e6dfff", "list_sel": "#4b3a66",
        "divider": "#5a4b72",
    },
    "Jaune": {
        "bg": "#2a281a", "fg": "#fff7cc",
        "muted": "#ffe58f",
        "accent": "#fbc02d", "accent_active": "#f57f17",
        "danger": "#ef6c00", "danger_active": "#d84315",
        "primary": "#ffc107", "primary_active": "#ffa000",
        "ok": "#a5d6a7", "warn": "#ffd54f",
        "list_bg": "#3a3722", "list_fg": "#fff7cc", "list_sel": "#5a5432",
        "divider": "#6a6540",
    },
    "Vert": {
        "bg": "#17231b", "fg": "#d8ffe4",
        "muted": "#a7ffcb",
        "accent": "#2e7d32", "accent_active": "#1b5e20",
        "danger": "#00695c", "danger_active": "#004d40",
        "primary": "#00c853", "primary_active": "#00a043",
        "ok": "#69f0ae", "warn": "#ffd740",
        "list_bg": "#1f2f26", "list_fg": "#d8ffe4", "list_sel": "#2f4a3a",
        "divider": "#3a5a48",
    },
}

#persistance du theme
def load_theme_preference(default_name: str = "Noir") -> str:
    """
    Charge le dernier thème depuis themes.json si présent/valide,
    sinon retourne default_name.
    """
    try:
        if os.path.exists(THEMES_PATH):
            with open(THEMES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            name = str(data.get("last_theme", default_name))
            if name in THEMES:
                return name
    except Exception as e:
        print(f"[WARN] Impossible de lire {THEMES_PATH} : {e}")
    return default_name

def save_theme_preference(name: str) -> None:
    """
    Sauvegarde le thème courant dans themes.json au format:
    {"last_theme": "<Nom>"}
    """
    try:
        with open(THEMES_PATH, "w", encoding="utf-8") as f:
            json.dump({"last_theme": name}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] Impossible d'écrire {THEMES_PATH} : {e}")

# Valeur par défaut si aucun fichier n'existe
CURRENT_THEME = load_theme_preference("Noir")

# ANTI SPAM DANS LE FICHIER TEXTE POUR LE GARDER CLEAN
CLICK_DEBOUNCE_MS = 600  # LE TEMPS ENTRE CHAQUE CLIQUE QUI PERMET DE PAS METTRE DE SPAM TU PEUX LE MODIF STV
_last_click_ms = {name: 0 for name in OPTIONS_MINUTES.keys()}
_last_saved_key = {name: None for name in OPTIONS_MINUTES.keys()}  # ICI LA FONCTION QUI DEFINI LE ANTI SPAM

def format_hm(dt: datetime) -> str:
    return dt.strftime("%H:%M")

def format_dm(dt: datetime) -> str:
    return dt.strftime("%d/%m")

option_log = {name: f"{name} : —" for name in OPTIONS_MINUTES.keys()}

# CHARGE LHEURE DU FICHIER
_HEURE_LINE_RE = re.compile(
    r"^(?P<name>.+?) : (?P<start>\d{2}:\d{2}) \(\d{2}/\d{2}\) = (?P<end>\d{2}:\d{2}) \(\d{2}/\d{2}\)$"
)

def load_heures_file():
    if not os.path.exists(HEURES_PATH):
        return
    try:
        with open(HEURES_PATH, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue
                m = _HEURE_LINE_RE.match(line)
                if not m:
                    continue
                name = m.group("name")
                if name not in OPTIONS_MINUTES:
                    continue
                start = m.group("start")
                end = m.group("end")
                option_log[name] = f"{name} : {start} = {end}"
    except Exception as e:
        print(f"[WARN] Impossible de charger heures.txt : {e}")

# Sauvegarde les heures dans le fichier txt
def save_line_to_file(option_name: str, now_dt: datetime, target_dt: datetime):
    start_hm = format_hm(now_dt)
    end_hm = format_hm(target_dt)
    key = f"{start_hm}|{end_hm}"
    if _last_saved_key.get(option_name) == key:
        return
    file_line = (
        f"{option_name} : {start_hm} ({format_dm(now_dt)}) = "
        f"{end_hm} ({format_dm(target_dt)})"
    )
    try:
        with open(HEURES_PATH, "a", encoding="utf-8") as f:
            f.write(file_line + "\n")
        _last_saved_key[option_name] = key
        cayo_status.config(text="Enregistré dans heures.txt", fg=THEMES[CURRENT_THEME]["ok"])
    except Exception as e:
        cayo_status.config(text=f"Erreur de sauvegarde: {e}", fg=THEMES[CURRENT_THEME]["warn"])

# Ajout des heures avec l'anti spam defini au dessus la
def add_for_option(option_name: str):
    now_ms = int(time.time() * 1000)
    last_ms = _last_click_ms.get(option_name, 0)
    if now_ms - last_ms < CLICK_DEBOUNCE_MS:
        return
    _last_click_ms[option_name] = now_ms

    minutes = OPTIONS_MINUTES.get(option_name, 46)
    now = datetime.now()
    target = now + timedelta(minutes=minutes)

    display_line = f"{option_name} : {format_hm(now)} = {format_hm(target)}"
    option_log[option_name] = display_line
    refresh_log_listbox()
    save_line_to_file(option_name, now, target)

# Actualisation des logs
def refresh_log_listbox():
    log_list.delete(0, tk.END)
    for name in OPTIONS_MINUTES.keys():
        log_list.insert(tk.END, option_log.get(name, f"{name} : —"))

# Vider heures.txt
def clear_heures_file():
    try:
        with open(HEURES_PATH, "w", encoding="utf-8") as f:
            f.write("")
        for k in option_log.keys():
            option_log[k] = f"{k} : —"
        for k in _last_saved_key.keys():
            _last_saved_key[k] = None
        refresh_log_listbox()
    except Exception as e:
        cayo_status.config(text=f"Erreur de supression: {e}", fg=THEMES[CURRENT_THEME]["warn"])
    else:
        cayo_status.config(text="heures.txt vidé", fg=THEMES[CURRENT_THEME]["ok"])

# Firewall NE PAS TOUCHER SVP SINON TU VA TOUT BZ
def firewall(force=None):
    check = subprocess.run(
        ["netsh", "advfirewall", "firewall", "show", "rule", f"name={rule_name}"],
        capture_output=True, text=True
    )
    if rule_name not in check.stdout:
        if force is None or force == "on":
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule",
                 f"name={rule_name}", "dir=out", "action=block",
                 "remoteip=192.81.241.170-192.81.241.171", "enable=yes"],
            )
            status_label.config(text="GTA Online Bloquer Save : Activer", fg=THEMES[CURRENT_THEME]["ok"])
            btn.config(bg=THEMES[CURRENT_THEME]["accent"], activebackground=THEMES[CURRENT_THEME]["accent_active"])
            print("[INFO] GTA Online Bloquer Save : Activer")
    else:
        if force is None or force == "off":
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={rule_name}"],
            )
            status_label.config(text="GTA Online Bloquer Save : Desactiver", fg=THEMES[CURRENT_THEME]["danger"])
            btn.config(bg=THEMES[CURRENT_THEME]["primary"], activebackground=THEMES[CURRENT_THEME]["primary_active"])
            print("[INFO] GTA Online Bloquer Save : Desactiver")

# Fermeture du tool a la fin de l'utilisation 
def on_close():
    print("[EXIT] Fermeture du tool.")
    try:
        root.destroy()
    finally:
        sys.exit(0)

def key_listener():
    keyboard.add_hotkey("insert", lambda: (print("[KEY] Activation via INSER"), firewall("on")))
    keyboard.add_hotkey("end",    lambda: (print("[KEY] Désactivation via FIN"), firewall("off")))
    keyboard.add_hotkey("delete", lambda: (print("[KEY] Fermeture via SUPPR"), on_close()))
    keyboard.wait()

threading.Thread(target=key_listener, daemon=True).start()

# ui
root = tk.Tk()
root.title("GTAO Save Blocker 1.4")

# code useless a retirer dans le futur (concerne le bouton bloquer la save avec le logo juste a coter)
top_frame = tk.Frame(root)
top_frame.pack(fill="x", pady=(10, 6))
top_frame.grid_columnconfigure(0, weight=1)
top_frame.grid_columnconfigure(3, weight=1)

# nouveau code pour le bouton bloquer la save
btn = tk.Button(top_frame, text="Bloquer la save", command=firewall,
                font=("Arial", 12))
btn.grid(row=0, column=1, padx=(0, 10), pady=0)

# def de licone rockstar
img_label = tk.Label(top_frame)
try:
    img_path = os.path.join(APP_DIR, "r.png")
    pil_img = Image.open(img_path)
    pil_img = pil_img.resize((48, 48), Image.LANCZOS)
    tk_img = ImageTk.PhotoImage(pil_img)
    img_label.configure(image=tk_img)
    img_label.image = tk_img
except Exception as e:
    print(f"[WARN] Impossible de charger r.png : {e}")
img_label.grid(row=0, column=2, padx=(16, 32))

status_label = tk.Label(root, text="Statut actuel : Inconnu", font=("Arial", 10))
status_label.pack(pady=3)

instruction_label = tk.Label(
    root,
    text="INSER = activer | FIN = désactiver | SUPPR = fermer le tool",
    font=("Arial", 9)
)
instruction_label.pack(pady=5)

# useless pour vous
sep = tk.Frame(root, height=1)
sep.pack(fill="x", padx=10, pady=8)

# interface des heures afficher
options_frame = tk.Frame(root)
options_frame.pack(fill="x", padx=12, pady=(6, 2))

title_opt = tk.Label(options_frame, text="Savoir quand refaire :",
                     font=("Arial", 12, "bold"))
title_opt.grid(row=0, column=0, columnspan=3, pady=(0, 6))

# ici ca garde les choix
option_lbls = []
tip_lbls = []
add_btns = []

row = 1
for name in OPTIONS_MINUTES.keys():
    lbl = tk.Label(options_frame, text=name, font=("Arial", 10))
    lbl.grid(row=row, column=0, pady=3)
    option_lbls.append(lbl)

    btn_add = tk.Button(options_frame, text="+", width=3,
                        command=lambda n=name: add_for_option(n),
                        font=("Arial", 11, "bold"))
    btn_add.grid(row=row, column=1, padx=(8, 0), pady=3)
    add_btns.append(btn_add)

    tip = tk.Label(options_frame, text=f"+{OPTIONS_MINUTES[name]} min",
                   font=("Arial", 9))
    tip.grid(row=row, column=2, padx=8)
    tip_lbls.append(tip)

    row += 1

# centré les lignes
for c in (0, 1, 2):
    options_frame.grid_columnconfigure(c, weight=1)

# Bouton pour vider le fichier heures
clear_btn = tk.Button(options_frame, text="Vider heures.txt",
                      command=clear_heures_file,
                      font=("Arial", 10, "bold"))
clear_btn.grid(row=row, column=0, columnspan=3, pady=(8, 0))

# Logs
log_frame = tk.Frame(root)
log_frame.pack(fill="both", expand=True, padx=12, pady=(8, 6))

log_title = tk.Label(log_frame, text="Log (une ligne par option)",
                     font=("Arial", 12, "bold"))
log_title.grid(row=0, column=0)

log_list = tk.Listbox(log_frame, height=8,
                      selectbackground="#3a3a3a", font=("Consolas", 10),
                      activestyle="none")
log_list.grid(row=1, column=0, sticky="nsew", pady=(6, 0))

log_scroll = tk.Scrollbar(log_frame, orient="vertical", command=log_list.yview)
log_scroll.grid(row=1, column=1, sticky="ns")
log_list.config(yscrollcommand=log_scroll.set)

log_frame.grid_rowconfigure(1, weight=1)
log_frame.grid_columnconfigure(0, weight=1)

# bas du tool
bottom_frame = tk.Frame(root)
bottom_frame.pack(fill="x", padx=12, pady=(2, 0))

theme_var = tk.StringVar(value=CURRENT_THEME)

def on_theme_change(*_):
    global CURRENT_THEME
    CURRENT_THEME = theme_var.get()
    apply_theme(CURRENT_THEME)
    save_theme_preference(CURRENT_THEME)

theme_menu = tk.OptionMenu(bottom_frame, theme_var, *THEMES.keys(), command=lambda _: on_theme_change())
theme_menu.config(width=8)
theme_menu.pack(side="left", anchor="w")

cayo_status = tk.Label(root, text="-", font=("Arial", 9))
cayo_status.pack(pady=(2, 8), anchor="center")

credit_label = tk.Label(root, text="Made by @jlzerty - IG @uxhk - telegram @enabIe",
                        font=("Arial", 9))
credit_label.pack(pady=(0, 10))

root.protocol("WM_DELETE_WINDOW", on_close)
root.attributes("-topmost", True)

#applique le visuel
def apply_theme(name: str):
    t = THEMES[name]
    # la fenetre qui s'ouvre
    root.configure(bg=t["bg"])
    for fr in (top_frame, options_frame, log_frame, sep, bottom_frame):
        fr.configure(bg=t["bg"])

    # Bouton principal
    btn.configure(bg=t["primary"], fg="white", activebackground=t["primary_active"], activeforeground="white")

    # image de fond
    img_label.configure(bg=t["bg"])

    # les Labels
    for lab in (status_label, instruction_label, title_opt, log_title, cayo_status, credit_label):
        lab.configure(bg=t["bg"], fg=t["fg"])
    for lab in option_lbls:
        lab.configure(bg=t["bg"], fg=t["fg"])
    for lab in tip_lbls:
        lab.configure(bg=t["bg"], fg=t["muted"])

    # Les bouton vert +
    for b in add_btns:
        b.configure(bg=t["accent"], fg="white", activebackground=t["accent_active"], activeforeground="white")

    # Bouton clear
    clear_btn.configure(bg=t["danger"], fg="white", activebackground=t["danger_active"], activeforeground="white")

    # separer tout
    sep.configure(bg=t["divider"])

    # Logs
    log_frame.configure(bg=t["bg"])
    log_list.configure(bg=t["list_bg"], fg=t["list_fg"], selectbackground=t["list_sel"])
    log_scroll.configure(bg=t["bg"])

    # le ptit menu pour les themes
    theme_menu.configure(bg=t["list_bg"], fg=t["fg"], activebackground=t["list_sel"], activeforeground=t["fg"])

#charge la base
load_heures_file()
refresh_log_listbox()

# applique le theme sauvegarder dans themes json
apply_theme(CURRENT_THEME)

root.mainloop()
