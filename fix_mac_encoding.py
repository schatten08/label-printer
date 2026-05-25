import codecs

with codecs.open('src/mac_version/print_gui_mac.py', 'r', 'utf-8-sig') as f:
    text = f.read()

start_idx = text.find("LANGS = {")
if start_idx != -1:
    after_langs_idx = text.find("def get_lang()")
    if after_langs_idx != -1:
        text = text[:start_idx] + '''LANGS = {
    "ru": {
        "title": "Печать этикеток",
        "printer": "Принтер:",
        "warn": "⚠️ Убедитесь, что принтер физически включен кнопкой питания!",
        "t_batch": " 📝 Список (Массовая) ",
        "d_batch": "Введите инвентарные номера (можно таблицей):",
        "btn_p": "Отправить на принтер",
        "t_scan": " 🔍 Сканер коробок / оборудования ",
        "d_dict": "1. Вставьте 2 колонки из Excel (SN и Label):",
        "d_scan": "2. Фокус сюда (перейдет автоматически) и сканируйте:",
        "t_inv": " 📋 Инвентаризация ",
        "i_top": "1. Вставьте базу (Label / Модель):",
        "btn_ld": "⚙️ Загрузить базу",
        "i_scan": "2. Сканируйте:",
        "btn_ex": "💾 Экспорт отчета в CSV",
        "c_stat": "Статус",
        "c_lbl": "Label (Инвентарный №)",
        "c_mod": "Модель",
        "s_pend": "❌ Ожидает",
        "s_found": "✅ Найдено",
        "s_stats": "Найдено:",
        "found_stat": "Найдено:"
    },
    "en": {
        "title": "Label Printing",
        "printer": "Printer:",
        "warn": "⚠️ Make sure the printer is physically turned on!",
        "t_batch": " 📝 List (Batch) ",
        "d_batch": "Enter inventory numbers (table format supported):",
        "btn_p": "Send to Printer",
        "t_scan": " 🔍 Equipment Scanner ",
        "d_dict": "1. Paste 2 columns from Excel (SN and Label):",
        "d_scan": "2. Focus here (moves automatically) and scan:",
        "t_inv": " 📋 Inventory Audit ",
        "i_top": "1. Paste database (Label / Model):",
        "btn_ld": "⚙️ Load Database",
        "i_scan": "2. Scan:",
        "btn_ex": "💾 Export Report",
        "c_stat": "Status",
        "c_lbl": "Label (Inventory ID)",
        "c_mod": "Model",
        "s_pend": "❌ Pending",
        "s_found": "✅ Found",
        "s_stats": "Found:"
    }
}\n\n''' + text[after_langs_idx:]
        
with codecs.open('src/mac_version/print_gui_mac.py', 'w', 'utf-8-sig') as f:
    f.write(text.replace('?? ', '🍏 '))

print("Mac encoding fixed!")
