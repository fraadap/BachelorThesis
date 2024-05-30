import pandas as pd
import csv
import re
import random
from datetime import datetime, timedelta

days = ['lunedi', 'martedi', 'mercoledi', 'giovedi', 'venerdi', 'sabato', 'domenica']


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
        time_str += '.00'
    time_str = time_str.replace(':', '.')
    hour, minute = map(int, time_str.split('.'))
    return f"{hour:02}.{minute:02}"


def random_interval_activity(time, n1, n2):
    """ Restituisce l'orario cambiandolo di [-range, +range] minuti utilizzando una gaussiana """
    # calcolo dell'intorno in maniera randomica
    time_normalized = normalize_time(time)
    start_time_obj, time_start = dirty_time(time_normalized, n1, n2)

    average = 20  # media settata a 20 minuti
    sigma = 5  # Deviazione standard
    rand = random.gauss(average, sigma)
    # calcolo della fine del trip in maniera randomica
    end_time_obj = start_time_obj + timedelta(minutes=rand)
    time_end = end_time_obj.strftime("%H.%M")

    return time_start, time_end


def generic_day_assignment(matches, flag, day_time):
    """ Genera i trip in macchina per le attività con il pattern n giorni alle ...  """
    prob = 90
    for match in matches:
        if flag == "all":
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
        returned = random_interval_activity(normalized_time, n1=30,
                                            n2=180)  # attività settata tra mezz'ora e 3 ore. media:2 ore
        while total_slots > 0:
            for day in random.sample(days, min(total_slots, len(days))):  # 8 volte -> 7 volte
                if about:
                    time_ab = random_interval_activity(normalized_time, n1=-20, n2=20)
                else:
                    time_ab = random_interval_activity(normalized_time, n1=-10, n2=10)
                return_about = random_interval_activity(returned[0], n1=-10, n2=10)
                day_time["automotive"][day].append(time_ab + return_about + ("act",))
                total_slots -= 1
    return day_time


def specific_day_assignment(matches, day_time, t, pattern_time):
    """ Genera i trip in macchina per le attività con il pattern 'giorno specifico' alle ...  """
    for i in range(len(matches)):
        match = matches[i]
        almost_all = match[0]
        if almost_all:
            prob = 80
        else:
            prob = 100
        rand = random.randint(0, 100)
        if rand <= prob:
            day = match[1]
            text_after_day = t[t.index(day) + len(day):]
            expression_time = re.findall(pattern_time, text_after_day)
            if expression_time:
                time_str = expression_time[0][1]
                normalized_time = normalize_time(time_str)
                about = expression_time[0][2]
                if about:
                    normalized_time = random_interval_activity(normalized_time, n1=-20, n2=20)
                else:
                    normalized_time = random_interval_activity(normalized_time, n1=-10, n2=10)
                returning = random_interval_activity(normalized_time[1], n1=30, n2=180)

                day_time["automotive"][day].append((normalized_time + returning + (
                "act",)))  # aggiunta del ritorno dall'attività con una durata media di 2 ore, tra 3 minuti e 3 ore

    return day_time


def extract_auto_activities(t):
    """ Cattura i principali pattern e attribuisce gli orari ai giorni """
    t = normalize_text(t)

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

    # definizione dei trip a piedi, in macchina o con mezzi di trasporto
    day_time_dict = {"walking": {day: [] for day in days}, "automotive": {day: [] for day in days},
                     "public": {day: [] for day in days}}

    matches = re.findall(pattern_n_times_week, t)
    generic_day_assignment(matches, "num", day_time_dict)

    matches = re.findall(pattern_all_days, t)
    generic_day_assignment(matches, "all", day_time_dict)

    matches = re.findall(pattern_specific_day, t)
    specific_day_assignment(matches, day_time_dict, t, pattern_specific_time)
    return day_time_dict


