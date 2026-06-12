import os
import glob
import math
import pandas as pd
from matplotlib.ticker import FormatStrFormatter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext


# ==============================================================================
# ЧАСТЬ 1: МАТЕМАТИКА И ОБРАБОТКА ДАННЫХ
# ==============================================================================
def analyze_inclinometer_data(d_displacement, p_cargo, l_distance, folder_path):
    # Поиск основных файлов замера (носовой пост)
    search_pattern = os.path.join(folder_path, "M_*_1.CSV")
    file_list_main = sorted(glob.glob(search_pattern))

    if not file_list_main:
        log_message("Внимание: В выбранной папке нет базовых файлов M_*_1.CSV!")
        messagebox.showwarning("Внимание", "В выбранной папке нет базовых файлов M_*_1.CSV!")
        return

    log_message(f"Найдено замеров: {len(file_list_main)}. Запуск обработки...")

    summary_results = []
    all_raw_rows = []
    h_meta_list = []

    # Очистка графиков перед новой отрисовкой
    ax1_main.clear()
    ax2_main.clear()
    ax1_aux.clear()
    ax2_aux.clear()

    # Восстановление оформления сеток и подписей осей
    for ax, title in zip([ax1_main, ax2_main, ax1_aux, ax2_aux],
                         ["Правый борт (+)", "Левый борт (-)", "Правый борт (+)", "Левый борт (-)"]):
        ax.set_title(title)
        ax.grid(True, which='both', linestyle='--', alpha=0.5)
        ax.set_xlabel("Время, с")
        ax.set_ylabel("Угол крена, град.")
        ax.yaxis.set_major_formatter(FormatStrFormatter('%.3f'))

    # Цикл обработки замеров
    for idx, file_main in enumerate(file_list_main):
        try:
            # 1. Чтение и парсинг данных носового поста
            df_main = pd.read_csv(file_main)
            if df_main.empty:
                log_message(f"Файл {os.path.basename(file_main)} пустой. Пропуск.")
                continue

            # Пересчет абсолютного времени в секунды от начала замера
            df_main['Time_dt'] = pd.to_datetime(df_main['Time'], format='%d.%m.%y %H:%M:%S', errors='coerce')
            total_time_1 = (df_main['Time_dt'].iloc[-1] - df_main['Time_dt'].iloc[0]).total_seconds()
            time_step_1 = total_time_1 / len(df_main) if len(df_main) > 1 else 0.1
            df_main['Time_s'] = df_main.index * time_step_1

            # Фильтрация последних 30 секунд для расчета установившегося режима
            max_time_1 = df_main['Time_s'].max()
            df_last_30_1 = df_main[df_main['Time_s'] >= (max_time_1 - 30)]
            mean_roll_1 = df_last_30_1['CalcY'].mean()

            # Выбор графика для носового датчика (положительный или отрицательный крен)
            target_ax = ax1_main if mean_roll_1 > 0 else ax2_main

            # Отрисовка графика с выводом точного среднего угла в ЛЕГЕНДУ (справа)
            line_1 = target_ax.plot(df_main['Time_s'], df_main['CalcY'], linewidth=2,
                                    label=f"Замер {idx + 1} ({mean_roll_1:.3f}°)" if not pd.isna(
                                        mean_roll_1) else f"Замер {idx + 1}")[0]
            current_color = line_1.get_color()
            target_ax.axhline(y=mean_roll_1, color=current_color, linestyle='--', alpha=0.8)

            # Расчет метацентрической высоты для носового поста
            if abs(mean_roll_1) > 0.1:
                h_meta_1 = (p_cargo * l_distance) / (d_displacement * math.tan(math.radians(abs(mean_roll_1))))
                h_meta_list.append(h_meta_1)
            else:
                h_meta_1 = 0.0

            # Расширенное логирование в левое окно
            arm_val = (p_cargo * l_distance) / d_displacement
            log_message(
                f"> Замер {idx + 1} (Нос): Ср. крен = {mean_roll_1:.3f}°, Плечо = {arm_val:.4f} м, h = {h_meta_1:.3f} м")

            # Сбор данных для отчета Excel
            df_main['Замер'] = idx + 1
            df_main['Пост'] = "Нос"
            all_raw_rows.append(df_main)

            bat_v_1 = df_main['BatV'].iloc[-1] if 'BatV' in df_main.columns else "—"
            summary_results.append({
                "Файл": os.path.basename(file_main), "Пост": "Носовой", "Средний крен (град)": round(mean_roll_1, 3),
                "Высота h (м)": round(h_meta_1, 3), "АКБ (В)": bat_v_1
            })

            # 2. Обработка парного файла кормового поста (если он существует)
            file_aux = file_main.replace("_1.CSV", "_2.CSV")
            if os.path.exists(file_aux):
                df_aux = pd.read_csv(file_aux)
                if not df_aux.empty:
                    df_aux['Time_dt'] = pd.to_datetime(df_aux['Time'], format='%d.%m.%y %H:%M:%S', errors='coerce')
                    total_time_2 = (df_aux['Time_dt'].iloc[-1] - df_aux['Time_dt'].iloc[0]).total_seconds()
                    time_step_2 = total_time_2 / len(df_aux) if len(df_aux) > 1 else 0.1
                    df_aux['Time_s'] = df_aux.index * time_step_2

                    max_time_2 = df_aux['Time_s'].max()
                    df_last_30_2 = df_aux[df_aux['Time_s'] >= (max_time_2 - 30)]
                    mean_roll_2 = df_last_30_2['CalcY'].mean()

                    target_ax_aux = ax1_aux if mean_roll_2 > 0 else ax2_aux

                    # Отрисовка кормы (тем же цветом, но точечным пунктиром и со значением угла в легенде)
                    target_ax_aux.plot(df_aux['Time_s'], df_aux['CalcY'], linewidth=2, linestyle=':',
                                       color=current_color,
                                       label=f"Замер {idx + 1} ({mean_roll_2:.3f}°)" if not pd.isna(
                                           mean_roll_2) else f"Замер {idx + 1}")
                    target_ax_aux.axhline(y=mean_roll_2, color=current_color, linestyle='-.', alpha=0.8)

                    if abs(mean_roll_2) > 0.1:
                        h_meta_2 = (p_cargo * l_distance) / (d_displacement * math.tan(math.radians(abs(mean_roll_2))))
                        h_meta_list.append(h_meta_2)
                    else:
                        h_meta_2 = 0.0

                    log_message(
                        f"> Замер {idx + 1} (Корма): Ср. крен = {mean_roll_2:.3f}°, Плечо = {arm_val:.4f} м, h = {h_meta_2:.3f} м")

                    df_aux['Замер'] = idx + 1
                    df_aux['Пост'] = "Корма"
                    all_raw_rows.append(df_aux)

                    bat_v_2 = df_aux['BatV'].iloc[-1] if 'BatV' in df_aux.columns else "—"
                    summary_results.append({
                        "Файл": os.path.basename(file_aux), "Пост": "Кормовой",
                        "Средний кren (град)": round(mean_roll_2, 3),
                        "Высота h (м)": round(h_meta_2, 3), "АКБ (В)": bat_v_2
                    })

        except pd.errors.EmptyDataError:
            log_message(f"Файл {os.path.basename(file_main)} пустой. Пропуск.")
        except Exception as e:
            log_message(f"Ошибка при обработке {os.path.basename(file_main)}: {e}")

    # Расчет итогового усредненного значения метацентрической высоты
    final_h_meta = sum(h_meta_list) / len(h_meta_list) if h_meta_list else 0.0
    summary_results.append({
        "Файл": "ИТОГОВОЕ СРЕДНЕЕ ЗНАЧЕНИЕ:", "Пост": "—", "Средний крен (град)": "—",
        "Высота h (м)": round(final_h_meta, 3), "АКБ (В)": "—"
    })

    # Отрисовка легенд с автоматическим размещением
    for ax in [ax1_main, ax2_main, ax1_aux, ax2_aux]:
        if ax.get_legend_handles_labels()[0]:
            ax.legend(loc='upper right', fontsize=9)

    canvas_main.draw()
    canvas_aux.draw()

    # Сохранение файлов отчета на флешку/папку
    if all_raw_rows:
        res_df = pd.DataFrame(summary_results)
        raw_df = pd.concat(all_raw_rows, ignore_index=True)
        excel_filename = os.path.join(folder_path, "Отчет_Кренование.xlsx")

        try:
            with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
                res_df.to_excel(writer, sheet_name="Результаты", index=False)
                raw_df.to_excel(writer, sheet_name="Сырые_данные", index=False)
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    for column in worksheet.columns:
                        max_length = max((len(str(cell.value)) for cell in column), default=0)
                        worksheet.column_dimensions[column[0].column_letter].width = (max_length + 2)

            # Сохранение графиков в PNG для диплома
            fig_main.savefig(os.path.join(folder_path, "График_Нос.png"), dpi=300, bbox_inches='tight')
            fig_aux.savefig(os.path.join(folder_path, "График_Корма.png"), dpi=300, bbox_inches='tight')

            log_message("========================================")
            log_message("Расчет завершен успешно!")
            log_message(f"ИТОГОВАЯ СРЕДНЯЯ ВЫСОТА h = {final_h_meta:.3f} м")
            log_message("========================================\n")
        except Exception as e:
            log_message(f"Ошибка сохранения файлов отчета: {e}")


