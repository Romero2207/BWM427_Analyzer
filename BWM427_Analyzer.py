import os
import glob
import math
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import tkinter as tk
from tkinter import filedialog, messagebox

# ==============================================================================
# ЧАСТЬ 1: МАТЕМАТИКА И ОБРАБОТКА ДАННЫХ
# ==============================================================================
def analyze_inclinometer_data(d_displacement, p_cargo, l_distance, folder_path):
    search_pattern = os.path.join(folder_path, "M_*.CSV")
    file_list = sorted(glob.glob(search_pattern))

    if not file_list:
        messagebox.showwarning("Внимание", "В выбранной папке нет файлов M_*.CSV!")
        return

    summary_results = []
    all_raw_rows = []
    h_meta_list = []  # Список для сбора всех валидных значений высоты h
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
    fig.subplots_adjust(hspace=0.3)

    for file_name in file_list:
        try:
            df = pd.read_csv(file_name)
        except pd.errors.EmptyDataError:
            print(f"Файл {file_name} пустой.")
            continue

        # Автоматический расчет времени (шкала секунд)
        time_clean = df['Time'].astype(str).apply(lambda x: x.split(' ')[1] if ' ' in x else x)
        time_series = pd.to_timedelta(time_clean)
        total_seconds = (time_series.iloc[-1] - time_series.iloc[0]).total_seconds()

        step = total_seconds / (len(df) - 1) if total_seconds > 0 and len(df) > 1 else 0.1
        df['Time_s'] = [i * step for i in range(len(df))]

        df.insert(0, 'Source_File', os.path.basename(file_name))
        all_raw_rows.append(df)

        # Расчет асимптоты по последним 4 секундам
        points_to_take = max(1, int(4.0 / step))
        mean_roll = df['CalcY'].tail(points_to_take).mean()

        if abs(mean_roll) > 0.1:
            h_meta = (p_cargo * l_distance) / (d_displacement * math.tan(math.radians(abs(mean_roll))))
            h_meta_list.append(h_meta)  # Сохраняем значение для итогового среднего
        else:
            h_meta = 0.0

        summary_results.append({
            "Файл": os.path.basename(file_name),
            "Средний крен (град)": round(mean_roll, 4),
            "Высота h (м)": round(h_meta, 3) if h_meta > 0 else "0.000",
            "АКБ (В)": round(df['BatV'].mean(), 2)
        })

        target_ax = ax1 if mean_roll > 0 else ax2
        line = target_ax.plot(df['Time_s'], df['CalcY'], linewidth=2, label=f"Сигнал ({os.path.basename(file_name)})")[0]
        target_ax.axhline(y=mean_roll, color=line.get_color(), linestyle='--', alpha=0.8,
                          label=f"Асимптота: {mean_roll:.3f}°")

    # --- РАСЧЕТ ОДНОГО ИТОГОВОГО ЧИСЛА ДЛЯ ВСЕГО ОПЫТА ---
    final_h_meta = sum(h_meta_list) / len(h_meta_list) if h_meta_list else 0.0

    # Добавляем финальную строчку в итоговую таблицу Excel
    summary_results.append({
        "Файл": "ИТОГОВОЕ СРЕДНЕЕ ЗНАЧЕНИЕ:",
        "Средний крен (град)": "—",
        "Высота h (м)": round(final_h_meta, 3),
        "АКБ (В)": "—"
    })

    for ax, title in zip([ax1, ax2], ["Правый борт (+)", "Левый борт (-)"]):
        ax.set_title(title)
        ax.yaxis.set_major_formatter(FormatStrFormatter('%.3f'))
        ax.grid(True, which='both', linestyle='--', alpha=0.5)
        ax.legend()

    res_df = pd.DataFrame(summary_results)
    raw_df = pd.concat(all_raw_rows, ignore_index=True)
    excel_filename = os.path.join(folder_path, "Отчет_Кренование.xlsx")
    graph_filename = os.path.join(folder_path, "Графики_кренования.png")

    try:
        # Сохраняем Excel
        with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
            res_df.to_excel(writer, sheet_name="Результаты", index=False)
            raw_df.to_excel(writer, sheet_name="Сырые_данные", index=False)

            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    worksheet.column_dimensions[column_letter].width = (max_length + 2)

        # Сохраняем график в картинку (высокое качество 300 dpi) и закрываем фон
        plt.savefig(graph_filename, dpi=300, bbox_inches='tight')
        plt.close(fig)

        # Сообщение об успехе с выводом главного числа
        success_text = f"Все расчеты успешно завершены!\n\nИтоговая метацентрическая высота h = {final_h_meta:.3f} м\n\nФайлы сохранены в папку:\n{folder_path}"
        messagebox.showinfo("Готово", success_text)

    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка при сохранении файлов: {e}")
        plt.close(fig)