def extract_user_habits(df):
    """ Estrae le abitudini degli utenti dalle risposte del questionario """
    habits = []
    for _, row in df.iterrows():
        user_habits = {}
        user_habits['os_phone'] = row.iloc[2]  # Android o iphone
        user_habits['bluetooth'] = row.iloc[3] == 'Si'  # usi bluetooth?
        user_habits['bluetooth_frequency'] = row.iloc[4]  # quanto spesso?
        user_habits['bluetooth_last_time'] = row.iloc[5] if not pd.isna(row.iloc[5]) else "Non ricordo"  # ultima volta?
        user_habits['bluetooth_connection'] = row.iloc[6] if not pd.isna(
            row.iloc[6]) else "Dipende"  # si connette manuale o automatica?
        user_habits['bluetooth_other'] = row.iloc[7] if not pd.isna(
            row.iloc[7]) else "Mai"  # ogni quanto ti connetti al bluetooth di altre macchine?
        user_habits['carplay'] = row.iloc[8] == 'Si'  # ha il carplay?
        user_habits['carplay_frequency'] = row.iloc[9] if user_habits[
            'carplay'] else "Mai"  # ogni quanto ti connetti ad esso?
        user_habits['carplay_connection'] = row.iloc[10] if user_habits[
            'carplay'] else "Nessuno dei due"  # con cavo o wireless?
        user_habits['carplay_other'] = row.iloc[11] if not pd.isna(
            row.iloc[11]) else "Mai"  # ogni quanto ti connetti al carplay di altre auto?
        user_habits['charging_frequency'] = row.iloc[12] if not pd.isna(
            row.iloc[12]) else "Mai"  # ogni quanto carichi il telefono in auto?
        user_habits['charging_place'] = row.iloc[13] if not pd.isna(
            row.iloc[13]) else "Non lo collego"  # lo attacchi all'accendisigari o all'auto?
        user_habits['wifi_home'] = row.iloc[14] == 'Si'  # hai un wifi in casa che usi?
        user_habits['wifi_work_frequency'] = row.iloc[15] if not pd.isna(
            row.iloc[15]) else "Mai"  # quanto spesso ti connetti al wifi al lavoro?
        user_habits['commute'] = {
            'driving_to_work_frequency': row.iloc[16] if not pd.isna(row.iloc[16]) else "Mai",
            # quanto spesso vai in macchina a lavoro?
            'distance': row.iloc[17] if not pd.isna(row.iloc[17]) else "3.0",  # distanza casa-lavoro in km
            'duration': row.iloc[18] if not pd.isna(row.iloc[18]) else "0.15.00",  # distanza casa-lavoro in minuti
            'days_per_week': row.iloc[19] if not pd.isna(row.iloc[19]) else 3.0,
            # quanti giorni a settimana vai a lavoro
            'leave_home': row.iloc[20] if not pd.isna(row.iloc[20]) else "8.00.00",
            # a che ora lasci casa per andare a lavoro
            'leave_work': row.iloc[21] if not pd.isna(row.iloc[21]) else "17.10.00",
            # a che ora lasci il lavoro per tornare a casa
        }
        user_habits['activities_exist'] = row.iloc[22] == "Si"  # fai attività regolari andandoci in macchina?
        user_habits['activities'] = row.iloc[23] if not pd.isna(row.iloc[23]) else ""  # Stringa con le attività
        user_habits['sex'] = row.iloc[24] if not pd.isna(row.iloc[24]) else random.randint(0, 1)  # Sesso dell'utente
        user_habits['age'] = row.iloc[25] if not pd.isna(row.iloc[25]) else random.randint(18, 50)  # Età dell'utente
        prepare_data(user_habits)
        habits.append(user_habits)
    return habits


def dirty_time(time, n1, n2):
    """ Aggiunge un rumore casuale al timestamp dato da limiti """
    rand = random.randint(n1, n2)

    time_obj = datetime.strptime(time, "%H.%M")
    start_time_obj = time_obj + timedelta(minutes=rand)
    time = start_time_obj.strftime("%H.%M")
    return start_time_obj, time