# ==============================================================================
# ЧАСТЬ 2: ГРАФИЧЕСКИЙ ИНТЕРФЕЙС
# ==============================================================================
def choose_folder():
    folder = filedialog.askdirectory(title="Выберите папку с логами")
    if folder:
        folder_var.set(folder)
        log_message(f"Выбрана папка:\n{folder}")


def start_processing():
    try:
        d_val = float(entry_d.get())
        p_val = float(entry_p.get())
        l_val = float(entry_l.get())
    except ValueError:
        messagebox.showerror("Ошибка ввода", "Проверьте числовые значения параметров.")
        return

    folder = folder_var.get()
    if not folder:
        messagebox.showwarning("Ошибка", "Не выбрана папка с измерительными файлами!")
        return

    analyze_inclinometer_data(d_val, p_val, l_val, folder)


def log_message(text):
    text_log.insert(tk.END, text + "\n")
    text_log.see(tk.END)


root = tk.Tk()
root.title("Программный комплекс анализа опыта кренования BWM427")
root.geometry("1400x800")

LARGE_FONT = ("Arial", 12)
folder_var = tk.StringVar()

# Левая панель параметров
frame_left = tk.Frame(root, width=350, padx=15, pady=15)
frame_left.pack(side=tk.LEFT, fill=tk.Y)

