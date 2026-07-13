# daca baza de date are o problema, nu vrem sa se opreasca procesarea mesajelor, ci doar sa afisam un mesaj de eroare in consola si sa continuam
def persist_safely(action_name: str, callback, *args, **kwargs):
    try:
        return callback(*args, **kwargs)    # apeleaza callback ul cu parametrii dati si returneaza rezultatul, se salveaza in kwargs parametrii
    except Exception as e:
        print(f"Persistence error during {action_name}: {e}")
        return None
# callback apeleaza functia data ca parametru, cu parametrii dati ca args si kwargs, 
# si returneaza rezultatul, daca apare o exceptie, afiseaza un mesaj de eroare in consola si returneaza None
# o eroare de persistenta sa opreasca fluxul