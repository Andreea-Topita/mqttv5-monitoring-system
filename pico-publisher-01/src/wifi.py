import network
import time


def connect_wifi(ssid, password, timeout=30):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    time.sleep(1)

    if wlan.isconnected():
        print("Already connected:", wlan.ifconfig())
        return wlan

    print("Connecting to Wi-Fi:", ssid)
    wlan.connect(ssid, password)

    start = time.time()

    while not wlan.isconnected():
        status = wlan.status()
        print("Wi-Fi status:", status)

        if time.time() - start > timeout:
            raise RuntimeError("Wi-Fi connection timeout")

        time.sleep(1)

    print("Wi-Fi connected:", wlan.ifconfig())
    return wlan
