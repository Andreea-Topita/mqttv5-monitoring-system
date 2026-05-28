def persist_safely(action_name: str, callback, *args, **kwargs):
    try:
        return callback(*args, **kwargs)
    except Exception as e:
        print(f"Persistence error during {action_name}: {e}")
        return None
    
# am nevoie de id ul mesajului salvat in mqtt message ca sa il leg de randul din sensor measurements
