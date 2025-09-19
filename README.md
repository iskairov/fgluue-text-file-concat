# 🔗 FGlue (EN)

A simple yet powerful GUI tool for **merging text files** using **flexible templates**.

---

## ✨ Features

- **Visual File Browser:** Convenient tree view for exploring and selecting files and folders.  
- **Powerful Templates:** Merge files using placeholders for metadata, content, and statistics.  
- **Live Preview:** Instantly see the merged result — copy or save it with one click.  
- **Flexible Filtering:**
  - **Blacklist:** Exclude files by extension directly in the GUI (e.g., `.log`, `.tmp`).
  - **Whitelist:** Include only specific extensions (e.g., `.txt`, `.md`).
- **Selection Management:** Select or deselect all files in one click or via hotkeys (`Ctrl+A`, `Ctrl+D`).
- **Context Menu:** Quickly open files, open folders, or refresh the list.

---

## ▶️ Launch

1. **From console:**
   ```bash
   python fglue.py "C:\path\to\your\folder"
   ```

2. **Without arguments:**
   If no path is specified, the program will open a folder selection dialog.

## 📝 Templates

Templates are plain text files stored in the `templates/` folder. 
They define how your files will be merged. On the first run, 
FGlue automatically creates a few useful example templates.

**Example template:**

```text
----- {filename} -----{nl}{content}{nl}
```

Here `{filename}`, `{nl}`, and `{content}` are placeholders that will be replaced with real data during processing.

## 🔍 Placeholders

All placeholders fall into three categories:
**Substitution**, **Modifiers**, and **Control** (**Filtering**) placeholders.

### 1. Substitution Placeholders

These placeholders insert file information or content.

#### File Info
- `{name}` — file name without extension  
- `{extension}` — file extension (e.g., `txt`)  
- `{filename}` — full file name (e.g., `notes.txt`)  
- `{path}` — absolute file path  
- `{folder}` — parent folder name  
- `{drive}` — drive letter (Windows, e.g., `C:`)  
- `{size}` — human-readable file size  
- `{hash:md5}`, `{hash:sha1}` — MD5 or SHA1 hash of file content  
- `{created}`, `{modified}`, `{accessed}` — file creation, modification, and access dates  
  - Custom format supported: `{created:%d.%m.%Y %H:%M:%S}`

#### Content
- `{content}` — full file content  
- `{content:numbered}` — file content with numbered lines  
- `{line:N}` — the Nth line (1-based)  
- `{lines:START;END}` — lines from START to END  
- `{head:N}` — first N lines  
- `{tail:N}` — last N lines  
- `{char:N}`, `{chars:S;E}`, `{headchars:N}`, `{tailchars:N}` — same but for characters

#### Statistics and Counters
- `{lines_count}`, `{words_count}`, `{chars_count}` — counts for the **current file**  
- `{counter}` — sequential number of the processed file (starting at 1)  
- `{current_files_count}`, `{current_lines_count}`, etc. — cumulative counters for the current operation  
- `{total_files_count}`, `{total_lines_count}`, etc. — totals for all selected files

#### Special Symbols
- `{nl}` — newline  
- `{_}` — space

---

### 2. Content Modifiers

These placeholders modify the `{content}` before inserting it.  
Modifiers are applied **in sequence**.

- `{upper}` — convert text to UPPERCASE  
- `{lower}` — convert text to lowercase  
- `{title}` — Capitalize Each Word  
- `{remove_linebreaks}` — remove all line breaks (join lines)  
- `{remove_blank_lines}` — remove empty lines only  
- `{remove_whitespaces}` — replace multiple spaces and newlines with a single space  
- `{remove_spaces}` — remove all spaces

**Example:**
```text
{remove_linebreaks}{content}
```
This template removes all line breaks before inserting the file content.

---

### 3. Control Placeholders

These placeholders control the merge process — they filter files or affect output structure.  
They are processed **before** the file loop starts and removed from the final text.

#### File Filtering
- `{allow_ext:py;js;html}` — process only files with these extensions  
- `{skip_ext:log;tmp}` — skip files with these extensions  
- `{limit_files:10}` — process only the first 10 files

#### Output Control
- `{x}` — remove the entire line containing this placeholder (useful for comments or cleanup)  
- `{show_before}` — the line will be inserted **once**, before the first file’s result  
- `{show_after}` — the line will be inserted **once**, after the last file’s result

**Example:**

```text
{show_before}--- Report Start. Total files: {total_files_count} ---{nl}
File #{counter}: {filename}{nl}
{show_after}--- Report End ---
```

---

# 🔗 FGlue (RU)

Простое GUI-приложение для объединения текстовых файлов по гибким шаблонам.

## ✨ Возможности

- **Визуальный выбор файлов:** Удобное дерево для просмотра и выбора файлов и папок.
- **Мощные шаблоны:** Объединяйте файлы, используя плейсхолдеры для метаданных, содержимого и статистики.
- **Предпросмотр:** Мгновенный предпросмотр результата с возможностью копирования и сохранения.
- **Гибкая фильтрация:**
    - **Черный список:** Исключайте файлы по расширениям прямо в GUI (например, `.log, .tmp`).
    - **Белый список:** Оставляйте только нужные расширения (например, `.txt, .md`).
