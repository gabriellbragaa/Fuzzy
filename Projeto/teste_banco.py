
import os
from influxdb_client import InfluxDBClient

# Configure as credenciais nas variáveis de ambiente
url = "http://3.135.246.204:8086"
token = "tcc-david-aws-2026-token"
org = "minha_org"
bucket = "wsn"

if not token:
    raise ValueError("Configure a variável de ambiente INFLUX_TOKEN")

query = '''
from(bucket: "wsn")
  |> range(start: -30d)
  |> filter(fn: (r) =>
      r["_measurement"] == "controle" or
      r["_measurement"] == "controle_sala" or
      r["_measurement"] == "wsn"
  )
  |> sort(columns: ["_time"], desc: true)
'''

print("Buscando dados no InfluxDB nos últimos 30 dias...")

try:
    with InfluxDBClient(
        url=url,
        token=token,
        org=org
    ) as client:

        query_api = client.query_api()

        result = query_api.query(
            org=org,
            query=query
        )

        records_found = False

        for table in result:
            for record in table.records:
                records_found = True

                measurement = record.get_measurement()
                timestamp = record.get_time()
                node_id = record.values.get("node_id")
                field = record.get_field()
                value = record.get_value()

                print(
                    f"[Sensor] "
                    f"Tempo: {timestamp} | "
                    f"Measurement: {measurement} | "
                    f"Node: {node_id} | "
                    f"Campo: {field} | "
                    f"Valor: {value}"
                )

        if not records_found:
            print(
                "\nNenhum dado encontrado nos últimos 30 dias. "
                "Verifique se a ESP32 está enviando dados "
                "via MQTT e se o InfluxDB está recebendo."
            )

except Exception as e:
    print(f"\nErro ao consultar o InfluxDB: {e}")
