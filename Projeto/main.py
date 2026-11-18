
import os
import sys
import logging

# Diretório onde está o main.py
projeto_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(projeto_path)

if projeto_path not in sys.path:
    sys.path.insert(0, projeto_path)

# Importar módulos do projeto
from mqtt_bridge import MqttFuzzyBridge

# Configurações MQTT
os.environ["MQTT_HOST"] = "broker.hivemq.com"
os.environ["MQTT_PORT"] = "1883"
os.environ["MQTT_TELEMETRY_TOPIC"] = "grupo4/esp32/telemetry"
os.environ["MQTT_LEVEL_TOPIC"] = "grupo4/fuzzy/level"
os.environ["MQTT_COMMAND_TOPIC"] = "grupo4/ac/command"
os.environ["MQTT_PUBLISH_INTERVAL"] = "60"

# Configuração de logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

print("Iniciando servidor de integração MQTT...")

try:
    bridge_server = MqttFuzzyBridge()

    print("Aguardando telemetrias da ESP32 física...")

    bridge_server.run()

except KeyboardInterrupt:
    print("\nServidor encerrado pelo usuário.")

except Exception as e:
    print(f"\nFalha crítica no servidor: {e}")