- **Управление выбором:** Выделяйте или снимайте выделение со всех файлов в один клик или горячими клавишами (`Ctrl+A`, `Ctrl+D`).
- **Контекстное меню:** Быстро открывайте файлы, папки или обновляйте список.

## ▶️ Запуск

1.  **Из консоли:**
    ```bash
    python fglue.py "C:\путь\к\вашей\папке"
    ```
2.  **Без аргументов:**
    Если путь не указан, программа откроет диалоговое окно для выбора папки.

## 📝 Шаблоны

Шаблоны — это обычные текстовые файлы, которые лежат в папке `templates/`. 
Они определяют, как именно будут объединены ваши файлы. 
При первом запуске FGlue автоматически создаст несколько полезных шаблонов.

**Пример шаблона (`1. Содержимой с шапкой.txt`):**

```text
----- {filename} -----{nl}{content}{nl}
```

Здесь `{filename}`, `{nl}` и `{content}` — это **плейсхолдеры**, которые программа заменяет реальными данными при обработке каждого файла.

## 🔍 Плейсхолдеры

Все плейсхолдеры можно разделить на три типа: 
**подстановочные**, **модификаторы** и **управляющие** (**фильтрующие**).

### 1. Подстановочные плейсхолдеры

Эти плейсхолдеры вставляют в текст информацию о файле или его содержимое.

#### Информация о файле
- `{name}` — имя файла без расширения.
- `{extension}` — расширение файла без точки (например, `txt`).
- `{filename}` — полное имя файла (например, `notes.txt`).
- `{path}` — абсолютный путь к файлу.
- `{folder}` — папка, в которой лежит файл.
- `{drive}` — диск (для Windows, например `C:`).
- `{size}` — размер файла в удобном формате (Б, КБ, МБ).
- `{hash:md5}`, `{hash:sha1}` — MD5 или SHA1 хэш содержимого файла.
- `{created}`, `{modified}`, `{accessed}` — дата создания, изменения и доступа.
    - Можно указать формат: `{created:%d.%m.%Y %H:%M:%S}`.

#### Содержимое
- `{content}` — полное содержимое файла.
- `{content:numbered}` — содержимое с пронумерованными строками.
- `{line:N}` — N-я строка файла (нумерация с 1).
- `{lines:START;END}` — строки с START по END.
- `{head:N}` — первые N строк файла.
- `{tail:N}` — последние N строк файла.
- `{char:N}`, `{chars:S;E}`, `{headchars:N}`, `{tailchars:N}` — то же самое, но для символов.

#### Статистика и счетчики
- `{lines_count}`, `{words_count}`, `{chars_count}` — количество строк, слов и символов в **текущем** файле.
- `{counter}` — порядковый номер обрабатываемого файла (начиная с 1).
- `{current_files_count}`, `{current_lines_count}` и т.д. — счетчики, нарастающие в процессе текущей операции.
- `{total_files_count}`, `{total_lines_count}` и т.д. — итоговые счетчики по всем **выбранным** для операции файлам.

#### Специальные символы
- `{nl}` — перенос строки.
- `{_}` — пробел.

### 2. Модификаторы содержимого

Эти плейсхолдеры не вставляют текст, а **изменяют содержимое** файла (`{content}`) перед его подстановкой. Они применяются последовательно.

- `{upper}` — преобразовать всё содержимое в ВЕРХНИЙ РЕГИСТР.
- `{lower}` — преобразовать всё содержимое в нижний регистр.
- `{title}` — Сделать Первые Буквы Слов Заглавными.
- `{remove_linebreaks}` — удалить все переносы строк, склеив текст в одну линию.
- `{remove_blank_lines}` — удалить только пустые строки.
- `{remove_whitespaces}` — заменить множественные пробелы и переносы на одиночные пробелы.
- `{remove_spaces}` — удалить все пробелы.

**Пример:** Этот шаблон сначала удалит все переносы строк, а затем вставит измененное содержимое.
```text
{remove_linebreaks}{content}
```

### 3. Управляющие плейсхолдеры

Эти плейсхолдеры управляют процессом объединения: фильтруют файлы или влияют на структуру вывода. Они обрабатываются **до** начала цикла по файлам и удаляются из шаблона.

#### Фильтрация файлов
- `{allow_ext:py;js;html}` — обработать только файлы с указанными расширениями.
- `{skip_ext:log;tmp}` — пропустить файлы с указанными расширениями.
- `{limit_files:10}` — обработать не более 10 первых файлов.

#### Управление выводом
- `{x}` — полностью удалить строку шаблона, в которой находится этот плейсхолдер. Удобно для комментариев или для удаления строк с фильтрами.
- `{show_before}` — текст в строке с этим плейсхолдером будет добавлен только **один раз**, перед результатом обработки первого файла.
- `{show_after}` — текст в строке с этим плейсхолдером будет добавлен только **один раз**, после результата обработки последнего файла.

**Пример использования `show_before` и `show_after`:**

```text
{show_before}--- Начало отчета. Всего файлов: {total_files_count} ---{nl}
Файл №{counter}: {filename}{nl}
{show_after}--- Конец отчета ---
```