def extract_working_trips(commute, trips):
    """ Genera i trip per andare a lavoro in macchina altrimenti con i mezzi o a piedi """
    working_days = ['lunedi', 'martedi', 'mercoledi', 'giovedi', 'venerdi']

    morning = commute['leave_home']
    duration = datetime.strptime(commute['duration'], "%H.%M")
    duration = duration.hour * 60 + duration.minute
    distance = commute['distance']
    returning = commute['leave_work']
    variation = int(duration / 100 * 30)

    for day in random.sample(working_days, int(commute['days_per_week'])):

        rand = random.randint(0, 100)
        if rand < commute['driving_to_work_frequency'] * 100:
            # va in macchina
            dirty_duration_morning = random.randint(-variation, variation) + duration  # più o meno del 20%
            obj_morning, dirty_morning = dirty_time(morning, -5,
                                                    15)  # qui è compreso il viaggio da fare fino alla macchina
            end_morning = obj_morning + timedelta(minutes=dirty_duration_morning)
            end_morning = end_morning.strftime("%H.%M")

            dirty_duration_returning = random.randint(-variation, variation) + duration  # più o meno del 20%
            obj_returning, dirty_returning = dirty_time(returning, -5,
                                                        15)  # qui è compreso il viaggio da fare fino alla macchina
            end_returning = obj_returning + timedelta(minutes=dirty_duration_returning)
            end_returning = end_returning.strftime("%H.%M")

            trips['automotive'][day].append((dirty_morning, end_morning, dirty_returning, end_returning, "work"))
            pass
        else:
            if distance < 1:
                obj_morning, dirty_morning = dirty_time(morning, -10, 10)
                end_morning = obj_morning + timedelta(minutes=random.randint(5, 10))
                end_morning = end_morning.strftime("%H.%M")

                obj_returning, dirty_returning = dirty_time(returning, -10, 10)
                end_returning = obj_returning + timedelta(minutes=random.randint(5, 10))
                end_returning = end_returning.strftime("%H.%M")
                trips['walking'][day].append(
                    (dirty_morning, end_morning, dirty_returning, end_returning, "walking_to_work"))
            else:

                dirty_duration_morning = random.randint(-variation, variation) + duration  # più o meno del 20%
                obj_morning, dirty_morning = dirty_time(morning, 5,
                                                        25)  # qui è compreso il viaggio da fare fino alla fermata + aspettare il bus
                end_morning = obj_morning + timedelta(minutes=dirty_duration_morning)
                end_morning = end_morning.strftime("%H.%M")

                dirty_duration_returning = random.randint(-variation, variation) + duration  # più o meno del 20%
                obj_returning, dirty_returning = dirty_time(returning, 5,
                                                            25)  # qui è compreso il viaggio da fare fino alla fermata + aspettare il bus
                end_returning = obj_returning + timedelta(minutes=dirty_duration_returning)
                end_returning = end_returning.strftime("%H.%M")

                trips['public'][day].append((dirty_morning, end_morning, dirty_returning, end_returning, "work"))
    return trips


def sort_trips(trips):
    """ Ordina i trip in base alla data di inizio """
    for mode in trips:
        for day in trips[mode]:
            trips[mode][day].sort()

    return trips


def time_to_minutes(time_str):
    """ Converte un orario in minuti """
    hour, minute = map(int, time_str.split('.'))
    if hour < 3:  # 2 di notte è maggiore delle 23
        hour += 24
    return hour * 60 + minute


def is_conflict(trip1, trip2):
    """ Verifica se c'è un conflitto tra due viaggi o tra gli intervalli delle attività """
    start1, end1, return_start1, return_end1, _ = trip1
    start2, end2, return_start2, return_end2, _ = trip2

    start1 = time_to_minutes(start1)
    end1 = time_to_minutes(end1)
    return_start1 = time_to_minutes(return_start1)
    return_end1 = time_to_minutes(return_end1)

    start2 = time_to_minutes(start2)
    end2 = time_to_minutes(end2)
    return_start2 = time_to_minutes(return_start2)
    return_end2 = time_to_minutes(return_end2)
    if start1 == start2 and end1 == end2 and return_start1 == return_start2 and return_end1 == return_end2:
        return False

    conflict1 = (start1 < end2 and end1 > start2) or (return_start1 < return_end2 and return_end1 > return_start2)
    conflict2 = (start2 < start1 < return_end2)
    return conflict1 or conflict2


def move_trip(trip, source_day, trips):
    """ Sposta il viaggio a un altro giorno senza conflitti """
    # prende un giorno random
    for day in random.sample(days, 7):
        if day != source_day:
            if not any(is_conflict(trip, other_trip) for other_trip in trips['automotive'][day]) and \
                    not any(is_conflict(trip, other_trip) for other_trip in trips['public'][day]) and \
                    not any(is_conflict(trip, other_trip) for other_trip in trips['walking'][day]):
                trips['automotive'][day].append(trip)
                return  # se è possibile lo aggiunge a quel giorno
    return


