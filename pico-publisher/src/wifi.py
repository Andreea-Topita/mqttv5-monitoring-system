import network
import time


def connect_wifi(ssid: str, password: str, timeout: int = 15):
    wlan = network.WLAN(network.WLAN.IF_STA)
    wlan.active(True)

    if wlan.isconnected():
        return wlan

    print("Connecting to Wi-Fi...")
    wlan.connect(ssid, password)

    start = time.time()
    while not wlan.isconnected():
        if time.time() - start > timeout:
            raise RuntimeError("Wi-Fi connection timeout")
        time.sleep(1)

    print("Wi-Fi connected:", wlan.ifconfig())
    return wlan