tk.Label(frame_left, text="Водоизмещение судна D (т):", font=LARGE_FONT).pack(pady=(10, 2))
entry_d = tk.Entry(frame_left, justify="center", font=LARGE_FONT, width=15)
entry_d.insert(0, "1500.0")
entry_d.pack()

tk.Label(frame_left, text="Масса кренящего груза P (т):", font=LARGE_FONT).pack(pady=(10, 2))
entry_p = tk.Entry(frame_left, justify="center", font=LARGE_FONT, width=15)
entry_p.insert(0, "15.0")
entry_p.pack()

tk.Label(frame_left, text="Макс. плечо переноса L (м):", font=LARGE_FONT).pack(pady=(10, 2))
entry_l = tk.Entry(frame_left, justify="center", font=LARGE_FONT, width=15)
entry_l.insert(0, "4.5")
entry_l.pack()

tk.Label(frame_left, text="Путь к файлам данных:", font=LARGE_FONT).pack(pady=(20, 2))
frame_folder = tk.Frame(frame_left)
frame_folder.pack()
tk.Entry(frame_folder, textvariable=folder_var, width=22, state="readonly", font=LARGE_FONT).pack(side=tk.LEFT, padx=5)
tk.Button(frame_folder, text="Обзор...", command=choose_folder, font=LARGE_FONT).pack(side=tk.LEFT)

tk.Button(frame_left, text="ВЫПОЛНИТЬ РАСЧЕТ", bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
          command=start_processing).pack(pady=25, fill=tk.X, ipady=10)

tk.Label(frame_left, text="Журнал системных сообщений:", font=LARGE_FONT).pack(anchor="w", pady=(10, 2))
text_log = scrolledtext.ScrolledText(frame_left, width=40, height=14, font=("Consolas", 11), bg="#F8F9FA", wrap=tk.WORD)
text_log.pack(fill=tk.BOTH, expand=True)

log_message("Программный комплекс готов к загрузке данных...")

# Правая панель (Вкладки)
frame_right = tk.Frame(root)
frame_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

notebook = ttk.Notebook(frame_right)
notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

tab_main = tk.Frame(notebook)
tab_aux = tk.Frame(notebook)

notebook.add(tab_main, text="  Носовой измерительный post  ")
notebook.add(tab_aux, text="  Кормовой измерительный post  ")

# Холст 1: Носовой пост
fig_main = Figure(figsize=(8, 6), dpi=100)
ax1_main = fig_main.add_subplot(211)
ax2_main = fig_main.add_subplot(212)
fig_main.subplots_adjust(hspace=0.35)
canvas_main = FigureCanvasTkAgg(fig_main, master=tab_main)
canvas_main.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Холст 2: Кормовой пост
fig_aux = Figure(figsize=(8, 6), dpi=100)
ax1_aux = fig_aux.add_subplot(211)
ax2_aux = fig_aux.add_subplot(212)
fig_aux.subplots_adjust(hspace=0.35)
canvas_aux = FigureCanvasTkAgg(fig_aux, master=tab_aux)
canvas_aux.get_tk_widget().pack(fill=tk.BOTH, expand=True)

root.mainloop()