from machine import Pin, ADC
import dht, time

# Pin definitions
DHT_PIN       = 0
PHOTO_RES_PIN = 27  # ADC pin

# Sensor init
dht_sensor        = dht.DHT11(Pin(DHT_PIN))
photo_res         = ADC(PHOTO_RES_PIN)
board_temp_sensor = ADC(4)


def dht_read():
    try:
        time.sleep(2)
        dht_sensor.measure()
        return dht_sensor.temperature(), dht_sensor.humidity()
    except Exception as e:
        print("DHT11 read error:", e)
        return None, None


def board_temp_read():
    try:
        voltage    = board_temp_sensor.read_u16() * (3.3 / 65535.0)
        temp       = 27 - (voltage - 0.706) / 0.001721
        return round(temp, 2)
    except Exception as e:
        print("Board temp read error:", e)
        return None


def light_level_read():
    try:
        return round(photo_res.read_u16() / 65535 * 100, 1)
    except Exception as e:
        print("Light level read error:", e)
        return None