import random
import datetime


def generate_csv(filename, start_time_str, base_angle, num_rows=100):
    with open(filename, 'w') as f:
        # Записываем заголовки столбцов
        f.write("Time,CalcX,CalcY,BatV\n")

        # Парсим стартовое время
        h, m, s = map(int, start_time_str.split(':'))
        current_time = datetime.timedelta(hours=h, minutes=m, seconds=s)

        for _ in range(num_rows):
            # Форматируем время (убираем дни, если они появились)
            time_str = str(current_time).split(', ')[-1]
            if len(time_str) < 8:
                time_str = "0" + time_str

            # Генерируем реалистичный крен с микро-качкой (шум от -0.040 до +0.040)
            noise = random.uniform(-0.040, 0.040)
            calc_x = round(base_angle + noise, 3)

            # Остальные данные "для массовки"
            calc_y = round(random.uniform(-0.1, 0.1), 3)
            bat_v = round(random.uniform(12.35, 12.45), 2)

            # Пишем строку в файл
            f.write(f"{time_str},{calc_x},{calc_y},{bat_v}\n")

            # Шаг времени = 1 секунда
            current_time += datetime.timedelta(seconds=1)


# Генерируем Правый борт (+) со средним креном ~ 2.450 градуса
generate_csv("M_001.CSV", "10:15:00", 2.450)

# Генерируем Левый борт (-) со средним креном ~ -2.315 градуса
generate_csv("M_002.CSV", "10:20:00", -2.315)

print("✅ Тестовые файлы M_001.CSV и M_002.CSV успешно созданы (по 100 значений)!")