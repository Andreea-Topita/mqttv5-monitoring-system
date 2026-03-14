import psutil

def get_system_metric(topic: str) -> str:
    if topic == "Cpu load":
        return f"CPU Load: {psutil.cpu_percent()}%"

    elif topic == "Memory usage":
        return f"Memory Usage: {psutil.virtual_memory().percent}%"

    elif topic == "Disk usage":
        try:
            disk_usage = psutil.disk_usage('/')
            return f"Disk Usage: {disk_usage.used / (1024**3):.2f} GB"
        except Exception as e:
            return f"Error disk usage: {e}"

    return "Unknown topic"