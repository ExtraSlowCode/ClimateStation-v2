import _thread
import network
import ntptime
import machine
from time import sleep, localtime
from state import state
from sensors import dht_read, board_temp_read, light_level_read
from storage import append_reading, read_csv
from server import start_server
import keys


POLL_INTERVAL = 600  # 10 minutes


# Pin setup
send_led  = machine.Pin(15, machine.Pin.OUT)
board_led = machine.Pin("LED", machine.Pin.OUT)


def lit(pin, on):
    pin.on() if on else pin.off()


def timestamp_iso():
    t = localtime()
    return f"{t[0]}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"

def timestamp_display():
    t = localtime()
    return f"{t[0]}-{t[1]:02d}-{t[2]:02d}\t{t[3]:02d}:{t[4]:02d}:{t[5]:02d} UTC (Sthlm is UTC +1/+2)"


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    network.hostname("climatestation")
    wlan.connect(keys.SSID, keys.PSWD)
    while not wlan.isconnected():
        lit(board_led, True)
        print("Connecting to WiFi...")
        sleep(1)
        lit(board_led, False)
    ip = wlan.ifconfig()[0]
    print(f"Connected to {keys.SSID} — {ip}")
    return ip


def http_get_portal():
    import socket, time
    url = "http://detectportal.firefox.com/"
    _, _, host, path = url.split("/", 3)
    addr = socket.getaddrinfo(host, 80)[0][-1]
    s = socket.socket()
    s.connect(addr)
    s.send(bytes(f"GET /{path} HTTP/1.0\r\nHost: {host}\r\n\r\n", "utf8"))
    time.sleep(1)
    s.recv(10000)
    s.close()


def ensure_wifi():
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        print("WiFi lost — reconnecting...")
        wlan.disconnect()
        wlan.connect(keys.SSID, keys.PSWD)
        for _ in range(20):
            if wlan.isconnected():
                print("WiFi restored —", wlan.ifconfig()[0])
                return True
            sleep(1)
        print("WiFi reconnect failed — rebooting")
        machine.reset()
        return False
    return True


def startup():
    lit(send_led, False)
    lit(board_led, False)

    # Blink on startup
    for i in range(6):
        lit(send_led, i % 2 == 0)
        sleep(0.5)

    connect_wifi()
    http_get_portal()       # WiFi stability fix
    lit(board_led, True)    # WiFi up indicator

    try:
        ntptime.settime()
        print("NTP sync OK —", timestamp_display())
    except Exception as e:
        print("NTP sync failed:", e)


def sensor_loop():
    while True:
        ensure_wifi()
        temp_dht, humidity  = dht_read()
        temp_board          = board_temp_read()
        light               = light_level_read()
        ts_iso     = timestamp_iso()
        ts_display = timestamp_display()

        if None not in (temp_dht, humidity, temp_board, light):
            state.update(temp_dht, humidity, temp_board, light, ts_display)
            append_reading(ts_iso, temp_dht, humidity, temp_board, light)
            
            lit(send_led, True)
            print(f"READ data: DHT {temp_dht}C, {humidity}%\t board {temp_board}C\t light {light}\t at:{ts_display}")
            sleep(0.1)
            lit(send_led, False)
        else:
            print(f"{ts_display} — partial read failure, skipping append")

        sleep(POLL_INTERVAL)


# Boot
startup()

# Server on second thread, sensor loop on main
_thread.start_new_thread(start_server, (state, read_csv, "0.0.0.0", 80))
sensor_loop()