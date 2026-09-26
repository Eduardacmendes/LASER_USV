import json, socket, subprocess, time, threading

HOST = '0.0.0.0'
PORT = 8765
INTERVAL = 1.0

MULTI_SENSORS = (
    "Accelerometer,Gyroscope,Magnetic field,Gravity,"
    "Linear Acceleration,Rotation Vector,Ambient Temperature,"
    "Proximity,Light,Pressure,Humidity"
)

_current_conn_lock = threading.Lock()
_current_conn = [None]  # guardado numa lista pra poder mutar de dentro das threads


def read_multi_sensors(timeout=4):
    """Le varios sensores numa unica chamada do termux-sensor."""
    try:
        out = subprocess.check_output(
            ["termux-sensor", "-s", MULTI_SENSORS, "-n", "1"],
            timeout=timeout, stderr=subprocess.DEVNULL,
        )
        raw = json.loads(out.decode())
        # normaliza: tira o prefixo "Goldfish ..." de cada chave
        result = {}
        for key, val in raw.items():
            result[key] = val.get("values")
        return result
    except Exception as e:
        print(f"[WARN] multi-sensor: {e}")
        return {}


def read_location(timeout=5):
    try:
        out = subprocess.check_output(
            ["termux-location", "-p", "gps", "-r", "once"],
            timeout=timeout, stderr=subprocess.DEVNULL,
        )
        return json.loads(out.decode())
    except Exception:
        return None


def read_battery(timeout=2):
    try:
        out = subprocess.check_output(
            ["termux-battery-status"], timeout=timeout, stderr=subprocess.DEVNULL,
        )
        return json.loads(out.decode())
    except Exception:
        return None


def find_value(sensors_dict, name_substring):
    for key, val in sensors_dict.items():
        if name_substring.lower() in key.lower():
            return val
    return None


def collect_snapshot(gps_every=5, battery_every=5, counter=[0]):
    counter[0] += 1
    sensors = read_multi_sensors()

    snap = {
        "accel": find_value(sensors, "Accelerometer"),
        "gyro": find_value(sensors, "Gyroscope"),
        "mag": find_value(sensors, "Magnetic field"),
        "gravity": find_value(sensors, "Gravity"),
        "linear_acceleration": find_value(sensors, "Linear Acceleration"),
        "rotation_vector": find_value(sensors, "Rotation Vector"),
        "temperature": find_value(sensors, "Temperature"),
        "proximity": find_value(sensors, "Proximity"),
        "light": find_value(sensors, "Light"),
        "pressure": find_value(sensors, "Pressure"),
        "humidity": find_value(sensors, "Humidity"),
        "gps": None,
        "battery": None,
        "timestamp": time.time(),
    }

    # GPS e bateria sao mais lentos/caros; le com menor frequencia
    if counter[0] % gps_every == 0:
        snap["gps"] = read_location()
    if counter[0] % battery_every == 0:
        snap["battery"] = read_battery()

    return snap


def handle_client(conn, addr):
    with _current_conn_lock:
        old = _current_conn[0]
        _current_conn[0] = conn
    if old is not None and old is not conn:
        try:
            old.close()
        except Exception:
            pass

    print(f"[server] cliente conectado: {addr}")
    try:
        while _current_conn[0] is conn:
            line = json.dumps(collect_snapshot()) + "\n"
            conn.sendall(line.encode())
            time.sleep(INTERVAL)
    except (BrokenPipeError, ConnectionResetError, OSError):
        print(f"[server] cliente desconectou: {addr}")
    finally:
        try:
            conn.close()
        except Exception:
            pass


def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(1)
    print(f"[server] escutando em {HOST}:{PORT}")
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()