def resolve_conflicts(trips):
    """ Verifica conflitti tra act e work (automotive e public) e in caso li sposta """
    for day in days:
        i = 0
        while i < len(trips['automotive'][day]):
            trip1 = trips['automotive'][day][i]
            if trip1[4] == 'act':
                # Controlla contro tutti i work di automotive
                if any(is_conflict(trip1, work_trip) for work_trip in trips['automotive'][day]):
                    move_trip(trip1, day, trips)
                    trips['automotive'][day].pop(i)
                    continue
                # Controlla contro tutti i work di public
                if any(is_conflict(trip1, work_trip) for work_trip in trips['public'][day]):
                    move_trip(trip1, day, trips)
                    trips['automotive'][day].pop(i)
                    continue
                if any(is_conflict(trip1, work_trip) for work_trip in trips['walking'][day]):
                    move_trip(trip1, day, trips)
                    trips['automotive'][day].pop(i)
                    continue
            i += 1

    return trips


def minutes_after(time, minutes):
    """ Restituisce il tempo aumentato di tot minuti """
    new_time_str = (datetime.strptime(time, "%H.%M") + timedelta(minutes=minutes)).strftime("%H.%M")
    return new_time_str


def day_after(day, n):
    """ Restituisce il giorno dopo  """
    return days[(days.index(day) + n) % len(days)]


def is_next_day(time1, time2):
    """ Controlla se il primo tempo è il giorno dopo del secondo
    se il primo tempo è più piccolo del secondo di 12 allora vuol dire che è scattata la mezzanotte """
    t1 = datetime.strptime(time1, "%H.%M")
    t2 = datetime.strptime(time2, "%H.%M")
    return t1.hour < t2.hour - 12


def is_late(time):
    return datetime.strptime(time, "%H.%M").hour > 12


def assign_walking(trips):
    """ Assegna lo stato walking randomico prima e dopo di prendere la macchina/i mezzi e mette lo stato interno (work) """

    def add_walks(start, stop):
        if mode == "automotive":
            n1, n2 = (2, 10)
        elif mode == "public":
            n1, n2 = (10, 20)
        else:
            return start, stop
        _, dirty_start1 = dirty_time(pre_start1, -n2,
                                     -n1)  # randomizzazione su quanto ci mette a prendere la macchina partendo da casa
        _, dirty_end1 = dirty_time(post_end1, n1,
                                   n2)  # randomizzazione su quanto ci mette ad arrivare a lavoro dopo aver parcheggiato
        _, dirty_start2 = dirty_time(pre_start2, -n2,
                                     -n1)  # randomizzazione su quanto ci mette a prendere la macchina partendo da lavoro
        _, dirty_end2 = dirty_time(post_end2, n1,
                                   n2)  # randomizzazione su quanto ci mette ad arrivare a casa dopo aver parcheggiato

        if is_late(dirty_start1) and not start_is_late:
            trips["walking"][day_after(day, -1)].append((dirty_start1, pre_start1, "walk"))
        else:
            trips["walking"][day].append((dirty_start1, pre_start1, "walk"))

        if not is_late(post_end1) and start_is_late:
            trips["walking"][day_after(day, 1)].append((post_end1, dirty_end1, "walk"))
        else:
            trips["walking"][day].append((post_end1, dirty_end1, "walk"))
        if not is_late(dirty_start2) and start_is_late:
            trips["walking"][day_after(day, 1)].append((dirty_start2, pre_start2, "walk"))
        else:
            trips["walking"][day].append((dirty_start2, pre_start2, "walk"))

        if not is_late(post_end2) and start_is_late:
            trips["walking"][day_after(day, 1)].append((post_end2, dirty_end2, "walk"))
        else:
            trips["walking"][day].append((post_end2, dirty_end2, "walk"))

        start = minutes_after(dirty_end1, 1)
        stop = minutes_after(dirty_start2, -1)
        return start, stop

    for mode in trips:
        for day in trips[mode]:
            for i, trip in enumerate(trips[mode][day]):
                if len(trip) == 5:
                    start_is_late = is_late(trip[0])
                    pre_start1 = minutes_after(trip[0], -1)
                    post_end1 = minutes_after(trip[1], 1)
                    pre_start2 = minutes_after(trip[2], -1)
                    post_end2 = minutes_after(trip[3], 1)
                    start_inter = post_end1
                    stop_inter = pre_start2
                    start_inter, stop_inter = add_walks(start_inter, stop_inter)

                    if trip[4] == "work" or trip[4] == "walking_to_work":
                        label = "work"
                    elif trip[4] == "act":
                        label = "act"
                        # aggiunta dell'intervallo in cui è in ufficio a lavorare o una attività
                    if (start_is_late and not is_late(start_inter)):
                        trips["walking"][day_after(day, 1)].append((start_inter, stop_inter, label))
                    else:
                        trips["walking"][day].append((start_inter, stop_inter, label))

                    #trips[mode][day].pop(i)  # splitta andata e ritorno in due viaggi diversi

                    trips[mode][day][i] = (trip[0], trip[1], trip[4])

                    if not is_late(stop_inter) and start_is_late:
                        trips[mode][day_after(day, 1)].append((trip[2], trip[3], trip[4]))
                    else:
                        trips[mode][day].append((trip[2], trip[3], trip[4]))

    return trips


