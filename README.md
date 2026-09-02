# 🖨️ Brother Label Printer

Утилита для быстрой печати наклеек на принтерах Brother (через штрихкод или текстом). Работает на Windows и macOS.

---

## 🚀 БЫСТРЫЙ СТАРТ (Windows)

1.  Скачайте проект целиком (Архив ZIP или `git clone`), распакуйте и запустите `Run_Printer.bat`.
    *   При запуске появится **запрос Windows на подтверждение прав администратора (UAC)** — нажмите "Да" (это единственное действие, которое нужно от пользователя, требуется для установки системного компонента b-PAC).
    *   Дальше скрипт полностью автоматически:
        1. Найдёт/установит Python (если его нет).
        2. Найдёт/установит системный компонент **Brother b-PAC Client Component**.
        3. Установит нужные Python-библиотеки.
        4. Запустит программу.
    *   *Готовый `.exe` не поставляется — большинство корпоративных антивирусов (SentinelOne/Defender) блокируют неподписанные exe-файлы, поэтому запуск через `.bat` надёжнее.*

---

## 📦 УСТАНОВКА (macOS)
1.  Скачайте архив проекта (ZIP).
2.  Запустите [setup/Install_Mac.command](setup/Install_Mac.command).

> ⚠️ **Mac пишет "Install_Mac.command Not Opened / could not verify... free of malware"?**
> Это стандартная блокировка Gatekeeper для неподписанных скриптов, скачанных из интернета — ничего критического.
>
> **Как запустить (выберите любой способ):**
> - **Через Finder:** нажмите **Done** в окне ошибки (НЕ "Move to Trash") → **System Settings → Privacy & Security** → внизу найдите строку про `Install_Mac.command` → **Open Anyway** → подтвердите запуск.
> - **Через правый клик:** Ctrl+клик (или правая кнопка мыши) на `Install_Mac.command` → **Open** → в диалоге нажмите **Open**.
> - **Через Terminal:**
>   ```bash
>   cd ~/Downloads/label-printer-main/setup
>   xattr -d com.apple.quarantine Install_Mac.command
>   chmod +x Install_Mac.command
>   ./Install_Mac.command
>   ```

---

## 🛠️ Основные функции
- **📝 Список**: Печать пачки номеров.
- **🔍 Сканер**: Печать по заводскому SN.
- **📋 Инвентарка**: Чек-лист и отчет в CSV.
- **✍️ Текст**: Печать произвольного текста.

---

**Разработчик**: [Andrei Trokol](https://github.com/schatten08)
