import codecs

def patch_file(filepath):
    with codecs.open(filepath, 'r', 'utf-8-sig') as f:
        content = f.read()
    
    # 1. Update LANGS
    if '"s_pend"' not in content:
        content = content.replace(
            '"c_mod": "??????"', 
            '"c_mod": "??????",\n        "s_pend": "? ???????",\n        "s_found": "? ???????",\n        "s_stats": "???????:"'
        )
        content = content.replace(
            '"c_mod": "Model"', 
            '"c_mod": "Model",\n        "s_pend": "? Pending",\n        "s_found": "? Found",\n        "s_stats": "Found:"'
        )
    
    # 2. Update update_texts to refresh table
    refresh_code = '''
    # Update inventory contents on lang switch
    if 'inv_tree' in globals() and 'inv_data' in globals():
        for sn, data in inv_data.items():
            if "???????" in data["status"] or "Found" in data["status"]:
                data["status"] = l["s_found"]
            else:
                data["status"] = l["s_pend"]
            inv_tree.set(data["item_id"], "status", data["status"])
        if 'update_inv_stats' in globals():
            update_inv_stats()
'''
    if 'inv_tree.heading("rest", text=l["c_mod"])' in content and 'for sn, data in inv_data.items():' not in content:
        content = content.replace(
            'inv_tree.heading("rest", text=l["c_mod"])',
            'inv_tree.heading("rest", text=l["c_mod"])' + refresh_code
        )

    # 3. Update load_inventory static strings
    content = content.replace(
        'status = "? ???????"',
        'status = LANGS[current_lang]["s_pend"]'
    )
    
    # 4. Update update_inv_stats
    content = content.replace(
        'found = sum(1 for v in inv_data.values() if "???????" in v["status"])',
        'found = sum(1 for v in inv_data.values() if "???????" in v["status"] or "Found" in v["status"])'
    )
    content = content.replace(
        'inv_stats_var.set(f"???????: {found} / {total}")',
        'inv_stats_var.set(f"{LANGS[current_lang][\\"s_stats\\"]} {found} / {total}")'
    )

    # 5. Update on_inv_scan static string
    content = content.replace(
        'new_st = "? ???????"',
        'new_st = LANGS[current_lang]["s_found"]'
    )

    with codecs.open(filepath, 'w', 'utf-8-sig') as f:
        f.write(content)

patch_file("src/windows_version/print_gui.py")
patch_file("src/mac_version/print_gui_mac.py")
print("LANGS patched!")
