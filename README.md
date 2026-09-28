# LASER USV Smartphone - Sensor Bridge

Código que pega os sensores de um celular Android (via Termux:API) e publica em tópicos ROS 2. Depende do ambiente configurado no repositório `laser_usv_smartphone_setup`.

## Prerequisites

- ROS 2 Humble instalado e configurado (repositório `laser_usv_smartphone_setup`)
- Python 3.10+
- Termux:API instalado no Android, com permissões de sensores/localização/bateria concedidas
- `ros-humble-sensor-msgs` instalado dentro do proot

## Como funciona

São dois arquivos, cada um rodando de um lado:

- **`sensor_server.py`** roda no Termux nativo, fora do proot. Não é um nó ROS 2 — só chama `termux-sensor`, `termux-location` e `termux-battery-status` e manda os valores por um socket TCP na porta 8765.
- **`boat_sensor_node.py`** roda dentro do proot. Esse sim é um nó ROS 2 de verdade (`rclpy`), aparece em `ros2 node list`. Ele se conecta no `sensor_server.py` pelo socket e publica os tópicos `/boat/*`.

Por que essa separação: os comandos `termux-sensor` etc. só existem fora do proot, e o ROS 2 só existe dentro dele. O proot isola o sistema de arquivos mas não a rede, então o socket local resolve a comunicação entre os dois lados.

## Installation

Copiar os arquivos pro celular (via `adb`, do computador):

```bash
adb root
adb push sensor_server.py /data/data/com.termux/files/home/sensor_server.py
adb push boat_sensor_node.py /data/data/com.termux/files/home/boat_sensor_node.py
```

O `boat_sensor_node.py` ainda precisa ser copiado pra dentro do proot (rodar isso fora do proot, no Termux nativo):

```bash
proot-distro login ubuntu -- bash -c "cat > boat_sensor_node.py" < boat_sensor_node.py
```

## Getting started

Terminal 1, no Termux nativo:

```bash
python sensor_server.py
```
Mostra `[server] escutando em 0.0.0.0:8765`.

Terminal 2, dentro do proot:

```bash
proot-distro login ubuntu
source /opt/ros/humble/setup.bash
python3 boat_sensor_node.py
```
Mostra `Conectado ao sensor_server.`.

Terminal 3, dentro do proot, pra conferir que está tudo publicando:

```bash
source /opt/ros/humble/setup.bash
ros2 node list        # /boat_sensor_node
ros2 topic list        # os tópicos /boat/*
ros2 topic echo /boat/imu
```

## Topics

| Tópico | Tipo | O que é |
| :--- | :--- | :--- |
| `/boat/imu` | `sensor_msgs/Imu` | orientação, velocidade angular, aceleração linear |
| `/boat/mag` | `sensor_msgs/MagneticField` | magnetômetro |
| `/boat/gravity` | `geometry_msgs/Vector3Stamped` | vetor gravidade |
| `/boat/linear_acceleration` | `geometry_msgs/Vector3Stamped` | aceleração linear isolada |
| `/boat/rotation_vector` | `geometry_msgs/QuaternionStamped` | quaternion de orientação |
| `/boat/temperature` | `sensor_msgs/Temperature` | temperatura ambiente |
| `/boat/proximity` | `sensor_msgs/Range` | proximidade |
| `/boat/light` | `sensor_msgs/Illuminance` | luz |
| `/boat/pressure` | `sensor_msgs/FluidPressure` | pressão atmosférica |
| `/boat/humidity` | `sensor_msgs/RelativeHumidity` | umidade relativa |
| `/boat/gps/fix` | `sensor_msgs/NavSatFix` | latitude/longitude/altitude |
| `/boat/battery_state` | `sensor_msgs/BatteryState` | estado da bateria |

No emulador, Giroscópio, Proximidade, Luz, Temperatura e Umidade voltam com valor fixo (placeholder) — não é bug do código, é limitação do AVD. Dado real só sai testando no celular físico.
