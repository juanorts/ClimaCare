# ClimaCare Bilbao
ClimaCare is a project that aims to improve the way people interact with diverse climate indicators in Bilbao. For that, the solution will implement several IoT systems over the city to obtain and preprocess data that will be used for creating useful, user-oriented climate recommendations. This GitHub repository contains the Python code we have used for developing the solution. It contains code oriented to extract data from the sensors, as well as data for preprocessing and creating the recommendations.
# Before the execution 📋
To ensure the proper functioning of the code, there are some steps you must follow before running the file:
1.  Install the following libraries:
```
pip install pigpio   
```
```
pip install seeed-python-dht
```
```
pip install pandas
```
```
pip install -U scikit-learn
```
```
pip install influxdb-client
```
2.	Download and start InfluxDB server:
After downloading InfluxDB on your machine (you can find it here: https://docs.influxdata.com/influxdb/v2/install/?t=Windows), you must access its path and execute the following in the command prompt:
```
influxd 
```
3.	Download and start Grafana Server:
After downloading the Grafana Server, open a command prompt and type the following code:
```
sudo systemctl start grafana-server
```
4.	Modify "climacare.py":
You must set your InfluxDB token in the "climacare.py" file. For that, add your token here:
```
 token = INFLUXDB_TOKEN
```
5.	Execute the file:
Execute "climacare.py" in the command prompt
```
python3 climacare.py
```

## Built with🛠️
For this project, we have used the following tools:

Python 3: https://docs.python.org/es/3/tutorial/
Raspberry Pi: https://www.raspberrypi.com/
InfluxDB: https://www.influxdata.com/
Grafana: https://grafana.com/

## Wiki 📖
You can find much more on how to use this project and about the sensors we have used on our Wiki.

## Authors ✒️
* Juan Orts Madina
* Andoni Okariz Apaolaza