def split_midnight_trips(trips):
    """ Splitta i trip a cavallo della mezzanotte fino alle 23.59 e dalle 00.00 del giorno dopo """
    for mode in trips:
        for day in trips[mode]:
            for i, trip in enumerate(trips[mode][day]):
                if is_late(trip[0]) and not is_late(trip[1]):
                    trips[mode][day].pop(i)
                    trips[mode][day].append((trip[0], "23.59", trip[2]))
                    trips[mode][day_after(day, 1)].append(("00.00", trip[1], trip[2]))
    return trips


def add_home_state(trips):
    """ Riempie gli intervalli liberi con lo stato home di walking (posiziona l'utente a casa) """
    for day in days:
        intervals_day = []
        for mode in trips:
            intervals_day += trips[mode][day]
        if intervals_day:
            intervals_day.sort()
            if intervals_day[0][0] != "00.00":
                trips["walking"][day].append(("00.00", minutes_after(intervals_day[0][0], -1), "home"))
            if intervals_day[-1][0] != "23.59":
                trips["walking"][day].append((minutes_after(intervals_day[-1][1], 1), "23.59", "home"))
            for i in range(len(intervals_day) - 1):
                if time_to_minutes(intervals_day[i][1]) + 1 != time_to_minutes(intervals_day[i+1][0]) :  # se c'è dello spazio
                    trips["walking"][day].append((minutes_after(intervals_day[i][1], 1),
                                                 minutes_after(intervals_day[i+1][0], -1), "home"))
    for day in days:
        if trips["walking"][day] == []:
            trips["walking"][day].append(("00.00", "23.59", "home"))

    return trips


def merge_dicts(trips):
    merged = {day: [] for day in days}
    for day in days:
        intervals_day = []
        for mode in trips:
            temp = trips[mode][day]
            for i in range(len(temp)):
                if mode != "walking":
                    temp[i] = (temp[i][0], temp[i][1], temp[i][2].replace("act", mode))
                    temp[i] = (temp[i][0], temp[i][1], temp[i][2].replace("work", mode))
                else:
                    temp[i] = (temp[i][0], temp[i][1], temp[i][2].replace("walking_to_work", mode))
            intervals_day += temp
        intervals_day.sort()
        merged[day] = intervals_day
    return trips


def prepare_data(us_h):
    """ Normalizza i dati che devono essere utilizzati in maniera numerica o strutturata e non come stringa """
    us_h['bluetooth_frequency'] = regolize_frequency(us_h['bluetooth_frequency'])
    us_h['bluetooth_other'] = regolize_frequency(us_h['bluetooth_other'])
    us_h['carplay_frequency'] = regolize_frequency(us_h['carplay_frequency'])
    us_h['carplay_other'] = regolize_frequency(us_h['carplay_other'])
    us_h['charging_frequency'] = regolize_frequency(us_h['charging_frequency'])
    us_h['wifi_work_frequency'] = regolize_frequency(us_h['wifi_work_frequency'])
    us_h['commute']['driving_to_work_frequency'] = regolize_frequency(us_h['commute']['driving_to_work_frequency'])
    temp = us_h['commute']['duration'].split('.')
    if int(temp[0]) > 3:
        temp[0] = 0
    if int(temp[0] == 0 and int(temp[1]) == 0):
        temp[1] = "20"
    us_h['commute']['duration'] = str(temp[0]) + '.' + str(temp[1])
    temp = us_h['commute']['leave_home'].split('.')
    us_h['commute']['leave_home'] = temp[0] + '.' + temp[1]
    temp = us_h['commute']['leave_work'].split('.')
    us_h['commute']['leave_work'] = temp[0] + '.' + temp[1]
    us_h['commute']['distance'] = us_h['commute']['distance'].replace("km", "")
    try:
        us_h['commute']['distance'] = float(us_h['commute']['distance'])
    except ValueError:
        us_h['commute']['distance'] = 3.0
    if us_h['commute']['days_per_week'] > 6:
        us_h['commute']['days_per_week'] = 6
    if us_h['sex'] == 'M':
        us_h['sex'] = 1
    elif us_h['sex'] == 'F':
        us_h['sex'] = 0
    else:
        us_h['sex'] = random.randint(0, 1)

    if us_h['activities'] == "":
        us_h['activities'] = "tutti i giorni alle 12"  # test
    us_h['trips'] = extract_auto_activities(str(us_h['activities']))
    us_h['trips'] = extract_working_trips(us_h['commute'], us_h['trips'])
    us_h['trips'] = resolve_conflicts(us_h['trips'])
    us_h['trips'] = assign_walking(us_h['trips'])
    us_h['trips'] = split_midnight_trips(us_h['trips'])
    us_h['trips'] = add_home_state(us_h['trips'])
    us_h['trips'] = sort_trips(us_h['trips'])
    #print(us_h['trips'], "")
    us_h['trips'] = merge_dicts(us_h['trips'])

    return us_h


