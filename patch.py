import re

ru_dict = '''
LANGS = {
    "ru": {
        "title": "?????? ????????",
        "printer": "???????:",
        "warn": "?? ?????????, ??? ??????? ????????? ??????? ??????? ???????!",
        "t_batch": " ?? ?????? (????????) ",
        "d_batch": "??????? ??????????? ?????? (????? ????????):",
        "btn_p": "????????? ?? ???????",
        "t_scan": " ?? ?????? ??????? / ???????????? ",
        "d_dict": "1. ???????? 2 ??????? ?? Excel (SN ? Label):",
        "d_scan": "2. ????? ???? (???????? ?????????????) ? ??????????:",
        "t_inv": " ?? ?????????????? ",
        "i_top": "1. ???????? ???? (Label / ??????):",
        "btn_ld": "?? ????????? ????",
        "i_scan": "2. ??????????:",
        "btn_ex": "?? ??????? ?????? ? CSV",
        "c_stat": "??????",
        "c_lbl": "Label (??????????? ?)",
        "c_mod": "??????"
    },
    "en": {
        "title": "Label Printing",
        "printer": "Printer:",
        "warn": "?? Make sure the printer is physically turned on!",
        "t_batch": " ?? List (Batch) ",
        "d_batch": "Enter inventory numbers (table format supported):",
        "btn_p": "Send to Printer",
        "t_scan": " ?? Equipment Scanner ",
        "d_dict": "1. Paste 2 columns from Excel (SN and Label):",
        "d_scan": "2. Focus here (moves automatically) and scan:",
        "t_inv": " ?? Inventory Audit ",
        "i_top": "1. Paste database (Label / Model):",
        "btn_ld": "?? Load Database",
        "i_scan": "2. Scan:",
        "btn_ex": "?? Export to CSV",
        "c_stat": "Status",
        "c_lbl": "Label (Inventory ID)",
        "c_mod": "Model"
    }
}
def get_lang():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("lang", "ru")
        except: pass
    return "ru"

def save_lang(lang_code):
    try:
        data = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f: data = json.load(f)
        data["lang"] = lang_code
        with open(CONFIG_FILE, "w", encoding="utf-8") as f: json.dump(data, f)
    except: pass
    update_texts(lang_code)

def update_texts(lang):
    global current_lang
    current_lang = lang
    l = LANGS[lang]
    header.config(text="??? " + l["title"])
    printer_lbl.config(text=l["printer"])
    printer_warning.config(text=l["warn"])
    notebook.tab(0, text=l["t_batch"])
    desc_batch.config(text=l["d_batch"])
    print_btn.config(text=l["btn_p"])
    notebook.tab(1, text=l["t_scan"])
    desc_dict.config(text=l["d_dict"])
    desc_scan.config(text=l["d_scan"])
    notebook.tab(2, text=l["t_inv"])
    inv_top_lbl.config(text=l["i_top"])
    btn_load.config(text=l["btn_ld"])
    inv_scan_lbl.config(text=l["i_scan"])
    btn_export.config(text=l["btn_ex"])
    inv_tree.heading("status", text=l["c_stat"])
    inv_tree.heading("sn", text=l["c_lbl"])
    inv_tree.heading("rest", text=l["c_mod"])
'''

def patch_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    # Add dictionaries and functions after apply_theme definition
    if 'LANGS = {' not in text:
        text = text.replace('def apply_theme(theme_name):', ru_dict + '\ndef apply_theme(theme_name):')

    # Menu patch
    menu_patch = '''
lang_menu = tk.Menu(menubar, tearoff=0)
lang_menu.add_command(label="???? ???????", command=lambda: save_lang("ru"))
lang_menu.add_command(label="???? English", command=lambda: save_lang("en"))
menubar.add_cascade(label="???? / Lang", menu=lang_menu)
'''
    if 'menubar.add_cascade(label="????' not in text:
        text = text.replace('menubar.add_cascade(label="????", menu=theme_menu)', 'menubar.add_cascade(label="????", menu=theme_menu)\n' + menu_patch)

    # UI assignments rename variables so we can update them in update_texts
    text = text.replace('ttk.Label(printer_frame, text="???????:",', 'printer_lbl = ttk.Label(printer_frame, text="???????:",')
    text = text.replace('ttk.Label(printer_frame, text="???????:").pack(side=tk.LEFT)', 'printer_lbl.pack(side=tk.LEFT)')
    text = text.replace('header = ttk.Label(window, text="??? ?????? ????????",', 'header = ttk.Label(window, text="??? ?????? ????????",')
    text = text.replace('ttk.Label(inv_top_frame, text="1. ???????? ???? (Label / ??????):").pack(side=tk.LEFT)', 'inv_top_lbl = ttk.Label(inv_top_frame, text="1. ???????? ???? (Label / ??????):")\ninv_top_lbl.pack(side=tk.LEFT)')
    text = text.replace('ttk.Button(tab_inv, text="?? ????????? ????", command=load_inventory).pack(pady=2)', 'btn_load = ttk.Button(tab_inv, text="?? ????????? ????", command=load_inventory)\nbtn_load.pack(pady=2)')
    text = text.replace('ttk.Label(inv_scan_frame, text="2. ??????????:").pack(side=tk.LEFT)', 'inv_scan_lbl = ttk.Label(inv_scan_frame, text="2. ??????????:")\ninv_scan_lbl.pack(side=tk.LEFT)')
    text = text.replace('ttk.Button(tab_inv, text="?? ??????? ?????? ? CSV", command=export_inventory).pack(pady=10)', 'btn_export = ttk.Button(tab_inv, text="?? ??????? ??????", command=export_inventory)\nbtn_export.pack(pady=10)')
    text = text.replace('ttk.Button(tab_inv, text="?? ??????? ??????", command=export_inventory).pack(pady=10)', 'btn_export = ttk.Button(tab_inv, text="?? ??????? ??????", command=export_inventory)\nbtn_export.pack(pady=10)')
    
    # Initialize language call before UI mainloop
    if 'current_lang = get_lang()' not in text:
        text = text.replace('window.mainloop()', 'current_lang = get_lang()\nupdate_texts(current_lang)\nwindow.mainloop()')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)

patch_file('src/windows_version/print_gui.py')
patch_file('src/mac_version/print_gui_mac.py')
print("Patched!")
