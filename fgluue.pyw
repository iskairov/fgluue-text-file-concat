"""
FGlue v3.0: простое GUI-приложение для объединения файлов по шаблонам.
by @iskairov
"""

import hashlib
import os
import sys
import re
import tkinter as tk
from dataclasses import dataclass, field
from datetime import datetime
from tkinter import ttk, filedialog, messagebox
from typing import Dict, List, Any, Callable, Set


@dataclass
class AppConfig:
    """
    Класс конфигурации приложения.
    Содержит глобальные настройки, такие как лимит размера файла и кодировки для чтения.
    """

    version = 3.0
    max_file_size_mb: float = 10.0
    fallback_encodings: List[str] = field(default_factory=lambda: ["utf-8", "cp1251", "cp866", "latin-1"])
    templates_dir: str = "templates"

    @property
    def max_file_size_bytes(self) -> int:
        """
        Возвращает максимальный размер файла в байтах.

        :return: Лимит размера в байтах (int).
        """

        return int(self.max_file_size_mb * 1024 * 1024)


class FileContext:
    """
    Класс для работы с файлами: собирает метаданные файла, ведет счетчики
    и предоставляет методы форматирования текста (подстановки плейсхолдеров).
    """

    files_counter: int = 0
    current_files_count: int = 0
    current_lines_count: int = 0
    current_words_count: int = 0
    current_chars_count: int = 0

    total_files: int = 0
    total_lines: int = 0
    total_words: int = 0
    total_chars: int = 0

    def __init__(self, path: str, config: AppConfig) -> None:
        """
        Инициализация объекта FileContext.
        Считывает содержимое файла, проверяет лимиты размера и обновляет счетчики.

        :param path: Абсолютный путь к файлу.
        :param config: Экземпляр конфигурации приложения.

        :return: None
        """

        self.path: str = path
        self.config: AppConfig = config
        self.content: str = ""
        self.skip_file: bool = False

        try:
            file_size = os.path.getsize(path)
            if file_size > config.max_file_size_bytes:
                self.content = f"// Файл пропущен: превышен лимит размера ({config.max_file_size_mb} МБ)\n"
                self.skip_file = True
        except OSError:
            self.content = "// Ошибка доступа к файлу\n"
            self.skip_file = True

        if not self.skip_file:
            for enc in config.fallback_encodings:
                try:
                    with open(path, "r", encoding=enc) as f:
                        self.content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
                except Exception:
                    self.content = "// Ошибка чтения файла\n"
                    break

        self.lines: List[str] = self.content.splitlines()
        self.lines_count: int = len(self.lines)
        self.words_count: int = len(self.content.split())
        self.chars_count: int = len(self.content)

        FileContext.files_counter += 1
        FileContext.current_files_count += 1
        FileContext.current_lines_count += self.lines_count
        FileContext.current_words_count += self.words_count
        FileContext.current_chars_count += self.chars_count

    @staticmethod
    def reset_counters() -> None:
        """
        Сбрасывает все статические счетчики файлов, строк, слов и символов.

        :return: None
        """

        FileContext.files_counter = 0
        FileContext.current_files_count = 0
        FileContext.current_lines_count = 0
        FileContext.current_words_count = 0
        FileContext.current_chars_count = 0
        FileContext.total_files = 0
        FileContext.total_lines = 0
        FileContext.total_words = 0
        FileContext.total_chars = 0

    def _apply_content_modifier(self, template: str, pattern: str, func: Callable[['FileContext', ...], str], delete_line: bool = False) -> str:
        """
        Применяет модификатор (функцию) к содержимому текущего файла и удаляет плейсхолдер.

        :param template: Исходный текст шаблона.
        :param pattern: Имя плейсхолдера (например, 'upper').
        :param func: Функция-трансформатор, принимающая объект контекста.
        :param delete_line: Удалять ли строку целиком.

        :return: Измененный текст шаблона (str).
        """

        if delete_line:
            regex_line = r".*{" + pattern + r"(?:\:[^}]*)?}.*\n?"
            return re.sub(regex_line, "", template)
        else:
            regex = r"{(" + pattern + r")(?:\:([^}]+))?}"

            def repl(match: re.Match) -> str:
                args = match.group(2).split(";") if match.group(2) else []
                self.content = func(self, *args)
                return ""

            return re.sub(regex, repl, template)

    @staticmethod
    def find_placeholders(template: str) -> List[Dict[str, Any]]:
        """
        Находит все плейсхолдеры в шаблоне и возвращает информацию о них.

        :param template: Текст шаблона для парсинга.

        :return: Список словарей с данными плейсхолдеров (List[Dict]).
        """

        regex = r"{([a-zA-Z0-9_]+)(?:\:([^}]+))?}"
        placeholders: List[Dict[str, Any]] = []

        for match in re.finditer(regex, template):
            pattern = match.group(1)
            args = match.group(2).split(";") if match.group(2) else []
            placeholders.append({
                "full": match.group(0),
                "pattern": pattern,
                "args": args
            })

        return placeholders

    @staticmethod
    def _apply_placeholder(template: str, pattern: str, func: Callable[..., str], delete_line: bool = False) -> str:
        """
        Заменяет плейсхолдер в шаблоне на результат выполнения функции `func`.

        :param template: Исходный текст шаблона.
        :param pattern: Имя плейсхолдера.
        :param func: Функция, возвращающая строку для подстановки.
        :param delete_line: Удалять ли строку целиком.

        :return: Шаблон с подставленными значениями (str).
        """

        if delete_line:
            regex_line = r".*{" + pattern + r"(?:\:[^}]*)?}.*\n?"
            return re.sub(regex_line, "", template)
        else:
            regex = r"{(" + pattern + r")(?:\:([^}]+))?}"

            def repl(match: re.Match) -> str:
                args = match.group(2).split(";") if match.group(2) else []

                return str(func(*args))

            return re.sub(regex, repl, template)

    def format(self, template: str) -> str:
        """
        Основной метод форматирования. Заменяет все плейсхолдеры в шаблоне.

        :param template: Текст шаблона.

        :return: Отформатированный текст для конкретного файла (str).
        """

        result = template

        result = self._apply_placeholder(result, "name", lambda *args: os.path.splitext(os.path.basename(self.path))[0])
        result = self._apply_placeholder(result, "extension", lambda *args: os.path.splitext(os.path.basename(self.path))[1].lstrip("."))
        result = self._apply_placeholder(result, "filename", lambda *args: os.path.basename(self.path))
        result = self._apply_placeholder(result, "path", lambda *args: os.path.normpath(self.path).replace("/", "\\"))
        result = self._apply_placeholder(result, "folder", lambda *args: os.path.normpath(os.path.dirname(self.path)).replace("/", "\\"))
        result = self._apply_placeholder(result, "drive", lambda *args: os.path.splitdrive(self.path)[0])
        result = self._apply_placeholder(result, "size", lambda *args: self._human_size(os.path.getsize(self.path) if not self.skip_file else 0))

        result = self._apply_placeholder(result, "hash:md5", lambda *args: hashlib.md5(open(self.path, "rb").read()).hexdigest() if not self.skip_file else "N/A")
        result = self._apply_placeholder(result, "hash:sha1", lambda *args: hashlib.sha1(open(self.path, "rb").read()).hexdigest() if not self.skip_file else "N/A")

        result = self._apply_placeholder(result, "created", lambda fmt="%Y-%m-%d %H:%M:%S": datetime.fromtimestamp(os.stat(self.path).st_ctime).strftime(fmt) if not self.skip_file else "")
        result = self._apply_placeholder(result, "modified", lambda fmt="%Y-%m-%d %H:%M:%S": datetime.fromtimestamp(os.stat(self.path).st_mtime).strftime(fmt) if not self.skip_file else "")
        result = self._apply_placeholder(result, "accessed", lambda fmt="%Y-%m-%d %H:%M:%S": datetime.fromtimestamp(os.stat(self.path).st_atime).strftime(fmt) if not self.skip_file else "")

        result = self._apply_placeholder(result, '_', lambda *args: " ")
        result = self._apply_placeholder(result, 'nl', lambda *args: "\n")
        result = self._apply_placeholder(result, 'x', lambda *args: "", delete_line=True)

        result = self._apply_content_modifier(result, "upper", lambda ctx, *args: ctx.content.upper())
        result = self._apply_content_modifier(result, "lower", lambda ctx, *args: ctx.content.lower())
        result = self._apply_content_modifier(result, "title", lambda ctx, *args: ctx.content.title())
        result = self._apply_content_modifier(result, "remove_linebreaks", lambda ctx, *args: ctx.content.replace("\n", ""))
        result = self._apply_content_modifier(result, "remove_blank_lines", lambda ctx, *args: "\n".join(line for line in ctx.content.splitlines() if line.strip()))
        result = self._apply_content_modifier(result, "remove_whitespaces", lambda ctx, *args: " ".join(ctx.content.split()))
        result = self._apply_content_modifier(result, "remove_spaces", lambda ctx, *args: ctx.content.replace(" ", ""))
        result = self._apply_content_modifier(result, "indent", lambda ctx, spaces="4", *args: "\n".join((" " * int(spaces)) + line if line else line for line in ctx.content.splitlines()))
        result = self._apply_content_modifier(result, "sort_lines", lambda ctx, *args: "\n".join(sorted(ctx.content.splitlines())))
        result = self._apply_content_modifier(result, "unique_lines", lambda ctx, *args: "\n".join(list(dict.fromkeys(ctx.content.splitlines()))))
        result = self._apply_content_modifier(result, "strip_lines", lambda ctx, *args: "\n".join(line.strip() for line in ctx.content.splitlines()))
        result = self._apply_content_modifier(result, "prefix_lines", lambda ctx, prefix="", *args: "\n".join((prefix + line) for line in ctx.content.splitlines()))
        result = self._apply_content_modifier(result, "suffix_lines", lambda ctx, suffix="", *args: "\n".join((line + suffix) for line in ctx.content.splitlines()))
        result = self._apply_content_modifier(result, "replace", lambda ctx, old="", new="", *args: (ctx.content.replace(old, new) if old else ctx.content))
        result = self._apply_content_modifier(result, "grep", lambda ctx, pattern="", *args: ("\n".join(line for line in ctx.content.splitlines() if re.search(pattern, line)) if pattern else ctx.content))
        result = self._apply_content_modifier(result, "grep_v", lambda ctx, pattern="", *args: ("\n".join(line for line in ctx.content.splitlines() if not re.search(pattern, line)) if pattern else ctx.content))
        result = self._apply_content_modifier(result, "regex_replace", lambda ctx, pattern="", repl="", *args: (re.sub(pattern, repl, ctx.content) if pattern else ctx.content))

        result = self._apply_placeholder(result, "content:numbered", lambda *args: "\n".join(f"{i + 1}: {line}" for i, line in enumerate(self.lines)))
        result = self._apply_placeholder(result, "content", lambda *args: self.content)

        result = self._apply_placeholder(result, "line", lambda n="1": self.lines[int(n) - 1] if n.isdigit() and 0 < int(n) <= len(self.lines) else "")
        result = self._apply_placeholder(result, "lines", lambda start="1", end="1", *args: ("\n".join(self.lines[int(start) - 1:int(end)]) if start.isdigit() and end.isdigit() else ""))
        result = self._apply_placeholder(result, "head", lambda n="1": "\n".join(self.lines[:int(n)]) if n.isdigit() else "")
        result = self._apply_placeholder(result, "tail", lambda n="1": "\n".join(self.lines[-int(n):]) if n.isdigit() else "")

        result = self._apply_placeholder(result, "char", lambda n="1": self.content[int(n) - 1] if n.isdigit() and 0 < int(n) <= len(self.content) else "")
        result = self._apply_placeholder(result, "chars", lambda start="1", end="1", *args: (self.content[int(start) - 1:int(end)] if start.isdigit() and end.isdigit() else ""))
        result = self._apply_placeholder(result, "headchars", lambda n="1": self.content[:int(n)] if n.isdigit() else "")
        result = self._apply_placeholder(result, "tailchars", lambda n="1": self.content[-int(n):] if n.isdigit() else "")

        result = self._apply_placeholder(result, "lines_count", lambda *args: str(self.lines_count))
        result = self._apply_placeholder(result, "words_count", lambda *args: str(self.words_count))
        result = self._apply_placeholder(result, "chars_count", lambda *args: str(self.chars_count))

        result = self._apply_placeholder(result, "counter", lambda *args: str(self.files_counter))
        result = self._apply_placeholder(result, "current_files_count", lambda *args: str(self.current_files_count))
        result = self._apply_placeholder(result, "current_lines_count", lambda *args: str(self.current_lines_count))
        result = self._apply_placeholder(result, "current_words_count", lambda *args: str(self.current_words_count))
        result = self._apply_placeholder(result, "current_chars_count", lambda *args: str(self.current_chars_count))

        result = self._apply_placeholder(result, "total_files_count", lambda *args: str(self.total_files))
        result = self._apply_placeholder(result, "total_lines_count", lambda *args: str(self.total_lines))
        result = self._apply_placeholder(result, "total_words_count", lambda *args: str(self.total_words))
        result = self._apply_placeholder(result, "total_chars_count", lambda *args: str(self.total_chars))

        return result

    @staticmethod
    def _human_size(size: int) -> str:
        """
        Переводит байты в читаемый формат (КБ, МБ).

        :param size: Размер в байтах.

        :return: Строка с читаемым размером (str).
        """

        for unit in ["Б", "КБ", "МБ", "ГБ", "ТБ"]:
            if size < 1024:
                return f"{size} {unit}" if unit == "Б" else f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} ПБ"