def regolize_frequency(frequency):
    """ Attribuisce un numero alla frequenza testuale """

    if frequency == "Sempre":
        n = 1.0
    elif frequency == "Spesso":
        n = 0.75
    elif frequency == "Qualche volta":
        n = 0.50
    elif frequency == "Raramente":
        n = 0.25
    elif frequency == "Mai":
        n = 0.0
    else:
        n = 0.0
    return n


# Funzione per generare i dati dei sensori basati sulle abitudini
def generate_sensor_data(user_habits, start_date, end_date):
    """ Genera dati sintetici basati sulle abitudini dell'utente e simula i valori dei sensori """
    current_time = start_date
    sensor_data = []
    while current_time <= end_date:
        day_of_week = current_time.strftime('%A').lower()

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
                wifi = 0  # Connected to work Wi-Fi during working hours
            elif habit['wifi_home'] and 19 <= current_time.hour < 23 and day_of_week in ['saturday', 'sunday']:
                wifi = 0  # Connected to home Wi-Fi in the evening and weekends

        # Add noise and false positives
        if random.random() > 0.95:  # 5% chance of error
            motion_sensor = 1 - motion_sensor
            gps = 1 - gps

        # Create the sensor data row
        sensor_data.append([
            'user' + "1",  # User ID
            current_time.year, current_time.month, current_time.day, current_time.hour, current_time.minute,
            day_of_week,
            current_time.strftime('%Y-%m-%d %H.%M:%S'),
            wifi, bluetooth, battery, motion_sensor, gps, accelerometer, cell_change, carplay_android_auto
        ])

        current_time += timedelta(minutes=5)  # Increment the timestamp by one minute

    return sensor_data


# csv_file_path = 'a.csv'
csv_file_path = "C:/Users/Account2/PycharmProjects/AiLab_Lessons/Tirocinio/csv/a.csv "
# csv_file_path = "Tirocinio/csv/a.csv"

df = pd.read_csv(csv_file_path, delimiter=',')
debug_row = pd.DataFrame([[
    "", "", "Android", "Si", "Spesso", "Oggi", "Dipende", "Mai", "Si", "Sempre", "Cavo", "Mai", "Qualche volta",
    "Accendisigari", "Si", "Sempre", "Sempre", "3", "0.10.00", 0.0, "9.00.00", "19.30.00", "Si",
    "Domenica alle 23.59", "M", "21"
    # Aggiungi valori per tutte le colonne del tuo DataFrame
]], columns=df.columns)
df = pd.concat([debug_row, df], ignore_index=True)

user_habits = extract_user_habits(df)
# Definizione dell'intervallo di tempo

start_date = datetime(2024, 1, 1, 0, 0)
end_date = datetime(2024, 1, 2, 23, 59)

# Generazione dei dati sintetici per ogni utente
all_sensor_data = []
for habits in user_habits:
    sensor_data = generate_sensor_data([habits], start_date, end_date)
    all_sensor_data.extend(sensor_data)

with open('csv/out.csv', 'w', newline='') as csvfile:
    # Salvataggio in un file CSV
    # with open('Tirocinio/csv/out.csv', 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(
        ['UserID', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Day of week', 'Wi-Fi', 'Bluetooth', 'Charger',
         'MotionSensor', 'GPS', 'CellChange', 'CarPlay_AndroidAuto', 'BLE', 'State'])
    csvwriter.writerows(all_sensor_data)
# %%
