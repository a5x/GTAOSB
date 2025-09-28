import subprocess
import tkinter as tk
import sys
import threading
import keyboard
from datetime import datetime, timedelta
import os
from PIL import Image, ImageTk

rule_name = "GTA Online Bloquer la save"

# Durées
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

def format_hm(dt: datetime) -> str:
    return dt.strftime("%H:%M")

def format_dm(dt: datetime) -> str:
    return dt.strftime("%d/%m")

option_log = {name: f"{name} : —" for name in OPTIONS_MINUTES.keys()}

def save_line_to_file(display_line: str, now_dt: datetime, target_dt: datetime):
    """
    Ecrit dans heures.txt en ajoutant la date (jj/mm) à côté de CHAQUE heure,
    sans toucher à l'affichage UI.
    """
    file_line = (
        f"{display_line.split(' : ')[0]} : "
        f"{format_hm(now_dt)} ({format_dm(now_dt)}) = "
        f"{format_hm(target_dt)} ({format_dm(target_dt)})"
    )
    try:
        with open(HEURES_PATH, "a", encoding="utf-8") as f:
            f.write(file_line + "\n")
    except Exception as e:
        cayo_status.config(text=f"Erreur sauvegarde: {e}", fg="orange")
    else:
        cayo_status.config(text="Enregistré dans heures.txt", fg="lime")

def add_for_option(option_name: str):
    """Clique sur + pour une option : calcule, affiche (UI), et sauvegarde (fichier avec date)"""
    minutes = OPTIONS_MINUTES.get(option_name, 46)
    now = datetime.now()
    target = now + timedelta(minutes=minutes)

    display_line = f"{option_name} : {format_hm(now)} = {format_hm(target)}"
    option_log[option_name] = display_line
    refresh_log_listbox()

    save_line_to_file(display_line, now, target)

def refresh_log_listbox():
    """Reconstruit la liste du log dans l'ordre des options"""
    log_list.delete(0, tk.END)
    for name in OPTIONS_MINUTES.keys():
        log_list.insert(tk.END, option_log.get(name, f"{name} : —"))

def clear_heures_file():
    """Vide heures.txt et remet les lignes du log à —"""
    try:
        with open(HEURES_PATH, "w", encoding="utf-8") as f:
            f.write("")
        for k in option_log.keys():
            option_log[k] = f"{k} : —"
        refresh_log_listbox()
    except Exception as e:
        cayo_status.config(text=f"Erreur clear: {e}", fg="orange")
    else:
        cayo_status.config(text="heures.txt vidé", fg="lime")

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
            status_label.config(text="GTA Online Bloquer Save : Activer", fg="lime")
            btn.config(bg="green", activebackground="darkgreen")
            print("[INFO] GTA Online Bloquer Save : Activer")
    else:
        if force is None or force == "off":
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={rule_name}"],
            )
            status_label.config(text="GTA Online Bloquer Save : Desactiver", fg="red")
            btn.config(bg="red", activebackground="darkred")
            print("[INFO] GTA Online Bloquer Save : Desactiver")

def on_close():
    print("[EXIT] Fermeture du programme.")
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

root = tk.Tk()
root.title("GTAO Save Blocker 1.3")
root.configure(bg="#1e1e1e")

top_frame = tk.Frame(root, bg="#1e1e1e")
top_frame.pack(pady=(10, 6))

# Bouton firewall
btn = tk.Button(top_frame, text="Bloquer la save", command=firewall,
                bg="red", fg="white", font=("Arial", 12),
                activebackground="darkred")
btn.pack(side="left", padx=(20, 10))

#icone
try:
    img_path = os.path.join(APP_DIR, "r.png")
    pil_img = Image.open(img_path)
    pil_img = pil_img.resize((48, 48), Image.LANCZOS)
    tk_img = ImageTk.PhotoImage(pil_img)
    img_label = tk.Label(top_frame, image=tk_img, bg="#1e1e1e")
    img_label.image = tk_img 
    img_label.pack(side="left", padx=20)