class FGlueApp:
    """ Главный класс GUI-приложения. Управляет интерфейсом и бизнес-логикой. """

    def __init__(self, root: tk.Tk, folder_path: str, config: AppConfig) -> None:
        """
        Инициализирует приложение.

        :param root: Основное окно Tkinter.
        :param folder_path: Стартовая папка для сканирования.
        :param config: Объект настроек.

        :return: None
        """

        self.root: tk.Tk = root
        self.config: AppConfig = config
        self.root.title(f"FGlue v{config.version}")
        self.root.minsize(720, 520)

        self.folder_path: str = folder_path
        self.check_vars: Dict[str, tk.BooleanVar] = {}
        self.path_to_item: Dict[str, str] = {}
        self.templates: Dict[str, str] = {}
        self.selected_template: tk.StringVar = tk.StringVar()

        self.status_var: tk.StringVar = tk.StringVar(value="")

        self.excluded_exts: Set[str] = set()
        self.excluded_exts_var: tk.StringVar = tk.StringVar(value="")

        self.included_exts: Set[str] = set()
        self.included_exts_var: tk.StringVar = tk.StringVar(value="")

        self._create_ui()
        self._load_files(self.folder_path)
        self._load_templates()
        self._update_status()

        self.root.update_idletasks()
        self._center_window(self.root)

    def _create_ui(self) -> None:
        """
        Создает и размещает все элементы пользовательского интерфейса.

        :return: None
        """

        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill="both", expand=True)

        # --- Верхняя панель: Управление деревом и выделением ---
        top_btn_frame = ttk.Frame(frame)
        top_btn_frame.pack(fill="x", pady=(0, 5))

        # Кнопки раскрытия/сворачивания дерева
        ttk.Button(top_btn_frame, text="Раскрыть все", command=self.expand_all).pack(side="left", padx=(0, 5))
        ttk.Button(top_btn_frame, text="Свернуть все", command=self.collapse_all).pack(side="left", padx=(0, 5))

        # Вертикальный разделитель
        ttk.Separator(top_btn_frame, orient="vertical").pack(side="left", fill="y", padx=5)

        # Кнопки выделения файлов
        ttk.Button(top_btn_frame, text="Выбрать все", command=lambda: self._set_all(True)).pack(side="left",
                                                                                                padx=(5, 5))
        ttk.Button(top_btn_frame, text="Снять все", command=lambda: self._set_all(False)).pack(side="left", padx=(0, 5))

        # --- Дерево файлов ---
        self.tree = ttk.Treeview(frame, columns=("path",), show="tree", selectmode="browse")
        self.tree.pack(fill="both", expand=True, pady=5)

        yscroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        yscroll.pack(side="right", fill="y")

        # Контекстное меню
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Открыть файл", command=self.open_file_selected)
        self.menu.add_command(label="Открыть папку", command=self.open_folder_selected)
        self.menu.add_command(label="Обновить", command=self.refresh_files)
        self.tree.bind("<Button-3>", self._show_context_menu)

        # --- Фильтры ---
        # Фильтр: Исключить расширения
        ex_frame = ttk.Frame(frame)
        ex_frame.pack(fill="x", pady=(6, 6))
        ttk.Label(ex_frame, text="Исключить расширения (через запятую):").pack(side="left")
        ttk.Entry(ex_frame, textvariable=self.excluded_exts_var).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(ex_frame, text="Применить", command=self.apply_excluded_exts).pack(side="left")
        ttk.Button(ex_frame, text="Сброс", command=self.reset_excluded_exts).pack(side="left", padx=(6, 0))

        # Фильтр: Включить расширения
        inc_frame = ttk.Frame(frame)
        inc_frame.pack(fill="x", pady=(0, 6))
        ttk.Label(inc_frame, text="Только эти расширения (через запятую):").pack(side="left")
        ttk.Entry(inc_frame, textvariable=self.included_exts_var).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(inc_frame, text="Применить", command=self.apply_included_exts).pack(side="left")
        ttk.Button(inc_frame, text="Сброс", command=self.reset_included_exts).pack(side="left", padx=(6, 0))

        # --- Шаблоны ---
        ttk.Label(frame, text="Шаблон объединения:").pack(anchor="w", pady=(10, 0))
        self.template_combo = ttk.Combobox(frame, textvariable=self.selected_template, state="readonly")
        self.template_combo.pack(fill="x", pady=5)

        # --- Нижняя панель действий ---
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=5)

        ttk.Button(btn_frame, text="ОБЪЕДИНИТЬ", command=self.merge_files).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Очередь файлов", command=self.show_queue_window).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Обновить", command=self.refresh_files).pack(side="right")
        ttk.Button(btn_frame, text="Выбрать папку", command=self.choose_folder).pack(side="right")

        # --- Строка статуса ---
        ttk.Label(frame, textvariable=self.status_var, anchor="w").pack(fill="x", pady=(4, 0))

        # --- Бинды и теги ---
        self.root.bind_all("<Control-a>", lambda e: self._on_select_all())
        self.root.bind_all("<Control-d>", lambda e: self._on_deselect_all())
        self.root.bind_all("<F5>", lambda e: self.refresh_files())
        self.tree.bind("<Button-1>", self._on_tree_click, add="+")

        self.tree.tag_configure("excluded_ext", foreground="gray")
        self.tree.tag_configure("not_included_ext", foreground="gray")

    @staticmethod
    def _center_window(win: tk.Tk | tk.Toplevel) -> None:
        """
        Центрирует переданное окно по центру экрана.

        :param win: Окно Tkinter, которое необходимо отцентрировать.

        :return: None
        """

        try:
            win.update_idletasks()
            width, height = win.winfo_width(), win.winfo_height()
            screen_w, screen_h = win.winfo_screenwidth(), win.winfo_screenheight()
            win.geometry(f"{width}x{height}+{(screen_w - width) // 2}+{(screen_h - height) // 2}")
        except Exception:
            pass

    @staticmethod
    def _checkbox_prefix(checked: bool) -> str:
        """
        Возвращает юникод-символ для имитации чекбокса в дереве файлов.

        :param checked: Состояние чекбокса.

        :return: Строка с символом (str).
        """

        return "☑ " if checked else "☐ "

    @staticmethod
    def _normalize_exts(raw: str) -> Set[str]:
        """
        Приводит строку с расширениями к нормализованному множеству (напр., {'.txt', '.log'}).

        :param raw: Строка, введенная пользователем.

        :return: Множество расширений (Set[str]).
        """

        return {("." + p if not p.startswith(".") else p) for p in [x.strip().lower() for x in raw.split(",")] if p}

    def _is_filtered_out(self, path: str) -> bool:
        """
        Проверяет, исключен ли файл текущими фильтрами расширений.

        :param path: Путь к файлу.

        :return: True, если файл должен быть скрыт/отключен, иначе False.
        """

        ext = os.path.splitext(path)[1].lower()
        if ext in self.excluded_exts:
            return True
        if self.included_exts and (ext not in self.included_exts):
            return True
        return False

    def apply_excluded_exts(self) -> None:
        """
        Парсит поле исключенных расширений и применяет фильтр к дереву.

        :return: None
        """
        self.excluded_exts = self._normalize_exts(self.excluded_exts_var.get())
        self.apply_extension_filters()

    def apply_included_exts(self) -> None:
        """
        Парсит поле разрешенных расширений и применяет фильтр к дереву.

        :return: None
        """

        self.included_exts = self._normalize_exts(self.included_exts_var.get())
        self.apply_extension_filters()

    def apply_extension_filters(self) -> None:
        """
        Применяет активные фильтры к дереву: снимает галочки с неподходящих файлов
        и применяет серый цвет текста (теги).

        :return: None
        """

        for path, var in self.check_vars.items():
            item_id = self.path_to_item.get(path)
            if not item_id:
                continue
            if os.path.isdir(path):
                self._refresh_item_label(item_id, path)
                self.tree.item(item_id, tags=())
            else:
                if self._is_filtered_out(path):
                    var.set(False)
                    self._refresh_item_label(item_id, path)
                    ext = os.path.splitext(path)[1].lower()
                    if ext in self.excluded_exts:
                        self.tree.item(item_id, tags=("excluded_ext",))
                    else:
                        self.tree.item(item_id, tags=("not_included_ext",))
                else:
                    self.tree.item(item_id, tags=())
        self._update_status()

    def reset_excluded_exts(self) -> None:
        """
        Очищает список исключенных расширений и обновляет фильтры.

        :return: None
        """

        self.excluded_exts.clear()
        self.excluded_exts_var.set("")
        self.apply_extension_filters()

    def reset_included_exts(self) -> None:
        """
        Очищает белый список расширений и обновляет фильтры.

        :return: None
        """

        self.included_exts.clear()
        self.included_exts_var.set("")
        self.apply_extension_filters()

    def _on_tree_click(self, event: tk.Event) -> None:
        """
        Обработчик клика мыши по элементу дерева (эмуляция чекбоксов).

        :param event: Событие мыши от Tkinter.

        :return: None
        """

        item_id = self.tree.identify_row(event.y)
        if not item_id or self.tree.identify_element(event.x, event.y) in ("Treeitem.indicator", "Treeitem.image"):
            return

        abspath = self.tree.item(item_id, "values")[0]
        if os.path.isfile(abspath) and self._is_filtered_out(abspath):
            return

        var = self.check_vars.get(abspath)
        if var is None:
            return

        new_state = not var.get()
        if os.path.isdir(abspath):
            self._set_state_recursive(item_id, new_state)
        else:
            self._set_item_state(item_id, abspath, new_state)
        self._update_status()

    def _refresh_item_label(self, item_id: str, abspath: str) -> None:
        """
        Обновляет текст узла (меняет символ чекбокса в зависимости от состояния).

        :param item_id: ID элемента в Treeview.
        :param abspath: Абсолютный путь к файлу/папке.

        :return: None
        """

        checked = self.check_vars.get(abspath, tk.BooleanVar(value=True)).get()
        self.tree.item(item_id, text=self._checkbox_prefix(checked) + os.path.basename(abspath))

    def _set_item_state(self, item_id: str, abspath: str, state: bool) -> None:
        """
        Устанавливает логическое состояние переменной чекбокса и обновляет метку.

        :param item_id: ID элемента в Treeview.
        :param abspath: Абсолютный путь.
        :param state: Новое состояние (True/False).

        :return: None
        """

        if var := self.check_vars.get(abspath):
            var.set(state)
        self._refresh_item_label(item_id, abspath)

    def _set_state_recursive(self, item_id: str, state: bool) -> None:
        """
        Рекурсивно меняет состояние чекбоксов для папки и всех ее вложений.

        :param item_id: ID папки в Treeview.
        :param state: Новое состояние (True/False).

        :return: None
        """

        abspath = self.tree.item(item_id, "values")[0]
        if os.path.isfile(abspath) and self._is_filtered_out(abspath):
            return
        self._set_item_state(item_id, abspath, state)
        for child in self.tree.get_children(item_id):
            self._set_state_recursive(child, state)

    def _set_all(self, state: bool) -> None:
        """
        Включает или отключает все доступные чекбоксы в дереве файлов.

        :param state: True - выбрать все, False - снять со всех.

        :return: None
        """

        for path, var in self.check_vars.items():
            if os.path.isfile(path) and self._is_filtered_out(path):
                var.set(False)
            else:
                var.set(state)
            if item_id := self.path_to_item.get(path):
                self._refresh_item_label(item_id, path)
        self._update_status()

    def expand_all(self) -> None:
        """
        Рекурсивно разворачивает все узлы файлового дерева.

        :return: None
        """

        def recurse(node: str) -> None:
            """ Внутренняя функция для рекурсивного раскрытия веток. """

            self.tree.item(node, open=True)
            for child in self.tree.get_children(node):
                recurse(child)

        for top_node in self.tree.get_children(""):
            recurse(top_node)

    def collapse_all(self) -> None:
        """
        Рекурсивно сворачивает все узлы файлового дерева.

        :return: None
        """

        def recurse(node: str) -> None:
            """ Внутренняя функция для рекурсивного закрытия веток. """
            self.tree.item(node, open=False)
            for child in self.tree.get_children(node):
                recurse(child)

        for top_node in self.tree.get_children(""):
            recurse(top_node)

    def _on_select_all(self) -> None:
        """
        Обработчик горячей клавиши Ctrl+A. Выделяет все файлы.

        :return: None
        """

        self._set_all(True)

    def _on_deselect_all(self) -> None:
        """
        Обработчик горячей клавиши Ctrl+D. Снимает выделение со всех файлов.

        :return: None
        """

        self._set_all(False)

    def _show_context_menu(self, event: tk.Event) -> None:
        """
        Отображает контекстное меню при клике ПКМ по элементу дерева.

        :param event: Событие мыши.

        :return: None
        """

        if item_id := self.tree.identify_row(event.y):
            self.tree.selection_set(item_id)
            self.menu.tk_popup(event.x_root, event.y_root)

    def open_file_selected(self) -> None:
        """
        Открывает выбранный в дереве файл стандартными средствами ОС.

        :return: None
        """

        if sel := self.tree.selection():
            self._open_in_os(self.tree.item(sel[0], "values")[0])

    def open_folder_selected(self) -> None:
        """
        Открывает родительскую папку выбранного файла стандартными средствами ОС.

        :return: None
        """

        if sel := self.tree.selection():
            abspath = self.tree.item(sel[0], "values")[0]
            self._open_in_os(abspath if os.path.isdir(abspath) else os.path.dirname(abspath))

    @staticmethod
    def _open_in_os(path: str) -> None:
        """
        Выполняет системную команду открытия пути для текущей ОС (Windows).

        :param path: Путь к файлу или папке.

        :return: None
        """

        try:
            os.startfile(path)
        except Exception as exc:
            messagebox.showerror("Ошибка", f"Не удалось открыть: {path}\n{exc}")

    def _load_files(self, path: str) -> None:
        """
        Очищает дерево и рекурсивно сканирует указанную папку для заполнения списка.

        :param path: Абсолютный путь к стартовой директории.

        :return: None
        """

        self.tree.delete(*self.tree.get_children())
        self.check_vars.clear()
        self.path_to_item.clear()

        def insert_node(parent: str, abspath: str) -> None:
            """ Вставляет узел в дерево и сканирует дочерние элементы. """

            self.check_vars[abspath] = tk.BooleanVar(value=True)
            node = self.tree.insert(parent, "end", text=self._checkbox_prefix(True) + os.path.basename(abspath), open=(parent == ""), values=(abspath,))
            self.path_to_item[abspath] = node

            if os.path.isdir(abspath):
                try:
                    for item in sorted(os.listdir(abspath)):
                        insert_node(node, os.path.join(abspath, item))
                except PermissionError:
                    pass

        if os.path.exists(path):
            insert_node("", path)
            self.apply_extension_filters() if self.excluded_exts or self.included_exts else self._update_status()

    def get_selected_files(self) -> List[str]:
        """
        Собирает все пути к файлам, которые отмечены чекбоксами и не исключены фильтрами.

        :return: Список абсолютных путей файлов (List[str]).
        """

        selected: List[str] = []

        def walk(node: str) -> None:
            """ Внутренняя функция для обхода дерева. """

            for child in self.tree.get_children(node):
                abspath = self.tree.item(child, "values")[0]
                if os.path.isdir(abspath):
                    walk(child)
                elif not self._is_filtered_out(abspath) and self.check_vars.get(abspath, tk.BooleanVar(value=False)).get():
                    selected.append(abspath)

        walk("")

        return selected

    def _update_status(self) -> None:
        """
        Обновляет текстовую метку внизу окна (количество выбранных файлов / всего).

        :return: None
        """

        total = sum(1 for p in self.check_vars if os.path.isfile(p))
        self.status_var.set(f"Выбрано файлов: {len(self.get_selected_files())} / {total}")

    def _load_templates(self) -> None:
        """
        Проверяет наличие папки с шаблонами, создает базовые шаблоны, если папка пуста,
        и загружает их в словарь `self.templates`.

        :return: None
        """

        os.makedirs(self.config.templates_dir, exist_ok=True)

        if not os.listdir(self.config.templates_dir):
            default_templates = {
                "1. Содержимое с шапкой": "----- {filename} -----{nl}{content}{nl}",
                "2. Cодержимое с шапкой и нумерацией": "----- {counter}. {filename} -----{nl}{content:numbered}{nl}",
                "3. Только содержимое": "{content}{nl}",
                "4. Объединение программного кода": "{allow_ext:py;js;ts;php;html;css;java;cpp;c;cs;rb;go;rs;swift;kt;bat;sh;sql;json;xml}{x}\n----- {filename} ({path}) -----\n{remove_blank_lines}{content}{nl}{nl}",
                "5. Структура папок": "{if_folder_changed}{folder}{nl}"
            }

            for name, content in default_templates.items():
                with open(os.path.join(self.config.templates_dir, f"{name}.txt"), "w", encoding="utf-8") as f:
                    f.write(content)

        self.templates.clear()
        for fname in os.listdir(self.config.templates_dir):
            fpath = os.path.join(self.config.templates_dir, fname)
            if os.path.isfile(fpath):
                name = os.path.splitext(fname)[0]
                while name in self.templates: name += "_"
                with open(fpath, "r", encoding="utf-8") as f:
                    self.templates[name] = f.read()

        self.template_combo["values"] = list(self.templates.keys())
        if self.templates:
            self.template_combo.current(0)

    def choose_folder(self) -> None:
        """
        Открывает диалог выбора рабочей папки и загружает из нее файлы.

        :return: None
        """

        if new_path := filedialog.askdirectory():
            self.folder_path = new_path
            self._load_files(new_path)

    def refresh_files(self) -> None:
        """
        Повторно сканирует текущую папку, обновляя файловое дерево.

        :return: None
        """

        if self.folder_path:
            self._load_files(self.folder_path)

    def merge_files(self) -> None:
        """
        Основной метод объединения: считывает выбранные файлы,
        подставляет их в выбранный шаблон и выводит в окно предпросмотра.

        :return: None
        """

        template_name = self.selected_template.get()
        if not template_name:
            messagebox.showwarning("Внимание", "Выберите шаблон!")
            return

        template = self.templates[template_name]
        selected_files = self.get_selected_files()

        if not selected_files:
            messagebox.showinfo("Информация", "Нет файлов для объединения.")
            return

        FileContext.reset_counters()
        placeholders = FileContext.find_placeholders(template)

        # --- 1. Препроцессинг: skip_ext (Собираем ВСЕ исключения в одно множество) ---
        skip_ext_phs = [p for p in placeholders if p["pattern"] == "skip_ext"]
        if skip_ext_phs:
            global_skip_set: Set[str] = set()
            for ph in skip_ext_phs:
                global_skip_set.update(
                    ("." + arg if not arg.startswith(".") else arg).lower()
                    for arg in ph["args"] if arg.strip()
                )
                template = template.replace(ph["full"], "")

            selected_files = [f for f in selected_files if os.path.splitext(f)[1].lower() not in global_skip_set]

        # --- 2. Препроцессинг: allow_ext (Собираем ВСЕ разрешения в одно множество) ---
        allow_ext_phs = [p for p in placeholders if p["pattern"] == "allow_ext"]
        if allow_ext_phs:
            global_allow_set: Set[str] = set()
            for ph in allow_ext_phs:
                global_allow_set.update(
                    ("." + arg if not arg.startswith(".") else arg).lower()
                    for arg in ph["args"] if arg.strip()
                )
                template = template.replace(ph["full"], "")

            selected_files = [f for f in selected_files if os.path.splitext(f)[1].lower() in global_allow_set]

        # --- 3. Препроцессинг: limit_files ---
        if limit_ph := next((p for p in placeholders if p["pattern"] == "limit_files"), None):
            if limit_ph["args"] and limit_ph["args"][0].isdigit():
                selected_files = selected_files[:int(limit_ph["args"][0])]
            template = template.replace(limit_ph["full"], "")

        # Если после фильтрации не осталось файлов
        if not selected_files:
            messagebox.showinfo("Информация", "После применения фильтров шаблона (allow_ext/skip_ext) файлов не осталось.")
            return

        # Подсчет тоталов
        FileContext.total_files = len(selected_files)
        for p in selected_files:
            ctx = FileContext(p, self.config)
            FileContext.total_lines += ctx.lines_count
            FileContext.total_words += ctx.words_count
            FileContext.total_chars += ctx.chars_count

        # Обнуляем счетчики
        FileContext.files_counter = 0
        FileContext.current_files_count = 0
        FileContext.current_lines_count = 0
        FileContext.current_words_count = 0
        FileContext.current_chars_count = 0

        result = ""
        last_folder = None

        # --- 4. Формирование результата ---
        for i, path in enumerate(selected_files):
            ctx = FileContext(path, self.config)
            temp_template = template

            if i > 0:
                temp_template = re.sub(r".*\{show_before}.*\n?", "", temp_template, flags=re.IGNORECASE)
            else:
                temp_template = temp_template.replace("{show_before}", "")

            if i < len(selected_files) - 1:
                temp_template = re.sub(r".*\{show_after}.*\n?", "", temp_template, flags=re.IGNORECASE)
            else:
                temp_template = temp_template.replace("{show_after}", "")

            folder = os.path.dirname(path)
            if last_folder is not None and folder != last_folder:
                temp_template = temp_template.replace("{if_folder_changed}", "")
            else:
                temp_template = re.sub(r".*\{if_folder_changed}.*\n?", "", temp_template)

            last_folder = folder
            result += ctx.format(temp_template)

        self._show_preview(result)

    def _show_preview(self, result: str) -> None:
        """
        Открывает новое окно поверх основного с результатом объединения файлов.

        :param result: Готовый текст после обработки шаблона.

        :return: None
        """

        preview = tk.Toplevel(self.root)
        preview.title("Результат объединения")
        preview.minsize(800, 600)

        toolbar = ttk.Frame(preview)
        toolbar.pack(fill="x", padx=5, pady=5)

        ttk.Button(toolbar, text="Скопировать", command=lambda: self.copy_to_clipboard(result)).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Сохранить", command=lambda: self.save_result(result)).pack(side="left", padx=2)
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=10)

        ttk.Label(toolbar, text="Шрифт:").pack(side="left", padx=(0, 2))
        font_size = tk.IntVar(value=10)
        font_combo = ttk.Combobox(toolbar, textvariable=font_size, values=[8, 10, 12, 14, 16], width=5, state="readonly")
        font_combo.pack(side="left", padx=2)

        text_frame = ttk.Frame(preview)
        text_frame.pack(fill="both", expand=True, padx=5, pady=5)

        yscroll = ttk.Scrollbar(text_frame, orient="vertical")
        yscroll.pack(side="right", fill="y")
        xscroll = ttk.Scrollbar(text_frame, orient="horizontal")
        xscroll.pack(side="bottom", fill="x")

        text = tk.Text(text_frame, wrap="none", yscrollcommand=yscroll.set, xscrollcommand=xscroll.set, font=("Consolas", 10))
        text.insert("1.0", result)
        text.pack(side="left", fill="both", expand=True)
        text.config(state="disabled")

        yscroll.config(command=text.yview)
        xscroll.config(command=text.xview)

        font_combo.bind("<<ComboboxSelected>>", lambda e: text.config(font=("Consolas", font_size.get())))

        stats = f"Строк: {len(result.splitlines())} | Символов: {len(result)} | Слов: {len(result.split())}"
        ttk.Label(preview, text=stats).pack(anchor="w", padx=5, pady=(0, 5))
        self._center_window(preview)

    def copy_to_clipboard(self, result: str) -> None:
        """
        Записывает переданный текст в буфер обмена ОС.

        :param result: Текст для копирования.

        :return: None
        """

        self.root.clipboard_clear()
        self.root.clipboard_append(result)
        messagebox.showinfo("Готово", "Текст скопирован в буфер обмена!")

    @staticmethod
    def save_result(result: str) -> None:
        """
        Вызывает диалог сохранения и записывает переданный текст в .txt файл.

        :param result: Текст для сохранения.

        :return: None
        """

        if save_path := filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")]):
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(result)
            messagebox.showinfo("Успех", f"Файл сохранен:\n{save_path}")

    def show_queue_window(self) -> None:
        """
        Отображает вспомогательное окно со списком файлов в очереди на объединение.

        :return: None
        """

        queue_win = tk.Toplevel(self.root)
        queue_win.title("Очередь файлов")
        queue_win.geometry("500x400")

        list_frame = ttk.Frame(queue_win)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        scroll = ttk.Scrollbar(list_frame)
        scroll.pack(side="right", fill="y")

        lb = tk.Listbox(list_frame, yscrollcommand=scroll.set)
        lb.pack(side="left", fill="both", expand=True)
        scroll.config(command=lb.yview)

        for f in self.get_selected_files():
            lb.insert("end", f)

        self._center_window(queue_win)


if __name__ == "__main__":
    folder_to_open = sys.argv[1] if len(sys.argv) > 1 else filedialog.askdirectory(title="Выберите папку")

    if folder_to_open:
        main_root = tk.Tk()
        app_config = AppConfig()
        app = FGlueApp(main_root, folder_to_open, app_config)
        main_root.mainloop()
        