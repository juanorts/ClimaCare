import requests

params = {
  'access_key': '721a04984f62bbfc8900c300327807bb',
  'type': 'Ip',
  'query': '130.206.138.233',
  'units': 'm',
}

api_response1 = requests.get('http://api.weatherstack.com/current', params)
response1 = api_response1.json()

api_response2 = requests.get('https://air-quality-api.open-meteo.com/v1/air-quality?latitude=43.270097&longitude=-2.938766&current=alder_pollen,birch_pollen,grass_pollen,mugwort_pollen,olive_pollen,ragweed_pollen&domains=cams_europe')
response2 = api_response2.json()

print("Wind speed: " + str(response1['current']['wind_speed']) + " kmph")
print("UV: " + str(response1['current']['uv_index']) + " (Index)")

print("Pollen concentrations:" + "\n" + "\tAlder: " + str(response2['current']['alder_pollen']) + " grains/m³" + "\n" + "\tBirch: " + str(response2['current']['birch_pollen']) + " grains/m³" + "\n" + "\tGrass: " + str(response2['current']['grass_pollen']) + " grains/m³" + "\n" + "\tMugwort: " + str(response2['current']['mugwort_pollen']) + " grains/m³" + "\n" + "\tOlive: " + str(response2['current']['olive_pollen']) + " grains/m³" + "\n" + "\tRagweed: " + str(response2['current']['ragweed_pollen']) + " grains/m³")