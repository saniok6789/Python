import requests
import csv
import time

# URL для отримання даних про положення МКС
iss_url = "http://api.open-notify.org/iss-now.json"


# Функція для отримання даних про положення МКС
def get_iss_position():
    response = requests.get(iss_url)
    data = response.json()
    return data['iss_position']


# Назва CSV-файлу для зберігання даних
csv_file = 'iss_position.csv'

while True:
    # Отримуємо дані про положення МКС
    iss_position = get_iss_position()

    # Записуємо дані у CSV-файл
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow([iss_position['latitude'], iss_position['longitude']])

    print(f"Записано дані: Широта={iss_position['latitude']}, Довгота={iss_position['longitude']}")

    # Почекати 5 секунд перед наступним запуском
    time.sleep(5)
