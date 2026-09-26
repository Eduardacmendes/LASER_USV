import json
import socket
import threading
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import (
    Imu, MagneticField, Temperature, Range, Illuminance,
    FluidPressure, RelativeHumidity, NavSatFix, BatteryState,
)
from geometry_msgs.msg import Vector3Stamped, QuaternionStamped

SERVER_HOST = 'localhost'
SERVER_PORT = 8765


class BoatSensorNode(Node):
    def __init__(self):
        super().__init__('boat_sensor_node')

        self.imu_pub = self.create_publisher(Imu, '/boat/imu', 10)
        self.mag_pub = self.create_publisher(MagneticField, '/boat/mag', 10)
        self.gravity_pub = self.create_publisher(Vector3Stamped, '/boat/gravity', 10)
        self.linaccel_pub = self.create_publisher(Vector3Stamped, '/boat/linear_acceleration', 10)
        self.rotvec_pub = self.create_publisher(QuaternionStamped, '/boat/rotation_vector', 10)
        self.temp_pub = self.create_publisher(Temperature, '/boat/temperature', 10)
        self.prox_pub = self.create_publisher(Range, '/boat/proximity', 10)
        self.light_pub = self.create_publisher(Illuminance, '/boat/light', 10)
        self.pressure_pub = self.create_publisher(FluidPressure, '/boat/pressure', 10)
        self.humidity_pub = self.create_publisher(RelativeHumidity, '/boat/humidity', 10)
        self.gps_pub = self.create_publisher(NavSatFix, '/boat/gps/fix', 10)
        self.battery_pub = self.create_publisher(BatteryState, '/boat/battery_state', 10)

        self._thread = threading.Thread(target=self._socket_loop, daemon=True)
        self._thread.start()
        self.get_logger().info('boat_sensor_node pronto, conectando ao sensor_server...')

    def _socket_loop(self):
        while rclpy.ok():
            try:
                sock = socket.create_connection((SERVER_HOST, SERVER_PORT), timeout=10)
                sock.settimeout(15)
                self.get_logger().info('Conectado ao sensor_server.')
                buf = b""
                while rclpy.ok():
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    buf += chunk
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        try:
                            self._process_snapshot(json.loads(line.decode()))
                        except Exception as e:
                            self.get_logger().warn(f'Snapshot invalido: {e}')
            except Exception as e:
                self.get_logger().warn(f'Sem conexao com sensor_server ({e}). Retentando em 3s...')
                time.sleep(3)

    def _stamp(self):
        return self.get_clock().now().to_msg()

    def _process_snapshot(self, snap):
        stamp = self._stamp()

        accel, gyro = snap.get("accel"), snap.get("gyro")
        if accel and gyro:
            msg = Imu()
            msg.header.stamp = stamp
            msg.header.frame_id = 'imu_link'
            msg.linear_acceleration.x, msg.linear_acceleration.y, msg.linear_acceleration.z = (float(v) for v in accel)
            msg.angular_velocity.x, msg.angular_velocity.y, msg.angular_velocity.z = (float(v) for v in gyro)
            msg.orientation.w = 1.0
            self.imu_pub.publish(msg)

        mag = snap.get("mag")
        if mag:
            msg = MagneticField()
            msg.header.stamp = stamp
            msg.header.frame_id = 'imu_link'
            msg.magnetic_field.x, msg.magnetic_field.y, msg.magnetic_field.z = (float(v) * 1e-6 for v in mag)
            self.mag_pub.publish(msg)

        gravity = snap.get("gravity")
        if gravity:
            msg = Vector3Stamped()
            msg.header.stamp = stamp
            msg.header.frame_id = 'imu_link'
            msg.vector.x, msg.vector.y, msg.vector.z = (float(v) for v in gravity)
            self.gravity_pub.publish(msg)

        linaccel = snap.get("linear_acceleration")
        if linaccel:
            msg = Vector3Stamped()
            msg.header.stamp = stamp
            msg.header.frame_id = 'imu_link'
            msg.vector.x, msg.vector.y, msg.vector.z = (float(v) for v in linaccel)
            self.linaccel_pub.publish(msg)

        rotvec = snap.get("rotation_vector")
        if rotvec and len(rotvec) >= 4:
            msg = QuaternionStamped()
            msg.header.stamp = stamp
            msg.header.frame_id = 'imu_link'
            msg.quaternion.x, msg.quaternion.y, msg.quaternion.z, msg.quaternion.w = (float(v) for v in rotvec[:4])
            self.rotvec_pub.publish(msg)

        temp = snap.get("temperature")
        if temp:
            msg = Temperature()
            msg.header.stamp = stamp
            msg.header.frame_id = 'ambient_link'
            msg.temperature = float(temp[0])
            self.temp_pub.publish(msg)

        prox = snap.get("proximity")
        if prox:
            msg = Range()
            msg.header.stamp = stamp
            msg.header.frame_id = 'proximity_link'
            msg.radiation_type = Range.INFRARED
            msg.field_of_view = 1.0
            msg.min_range = 0.0
            msg.max_range = 5.0
            msg.range = float(prox[0])
            self.prox_pub.publish(msg)

        light = snap.get("light")
        if light:
            msg = Illuminance()
            msg.header.stamp = stamp
            msg.header.frame_id = 'light_link'
            msg.illuminance = float(light[0])
            self.light_pub.publish(msg)

        pressure = snap.get("pressure")
        if pressure:
            msg = FluidPressure()
            msg.header.stamp = stamp
            msg.header.frame_id = 'pressure_link'
            msg.fluid_pressure = float(pressure[0]) * 100.0
            self.pressure_pub.publish(msg)

        humidity = snap.get("humidity")
        if humidity:
            msg = RelativeHumidity()
            msg.header.stamp = stamp
            msg.header.frame_id = 'humidity_link'
            msg.relative_humidity = float(humidity[0]) / 100.0
            self.humidity_pub.publish(msg)

        gps = snap.get("gps")
        if gps:
            msg = NavSatFix()
            msg.header.stamp = stamp
            msg.header.frame_id = 'gps_link'
            msg.latitude = float(gps.get('latitude', 0.0))
            msg.longitude = float(gps.get('longitude', 0.0))
            msg.altitude = float(gps.get('altitude', 0.0))
            self.gps_pub.publish(msg)

        battery = snap.get("battery")
        if battery:
            msg = BatteryState()
            msg.header.stamp = stamp
            msg.header.frame_id = 'battery_link'
            msg.percentage = float(battery.get('percentage', 0)) / 100.0
            msg.voltage = float(battery.get('voltage', 0)) / 1000.0
            msg.power_supply_status = (
                BatteryState.POWER_SUPPLY_STATUS_CHARGING
                if battery.get('status') == 'CHARGING'
                else BatteryState.POWER_SUPPLY_STATUS_DISCHARGING
            )
            self.battery_pub.publish(msg)


def main():
    rclpy.init()
    node = BoatSensorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()