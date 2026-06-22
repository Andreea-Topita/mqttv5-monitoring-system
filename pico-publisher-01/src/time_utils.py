import time

try:
    import ntptime
except ImportError:
    ntptime = None


# diferenta exacta, in secunde, dintre 1970-01-01 si 2000-01-01
# unele placi MicroPython folosesc anul 2000 ca timp de pornire pentru time.time()
EPOCH_2000_OFFSET = 946684800


def sync_time():
    # sincronizeaza ora placii prin internet, folosind NTP
    # timestamp-ul trimis in SenML este cat mai apropiat de timpul real
    if ntptime is None:
        print("NTP not available. Using local Pico time.")
        return False

    try:
        ntptime.settime()
        print("Time synchronized:", time.localtime())
        return True
    except Exception as e:
        print("NTP sync failed:", e)
        return False


def get_unix_time():
    # returneaza timpul in format Unix timestamp: numar de secunde de la 1970-01-01
    current_time = time.time()

    # detectam automat epoch-ul folosit de placa
    # daca time.gmtime(0) incepe cu anul 2000, convertim la Unix timestamp
    epoch_year = time.gmtime(0)[0]

    if epoch_year == 2000:
        return int(current_time + EPOCH_2000_OFFSET)

    return int(current_time)