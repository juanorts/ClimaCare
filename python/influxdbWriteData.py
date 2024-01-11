import os
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
INFLUXDB_TOKEN=os.getenv('INFLUX_TOKEN')

token = INFLUXDB_TOKEN
org = "ClimaCare"
url = "http://localhost:8086"

client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)

bucket="climacare-db"

write_api = client.write_api(write_options=SYNCHRONOUS)
   
#data = influxdb_client.Point("Medicion").tag("Ubicacion", "Puente de Deusto").field("temperture",10.2).field("humedad", 60.6).field("UV", 3)

#recommendationStr = "Llevar una chaqueta aislante de alta calidad para mantenerse abrigado;Vestir con una capa intermedia entre la camisa y el abrigo;Cubrir el cuello y cabeza, y usar guantes para las manos;"

data = influxdb_client.Point("measure").tag("location", "Universidad de Deusto").field("temperture", 9.3).field("humidity", 67.6).field("windspeed", 65.0).field("pressure", 1003.4).field("uv", 5.0).field("air_quality", 53.4).field("air_quality_index", "Peligroso").field("pollen", "Bajo")
write_api.write(bucket=bucket, org=org, record=data)

#data = influxdb_client.Point("measure").tag("location", "Universidad de Deusto").field("recommendations", "Vestir con una capa intermedia entre la camisa y el abrigo")
#write_api.write(bucket=bucket, org=org, record=data)