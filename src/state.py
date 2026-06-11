import _thread

class SharedState:
    def __init__(self):
        self.lock = _thread.allocate_lock()
        self.temp_dht    = 0.0
        self.humidity    = 0
        self.temp_board  = 0.0
        self.light_level = 0.0
        self.last_updated = "never"

    def update(self, temp_dht, humidity, temp_board, light_level, timestamp):
        with self.lock:
            self.temp_dht    = temp_dht
            self.humidity    = humidity
            self.temp_board  = temp_board
            self.light_level = light_level
            self.last_updated = timestamp

    def snapshot(self):
        with self.lock:
            return {
                "temp_dht":    self.temp_dht,
                "humidity":    self.humidity,
                "temp_board":  self.temp_board,
                "light_level": self.light_level,
                "last_updated": self.last_updated
            }

# Single instance, imported everywhere
state = SharedState()