import re
import random
from datetime import datetime, timedelta

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
    sigma = (range*2)/6  # Deviazione standard

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
            for day in random.sample(days, min(total_slots, len(days))):  # 8 volte -> 7 volte
                if about:
                    time_ab = time_about(normalized_time, 20)
                else:
                    time_ab = time_about(normalized_time, 10)
                day_time[day].append(time_ab)
                total_slots -= 1
    return day_time

def extract_days_times(t):
    """ Cattura i principali pattern e attribuisce gli orari ai giorni"""
    t = normalize_text(t)
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

# Test
texts = [
    
    "Tutti i sabati mattina dalle 11 fino alle 13\nTutti i sabati mattina dalle 15 alle 17\nTutti i venerdì sera dalle 21 alle 22",
    "Ogni giorno alle 08:00",
    "Tre volte alla settimana alle 20:30",
    "Tutti i mercoledi alle 15:45",
    "Quasi tutte le domeniche alle 09:00",
    "Cinque volte a settimana alle 17:30 circa",
    "Ogni venerdi alle 19:00",
    "Quasi tutti i giorni alle 06:30 circa",
    "Tutti i sabati alle 14:00",
    "Due volte a settimana alle 21:15",
    "Ogni martedi e giovedi alle 10:00",
    "Quattro volte alla settimana alle 22:00",
    "Quasi ogni giorno alle 07:45",
    "Tutti i lunedi alle 18:30",
    "Tre volte a settimana alle 12:15 circa",
    "Ogni mercoledi e venerdi alle 08:30",
    "Tutti i giorni alle 13:00",
    "Quasi tutti i sabati alle 16:00",
    "Cinque volte a settimana alle 11:00",
    "Ogni giovedi alle 09:30",
    "Quasi tutte le domeniche alle 19:45",
    "Due volte alla settimana alle 20:00",
    "Ogni martedi alle 14:30",
    "Tre volte alla settimana alle 15:00",
    "Quasi ogni giorno alle 17:00 circa",
    "Tutti i venerdi alle 07:15",
    "Quasi tutti i giorni alle 18:15 circa",
    "Ogni sabato alle 12:00",
    "Cinque volte a settimana alle 10:45",
    "Ogni lunedi alle 08:15"
]

for text in texts:
    users = []
    n_weeks = 1  # possono essere aumentate le settimane generate ricalcolando le casualità
    user_habits = []
    for _ in range(n_weeks):
        user_habits.append(extract_days_times(text))
    users.append(user_habits)
    print(user_habits)
