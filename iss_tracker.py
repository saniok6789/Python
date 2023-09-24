import requests
import csv
import time


iss_url = "http://api.open-notify.org/iss-now.json"



def get_iss_position():
    response=requests.get(iss_url)
    data=response.json()
    return data['iss_position']



csv_file='iss_position.csv'

while True:

    iss_position=get_iss_position()


    with open(csv_file, mode='a', newline='') as file:
        writer=csv.writer(file, delimiter=';')
        writer.writerow([iss_position['latitude'], iss_position['longitude']])

    print(f"Записано дані: Широта={iss_position['latitude']}, Довгота={iss_position['longitude']}")

    # Почекати 5 секунд перед наступним запуском
    time.sleep(5)
