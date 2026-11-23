import time
import sys
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from fuzzy_controller import temperature_centroid

# Credenciais de acesso ao seu InfluxDB na AWS
INFLUX_HOST = "http://3.135.246.204:8086"
INFLUX_TOKEN = "tcc-david-aws-2026-token"
INFLUX_ORG = "minha_org"
INFLUX_BUCKET = "wsn"

def integrar_fuzzy_com_dados_reais(intervalo_segundos=10):
    """
    Consome dados reais do InfluxDB, filtra ruídos indesejados,
    aplica o motor de inferência Fuzzy de Zadeh (1965) e grava o controle de volta.
    """
    print(f"Iniciando Integração Fuzzy em Tempo Real com o InfluxDB ({intervalo_segundos}s)...\n")
    
    client = InfluxDBClient(url=INFLUX_HOST, token=INFLUX_TOKEN, org=INFLUX_ORG)
    query_api = client.query_api()
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    # Query Flux otimizada para buscar as medições reais das últimas 2 horas
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -30d)
      |> filter(fn: (r) => r["_measurement"] == "wsn" or r["_measurement"] == "controle_sala" or r["_measurement"] == "controle")
      |> filter(fn: (r) => r["_field"] == "t")
      |> last()
    '''
    
    try:
        while True:
            result = query_api.query(org=INFLUX_ORG, query=query)
            
            leituras_reais = []
            for table in result:
                for record in table.records:
                    val = record.get_value()
                    if val is not None:
                        temp = float(val)
                        # Aplicação prática do filtro de sanidade (GSA): ignora falhas de sensores (-50°C ou 150°C)
                        if 10.0 <= temp <= 45.0:
                            leituras_reais.append(temp)
            
            if leituras_reais:
                # Média das medições físicas válidas encontradas no banco de dados
                temperatura_media = sum(leituras_reais) / len(leituras_reais)
                
                # Executa a inferência matemática baseada na composição Max-Min de Zadeh
                resultado_fuzzy = temperature_centroid(temperatura_media)
                payload = resultado_fuzzy.to_control_payload(int(time.time() * 1000))
                nivel_controle = float(payload.get('level', 0.0))
                
                print(f"Temperatura Média: {temperatura_media:.2f}°C | Nível Fuzzy Calculado: {nivel_controle:.2f}%")
                
                # Gravação robusta de volta ao InfluxDB na medição 'controle_fuzzy'
                ts_ms = int(time.time() * 1000)
                ponto_controle = Point("controle_fuzzy") \
                    .field("temperatura_media", temperatura_media) \
                    .field("nivel_controle", nivel_controle) \
                    .time(ts_ms, WritePrecision.MS)
                
                write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=ponto_controle)
                print("   ✓ Decisão gravada com sucesso no InfluxDB (medida: controle_fuzzy).")
            else:
                print("[ALERTA] Nenhuma temperatura real válida encontrada na última janela de tempo.")
                
            sys.stdout.flush()
            time.sleep(intervalo_segundos)
            
    except KeyboardInterrupt:
        print("\nIntegração contínua interrompida pelo usuário.")
    finally:
        client.close()

# Ativa a integração
integrar_fuzzy_com_dados_reais(intervalo_segundos=10)