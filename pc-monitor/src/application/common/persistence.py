def persist_safely(action_name: str, callback, *args, **kwargs):
    try:
        callback(*args, **kwargs)
    except Exception as e:
        print(f"Persistence error during {action_name}: {e}")