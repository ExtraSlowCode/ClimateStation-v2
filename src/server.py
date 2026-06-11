import socket

def _ascii_bar(value, max_val, width=20):
    filled = int((value / max_val) * width)
    filled = max(0, min(filled, width))
    return "█" * filled + "░" * (width - filled)

def _sparkline(values):
    if not values:
        return "  (no data yet)"

    min_v = min(values)
    max_v = max(values)
    span  = max_v - min_v if max_v != min_v else 1

    bars   = "▁▂▃▄▅▆▇█"
    result = []
    for v in values:
        idx = int((v - min_v) / span * (len(bars) - 1))
        result.append(bars[idx])

    lines = []
    # lines.append(f"{max_v:5.1f}% ┐")
    lines.append("│ " + "".join(result))
    # lines.append(f"{min_v:5.1f}% ┘")
    lines.append("└" + "─" * len(result))
    lines.append(" " + "48h ago" + " " * (len(result) - 10) + "now")
    return "\n".join(lines)

def _load_light_history(csv_data, max_points=288):
    rows   = csv_data.strip().split("\n")
    values = []
    for row in rows[1:]:
        parts = row.split(",")
        if len(parts) >= 5:
            try:
                values.append(float(parts[4]))
            except:
                pass
    values = values[-max_points:]
    return values[::4] # every 4 points only to squish graph a bit

def _build_page(s, csv_data):
    temp_dht    = s["temp_dht"]
    humidity    = s["humidity"]
    temp_board  = s["temp_board"]
    light_level = s["light_level"]
    updated     = s["last_updated"]

    bar_temp_dht   = _ascii_bar(temp_dht,   100)
    bar_humidity   = _ascii_bar(humidity,   100)
    bar_temp_board = _ascii_bar(temp_board, 100)
    bar_light      = _ascii_bar(light_level, 100)

    spark = _sparkline(_load_light_history(csv_data))
    spark_1, spark_2, spark_3 = spark.split("\n") # graph line VS x axis line VS x axis titles line

    return f"""HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="refresh" content="60">
                <title>ClimateStation</title>
                <style>
                    body {{ background:#0d0d0d; color:#c8c8c8; font-family:monospace; padding:2rem; }}
                    h1 {{ color:#ffffff; }}
                    pre {{ line-height:1.6; }}
                    pre.scroll {{ overflow-x:auto; white-space:pre; }}
                    a {{ color:#5af; }}
                </style>
            </head>
            <body>
                <h1>ClimateStation</h1>
                <pre>
                    Last updated: {updated}
                    Refresh:      every 60s

                    [DHT-11]
                      Temp      {temp_dht} C\t{bar_temp_dht}
                      Humidity  {humidity} %\t{bar_humidity}

                    [Board]
                      Temp      {temp_board} C\t{bar_temp_board}

                    [Light]
                      Level     {light_level} %\t{bar_light}
                </pre>
                <pre class="scroll">
                    [Daylight — last 48h]
                      {spark_1}
                      {spark_2}
                      {spark_3}
                </pre>
                <a href="/history.csv">Download history.csv</a>
            </body>
            </html>"""

def _handle(conn, state, get_csv):
    try:
        conn.settimeout(5)
        req = conn.recv(1024).decode()
        if "GET /history.csv" in req:
            conn.send(
                "HTTP/1.0 200 OK\r\n"
                "Content-Type: text/csv\r\n"
                "Content-Disposition: attachment; filename=\"history.csv\"\r\n"
                "\r\n"
            )
            conn.send(get_csv())
        else:
            conn.send(_build_page(state.snapshot(), get_csv()))
    except Exception as e:
        print("Server handle error:", e)
    finally:
        conn.close()

def start_server(state, get_csv, host, port):
    addr = socket.getaddrinfo(host, port)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    s.settimeout(10)
    print(f"Server listening on {host}:{port}")
    while True:
        try:
            conn, _ = s.accept()
            _handle(conn, state, get_csv)
        except OSError:
            pass # retry upon timeouts
        except Exception as e:
            print("Server loop error:", e)