import codecs

with codecs.open('src/mac_version/print_gui_mac.py', 'r', 'utf-8-sig') as f:
    text = f.read()

# 1. Add current_theme getter/setter
if 'def save_theme_pref(theme_name):' not in text:
    config_functions = '''def save_theme_pref(theme_name):
    try:
        data = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f: data = json.load(f)
        data["theme"] = theme_name
        with open(CONFIG_FILE, "w", encoding="utf-8") as f: json.dump(data, f)
    except: pass

def load_theme_pref():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("theme", "system")
        except: pass
    return "system"

def apply_theme(theme_name):
    save_theme_pref(theme_name)
    if theme_name == "dark":
        bg_color = "#252526"
        fg_color = "#cccccc"
        accent_color = "#0e639c"
        accent_hover = "#1177bb"
        text_bg = "#1e1e1e"
        tab_inactive = "#2d2d2d"
        input_bg = "#3c3c3c"
        input_fg = "white"
    elif theme_name == "light":
        bg_color = "#f3f3f3"
        fg_color = "#333333"
        accent_color = "#007acc"
        accent_hover = "#005999"
        text_bg = "#ffffff"
        tab_inactive = "#e8e8e8"
        input_bg = "#ffffff"
        input_fg = "black"
    else:
        # system (macOS native)
        return

    window.configure(bg=bg_color)
    style.configure('.', background=bg_color, foreground=fg_color)
    style.configure('TFrame', background=bg_color)
    style.configure('TLabel', background=bg_color, foreground=fg_color, font=("Helvetica", 10))
    style.configure('TButton', background=accent_color, foreground="black" if theme_name == "light" else "white")
    style.configure('Treeview', background=text_bg, fieldbackground=text_bg, foreground=input_fg)
    
    if 'text_input' in globals():
        text_input.configure(bg=input_bg, fg=input_fg, insertbackground=input_fg)
    if 'dict_input' in globals():
        dict_input.configure(bg=input_bg, fg=input_fg, insertbackground=input_fg)
    if 'inv_dict_input' in globals():
        inv_dict_input.configure(bg=input_bg, fg=input_fg, insertbackground=input_fg)
'''
    import re
    text = re.sub(r'def get_lang\(\):', config_functions + '\n\ndef get_lang():', text)

# 2. Update menus
menu_code = '''menubar = tk.Menu(window)

theme_menu = tk.Menu(menubar, tearoff=0)
theme_menu.add_command(label="Системная (Auto)", command=lambda: apply_theme("system"))
theme_menu.add_command(label="Темная", command=lambda: apply_theme("dark"))
theme_menu.add_command(label="Светлая", command=lambda: apply_theme("light"))
menubar.add_cascade(label="Тема", menu=theme_menu)

lang_menu = tk.Menu(menubar, tearoff=0)
lang_menu.add_command(label="🇷🇺 Русский", command=lambda: save_lang("ru"))
lang_menu.add_command(label="🇬🇧 English", command=lambda: save_lang("en"))
menubar.add_cascade(label="Язык", menu=lang_menu)
window.config(menu=menubar)'''

if 'theme_menu = tk.Menu' not in text:
    text = re.sub(r'menubar = tk\.Menu\(window\).*?window\.config\(menu=menubar\)', menu_code, text, flags=re.DOTALL)

# 3. add run at the bottom
if 'apply_theme(current_theme)' not in text:
    text = text.replace('current_lang = get_lang()', 'current_theme = load_theme_pref()\napply_theme(current_theme)\ncurrent_lang = get_lang()')


with codecs.open('src/mac_version/print_gui_mac.py', 'w', 'utf-8-sig') as f:
    f.write(text)

print("Mac Theme Patched!")