except Exception as e:
    print(f"[WARN] Impossible de charger r.png : {e}")

status_label = tk.Label(root, text="Statut actuel : Inconnu",
                        font=("Arial", 10), bg="#1e1e1e", fg="white")
status_label.pack(pady=3)

instruction_label = tk.Label(root,
                             text="INSER = activer | FIN = désactiver | SUPPR = fermer le tool",
                             font=("Arial", 9), bg="#1e1e1e", fg="orange")
instruction_label.pack(pady=5)

sep = tk.Frame(root, height=1, bg="#444444")
sep.pack(fill="x", padx=10, pady=8)

#Interface des heures dans la fenetre des logs
options_frame = tk.Frame(root, bg="#1e1e1e")
options_frame.pack(fill="x", padx=12, pady=(6, 2))

title_opt = tk.Label(options_frame, text="Savoir quand refaire :",
                     font=("Arial", 12, "bold"), bg="#1e1e1e", fg="#dddddd")
title_opt.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 6))

row = 1
for name in OPTIONS_MINUTES.keys():
    lbl = tk.Label(options_frame, text=name, font=("Arial", 10),
                   bg="#1e1e1e", fg="#e6e6e6")
    lbl.grid(row=row, column=0, sticky="w", pady=3)

    btn_add = tk.Button(options_frame, text="+", width=3,
                        command=lambda n=name: add_for_option(n),
                        bg="#2d7d46", fg="white", font=("Arial", 11, "bold"),
                        activebackground="#215c33")
    btn_add.grid(row=row, column=1, padx=(8, 0), pady=3, sticky="w")

    tip = tk.Label(options_frame, text=f"+{OPTIONS_MINUTES[name]} min",
                   font=("Arial", 9), bg="#1e1e1e", fg="gray")
    tip.grid(row=row, column=2, padx=8, sticky="w")

    row += 1

# Bouton pour VIDER heures.txt osef mais bon
clear_btn = tk.Button(options_frame, text="Vider heures.txt",
                      command=clear_heures_file,
                      bg="#7a1f1f", fg="white", font=("Arial", 10, "bold"),
                      activebackground="#5b1515")
clear_btn.grid(row=row, column=0, columnspan=3, sticky="w", pady=(8, 0))

#logs
log_frame = tk.Frame(root, bg="#1e1e1e")
log_frame.pack(fill="both", expand=True, padx=12, pady=(8, 6))

log_title = tk.Label(log_frame, text="Log (une ligne par option)",
                     font=("Arial", 12, "bold"), bg="#1e1e1e", fg="#dddddd")
log_title.grid(row=0, column=0, sticky="w")

log_list = tk.Listbox(log_frame, height=8, bg="#222222", fg="#e6e6e6",
                      selectbackground="#3a3a3a", font=("Consolas", 10),
                      activestyle="none")
log_list.grid(row=1, column=0, sticky="nsew", pady=(6, 0))

log_scroll = tk.Scrollbar(log_frame, orient="vertical", command=log_list.yview)
log_scroll.grid(row=1, column=1, sticky="ns")
log_list.config(yscrollcommand=log_scroll.set)

log_frame.grid_rowconfigure(1, weight=1)
log_frame.grid_columnconfigure(0, weight=1)

cayo_status = tk.Label(root, text="Prêt", font=("Arial", 9), bg="#1e1e1e", fg="gray")
cayo_status.pack(pady=(2, 8))

credit_label = tk.Label(root, text="Made by @jlzerty - IG @uxhk - telegram @enabIe",
                        font=("Arial", 9), bg="#1e1e1e", fg="gray")
credit_label.pack(pady=(0, 10))

root.protocol("WM_DELETE_WINDOW", on_close)
root.attributes("-topmost", True)

refresh_log_listbox()
root.mainloop()
