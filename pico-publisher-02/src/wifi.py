import network
import time


def connect_wifi(ssid, password, timeout=45):
    try:
        network.country("RO")
    except Exception:
        pass

    try:
        ap = network.WLAN(network.AP_IF)

        if ap.active():
            print("Stopping setup Access Point...")
            ap.active(False)
            time.sleep(1)
    except Exception as e:
        print("Could not stop AP:", e)

    wlan = network.WLAN(network.STA_IF)

    try:
        wlan.active(False)
        time.sleep(1)
    except Exception:
        pass

    wlan.active(True)
    time.sleep(2)

    if wlan.isconnected():
        print("Already connected:", wlan.ifconfig())
        return wlan

    try:
        wlan.disconnect()
        time.sleep(1)
    except Exception:
        pass

    print("Connecting to Wi-Fi:", ssid)
    wlan.connect(ssid, password)

    start = time.time()
    last_status = None

    while not wlan.isconnected():
        status = wlan.status()

        if status != last_status:
            print("Wi-Fi status:", status)
            last_status = status


        if status < 0:
            raise RuntimeError(
                "Wi-Fi connection failed, status={}".format(status)
            )

        if time.time() - start > timeout:
            raise RuntimeError(
                "Wi-Fi connection timeout, last status={}".format(status)
            )

        time.sleep(1)

    print("Wi-Fi connected:", wlan.ifconfig())
    return wlan
