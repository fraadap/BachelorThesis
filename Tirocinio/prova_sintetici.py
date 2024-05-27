import pandas as pd
import re
import random
from datetime import datetime, timedelta
import csv

# Carica il file TSV per analizzarlo
file_path = 'csv/a.csv'
df = pd.read_csv(file_path, delimiter=',', encoding='utf-8')



def normalize_text(t):
    """ Normalizza il testo """
    t = t.lower()
    t = re.sub(r'[è|é]', 'e', t)
    t = re.sub(r'[à|á]', 'a', t)
    t = re.sub(r'[ì|í]', 'i', t)
    t = re.sub(r'[ò|ó]', 'o', t)
    t = re.sub(r'[ù|ú]', 'u', t)
    t = re.sub(r'domeniche', 'domenica', t)
    t = re.sub(r'sabati', 'sabato', t)
    t = re.sub(r'volta', 'volte', t)
    t = re.sub(r'\s+', ' ', t).strip()
    t = t.replace('. ', '')
    t = t.replace(',', '')
    t = t.replace(';', '')
    t = t.replace('\n', '')
    return t


def text_to_number(text):
    """ Converte i numeri scritti in lettere nei loro equivalenti numerici """
    numbers = {
        "una": 1, "uno": 1, "due": 2, "tre": 3, "quattro": 4, "cinque": 5,
        "sei": 6, "sette": 7, "otto": 8, "nove": 9, "dieci": 10
    }
    return numbers.get(text, text)


def normalize_time(time_str):
    """ Converte gli orari in formato HH:MM. """
    if ':' not in time_str and '.' not in time_str:
        time_str += ':00'
    time_str = time_str.replace('.', ':')
    hour, minute = map(int, time_str.split(':'))
    return f"{hour:02}:{minute:02}"


def time_about(approx_time, range):
    """Restituisce l'orario cambiandolo di [-range, +range] minuti utilizzando una gaussiana"""
    mu = 0  # Media
    sigma = (range * 2) / 6  # Deviazione standard

    while True:
        rand = random.gauss(mu, sigma)
        if -range <= rand <= range:
            break

    time_obj = datetime.strptime(approx_time, "%H:%M")
    new_time_obj = time_obj - timedelta(minutes=rand)
    new_time_str = new_time_obj.strftime("%H:%M")
    return new_time_str


def generic_day_assignment(matches, type, day_time, days):
    prob = 90
    for match in matches:
        if type == "all":
            times = 7
            almost_all = match[0]
            time_str = match[3]
            about = match[4]
            for _ in range(7):
                if almost_all:
                    rand = random.randint(0, 100)
                    if rand >= prob:
                        times = times - 1
        else:
            times = int(text_to_number(match[0]))
            time_str = match[3]
            about = match[4]

        normalized_time = normalize_time(time_str)
        prob = 90
        total_slots = times

        while total_slots > 0:
            for day in random.sample(days, min(total_slots, len(days))):
                if about:
                    time_ab = time_about(normalized_time, 20)
                else:
                    time_ab = time_about(normalized_time, 10)
                day_time[day].append(time_ab)
                total_slots -= 1
    return day_time


def extract_days_times(t):
    """ Cattura i principali pattern e attribuisce gli orari ai giorni"""
    days = ['lunedi', 'martedi', 'mercoledi', 'giovedi', 'venerdi', 'sabato', 'domenica']

    # pattern n volte a settimana alle time
    pattern_n_times_week = (r"(\d+|una|uno|due|tre|quattro|cinque|sei|sette|otto|nove|dieci)\s*(volte|giorni)\s*.*?\s*"
                            r"(alle|per le|a|dalle)\s*(\d{1,2}(?:[:.]\d{0,2})?)\s*(circa)*\s*")

    # pattern giorno_settimana alle time
    pattern_specific_day = (r"(piu o meno |quasi tutti i |quasi tutte le |quasi ogni |quasi tutti i )*"
                            r"(lunedi|martedi|mercoledi|giovedi|venerdi|sabato|domenica)")
    pattern_specific_time = r"(alle|per le|a|dalle|le)*\s*(\d{1,2}(?:[:.]\d{0,2})?)\s*(circa)*"

    # pattern tutti i giorni alle
    pattern_all_days = \
        (r"(piu o meno |quasi )*"
         r"(tutti i giorni|ogni giorno|tutta la |tutte le mattine|tutte le sere|ogni mattina|ogni sera|sempre)"
         r"\s*.*?\s*(alle|per le|a|dalle)\s*(\d{1,2}(?:[:.]\d{0,2})?)\s*(circa)*\s*")

    day_time_dict = {day: [] for day in days}

    matches = re.findall(pattern_n_times_week, t)
    day_time_dict = generic_day_assignment(matches, "num", day_time_dict, days)

    matches = re.findall(pattern_all_days, t)
    day_time_dict = generic_day_assignment(matches, "all", day_time_dict, days)

    for match in re.finditer(pattern_specific_day, t):
        almost_all = match.group(1)
        if almost_all:
            prob = 80
        else:
            prob = 100
        rand = random.randint(0, 100)
        if rand <= prob:
            day = match.group(2)
            text_after_day = t[match.end():]
            expression_time = re.findall(pattern_specific_time, text_after_day)
            if expression_time:
                time_str = expression_time[0][1]
                normalized_time = normalize_time(time_str)
                about = expression_time[0][2]
                if about:
                    normalized_time = time_about(normalized_time, 20)
                else:
                    normalized_time = time_about(normalized_time, 10)

                day_time_dict[day].append(normalized_time)

    return day_time_dict


