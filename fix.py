def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    # printer
    text = text.replace('ttk.Label(printer_frame, text="???????:", font=("Segoe UI", 10)).pack(side=tk.LEFT)', 
                        'printer_lbl = ttk.Label(printer_frame, text="???????:", font=("Segoe UI", 10))\nprinter_lbl.pack(side=tk.LEFT)')
    text = text.replace('ttk.Label(printer_frame, text="???????:", font=("Helvetica", 10)).pack(side=tk.LEFT)', 
                        'printer_lbl = ttk.Label(printer_frame, text="???????:", font=("Helvetica", 10))\nprinter_lbl.pack(side=tk.LEFT)')

    # inventory top
    text = text.replace('ttk.Label(inv_top_frame, text="1. ???????? ???? (Label / ??????):").pack(side=tk.LEFT)', 
                        'inv_top_lbl = ttk.Label(inv_top_frame, text="1. ???????? ???? (Label / ??????):")\ninv_top_lbl.pack(side=tk.LEFT)')

    # load button
    text = text.replace('ttk.Button(tab_inv, text="?? ????????? ????", command=load_inventory).pack(pady=2)', 
                        'btn_load = ttk.Button(tab_inv, text="?? ????????? ????", command=load_inventory)\nbtn_load.pack(pady=2)')

    # inventory scan
    text = text.replace('ttk.Label(inv_scan_frame, text="2. ??????????:").pack(side=tk.LEFT)', 
                        'inv_scan_lbl = ttk.Label(inv_scan_frame, text="2. ??????????:")\ninv_scan_lbl.pack(side=tk.LEFT)')

    # export button
    text = text.replace('ttk.Button(tab_inv, text="?? ??????? ?????? ? CSV", command=export_inventory).pack(pady=10)', 
                        'btn_export = ttk.Button(tab_inv, text="?? ??????? ?????? ? CSV", command=export_inventory)\nbtn_export.pack(pady=10)')
    text = text.replace('ttk.Button(tab_inv, text="?? ??????? ??????", command=export_inventory).pack(pady=10)', 
                        'btn_export = ttk.Button(tab_inv, text="?? ??????? ??????", command=export_inventory)\nbtn_export.pack(pady=10)')

    # Some labels might need 'global' scope inside update_texts but Tkinter widgets are module-level anyway.
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)

fix_file('src/windows_version/print_gui.py')
fix_file('src/mac_version/print_gui_mac.py')
print("Fixed!")