# ==============================================================================
# ЧАСТЬ 2: ГРАФИЧЕСКИЙ ИНТЕРФЕЙС (Окно программы)
# ==============================================================================
def choose_folder():
    folder = filedialog.askdirectory(title="Выберите папку с файлами SD-карты")
    if folder:
        folder_var.set(folder)


def start_processing():
    try:
        d_val = float(entry_d.get())
        p_val = float(entry_p.get())
        l_val = float(entry_l.get())
    except ValueError:
        messagebox.showerror("Ошибка ввода", "Пожалуйста, введите корректные числа (используйте точку для дробей).")
        return

    folder = folder_var.get()
    if not folder:
        messagebox.showwarning("Ошибка", "Сначала выберите папку с файлами!")
        return

    analyze_inclinometer_data(d_val, p_val, l_val, folder)


# --- Настройка главного окна ---
root = tk.Tk()
root.title("Анализатор кренования BWM427")
root.geometry("650x450")  # Увеличенный размер окна

# Задаем крупный шрифт для всего интерфейса
LARGE_FONT = ("Arial", 14)
BUTTON_FONT = ("Arial", 14, "bold")

folder_var = tk.StringVar()

# 1. Настройка водоизмещения (D)
tk.Label(root, text="Водоизмещение судна (т):", font=LARGE_FONT).pack(pady=(15, 5))
entry_d = tk.Entry(root, justify="center", font=LARGE_FONT, width=15)
entry_d.insert(0, "1500.0")
entry_d.pack()

# 2. Настройка массы груза (P)
tk.Label(root, text="Масса кренящего груза (т):", font=LARGE_FONT).pack(pady=(10, 5))
entry_p = tk.Entry(root, justify="center", font=LARGE_FONT, width=15)
entry_p.insert(0, "15.0")
entry_p.pack()

# 3. Настройка плеча (L)
tk.Label(root, text="Плечо переноса груза (м):", font=LARGE_FONT).pack(pady=(10, 5))
entry_l = tk.Entry(root, justify="center", font=LARGE_FONT, width=15)
entry_l.insert(0, "4.5")
entry_l.pack()

# 4. Выбор папки
tk.Label(root, text="Папка с файлами (M_*.CSV):", font=LARGE_FONT).pack(pady=(20, 5))
frame_folder = tk.Frame(root)
frame_folder.pack()
tk.Entry(frame_folder, textvariable=folder_var, width=35, state="readonly", font=LARGE_FONT).pack(side=tk.LEFT, padx=5)
tk.Button(frame_folder, text="Обзор...", command=choose_folder, font=LARGE_FONT).pack(side=tk.LEFT)

# 5. Главная кнопка запуска
btn_start = tk.Button(root, text="РАССЧИТАТЬ И СОХРАНИТЬ ОТЧЕТ", bg="#4CAF50", fg="white", font=BUTTON_FONT,
                      command=start_processing)
btn_start.pack(pady=30, fill=tk.X, padx=50, ipady=10)

# Запускаем бесконечный цикл отрисовки окна
root.mainloop()