def extract_user_habits(df):
    """ Estrae le abitudini degli utenti dalle risposte del questionario """
    habits = []
    for _, row in df.iterrows():
        user_habits = {}
        user_habits['bluetooth'] = row['Ti connetti mai al bluetooth della tua macchina?'] == 'Si'
        user_habits['bluetooth_frequency'] = row['Quanto spesso ti connetti al bluetooth quando sei nella tua auto?']
        user_habits['carplay'] = row['La tua macchina ha un sistema di Apple Car Play/Android Auto?'] == 'Si'
        user_habits['carplay_frequency'] = row[
            ' Quanto spesso ti capita di collegarti a Apple Car Play o Android auto sulla tua macchina?']
        user_habits['charging_frequency'] = row['Quanto spesso ti capita di mettere in carica il telefono in macchina?']
        user_habits['home_wifi'] = row['Hai un WiFi in casa che usi spesso dal telefono?'] == 'Si'
        user_habits['work_wifi'] = row[
            'Quanto spesso ti capita di collegarti a una rete wifi con il telefono quando sei a lavoro/Università?']
        user_habits['driving_to_work'] = row[
            'Quanto spesso vai a lavoro/Università in macchina? (anche solo per fare il cambio con un mezzo pubblico)']
        user_habits['work_commute'] = {
            'distance': row['Quanto è lungo approssimativamente il tragitto in macchina (Km)? Indicare solo il numero'],
            'duration': row['Più o meno quanto ci metteresti?'],
            'days_per_week': row['Quanti giorni a settimana vai indicativamente a lavoro/università?'],
            'leave_home': row['Qual è l\'orario in cui parti da casa per andarci più spesso attualmente?'],
            'leave_work': row['Qual è l\'orario in cui riparti per tornare a casa più spesso attualmente?']
        }
        user_habits['other_activities'] = row[
            'Fai qualche esempio di attività che svolgi regolarmente andandoci con la tua auto indicando il giorno e l\'ora. Non serve che specifichi il tipo di attività. Per esempio: venerdì alle 18, sabato alle 12. Oppure lunedì martedì venerdì alle 20 Più preciso sarai a formattare e più sarà facile lavorare con i dati ']

        habits.append(user_habits)
    return habits


# Estrazione delle abitudini degli utenti
user_habits = extract_user_habits(df)


# Funzione per generare i dati dei sensori basati sulle abitudini
def generate_sensor_data(user_habits, start_date, end_date):
    """ Genera dati sintetici basati sulle abitudini dell'utente e simula i valori dei sensori """
    current_time = start_date
    sensor_data = []

    while current_time <= end_date:
        day_of_week = current_time.strftime('%A').lower()
        time_of_day = current_time.strftime('%H:%M')

        # Default sensor values
        wifi = 0.5
        bluetooth = 0.5
        battery = 0.5
        motion_sensor = 0
        gps = 0
        accelerometer = 0.5
        cell_change = 0.5
        carplay_android_auto = 0

        for habit in user_habits:
            # Adjust sensor values based on user habits
            if habit['bluetooth']:
                bluetooth = 1 if random.random() > 0.2 else 0.5  # 80% probability of being connected
            if habit['carplay']:
                carplay_android_auto = 1
            if habit['charging_frequency'] != 'Mai':
                battery = 0 if random.random() > 0.8 else 0.5  # 20% probability of being connected to fast charging
            if day_of_week in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'] and 8 <= current_time.hour < 18:
                wifi = 0  # Connected to work WiFi during working hours
            elif habit['home_wifi'] and 19 <= current_time.hour < 23 and day_of_week in ['saturday', 'sunday']:
                wifi = 0  # Connected to home WiFi in the evening and weekends

            # Simulate driving times based on extracted habits
            if time_of_day in habit['work_commute']['leave_home']:
                motion_sensor = 1
                gps = 1
                accelerometer = 0
            if time_of_day in habit['work_commute']['leave_work']:
                motion_sensor = 1
                gps = 1
                accelerometer = 0

            # Check other activities
            other_activities = habit['other_activities'].split()
            for activity in other_activities:
                if time_of_day in activity:
                    motion_sensor = 1
                    gps = 1
                    accelerometer = 0

        # Add noise and false positives
        if random.random() > 0.95:  # 5% chance of error
            motion_sensor = 1 - motion_sensor
            gps = 1 - gps

        # Create the sensor data row
        sensor_data.append([
            'user1',  # User ID
            current_time.strftime('%Y-%m-%d %H:%M:%S'),
            wifi, bluetooth, battery, motion_sensor, gps, accelerometer, cell_change, carplay_android_auto
        ])

        current_time += timedelta(minutes=1)  # Increment the timestamp by one minute

    return sensor_data


# Definizione dell'intervallo di tempo
start_date = datetime(2024, 1, 1, 0, 0)
end_date = datetime(2024, 1, 31, 23, 59)

# Generazione dei dati sintetici per ogni utente
all_sensor_data = []
for habits in user_habits:
    sensor_data = generate_sensor_data([habits], start_date, end_date)
    all_sensor_data.extend(sensor_data)

# Salvataggio in un file CSV
with open('sensor_data.csv', 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(
        ['UserID', 'Timestamp', 'WiFi', 'Bluetooth', 'Battery', 'MotionSensor', 'GPS', 'Accelerometer', 'CellChange',
         'CarPlay_AndroidAuto'])
    csvwriter.writerows(all_sensor_data)
