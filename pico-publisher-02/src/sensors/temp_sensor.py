from machine import Pin
import dht


class TempSensor:
    def __init__(self, gpio_pin=20):
        self.sensor = dht.DHT11(Pin(gpio_pin))

    def read(self):
        self.sensor.measure()
        temp = self.sensor.temperature()
        hum = self.sensor.humidity()
        return temp, hum


