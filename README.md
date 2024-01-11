# ClimaCare

ClimaCare is a project that aims to improve the way people interact with diverse climate indicators in Bilbao. For that, the solution will implement several IoT systems over the city to obtain and preprocess data that will be used for creating useful, user-oriented climate recommendations. This GitHub repository contains the Python code we have used to develop the solution. It contains code oriented to extract data from the sensors and additional open data sources, as well as training data for preprocessing and creating the recommendations.

# Prerequisites 📋

To ensure the proper functioning of the code, there are some steps you must follow before running the file.

**1.  Install the following Python libraries**

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

**2.	Download and start InfluxDB server**

After downloading and installing InfluxDB on your machine (https://docs.influxdata.com/influxdb/v2/install/), you can start the server with this command:

```
influxd
```

**3.	Download and start Grafana Server**

After downloading the Grafana Server (https://grafana.com/docs/grafana/latest/setup-grafana/installation/), open a command prompt and type the following code:

```
sudo systemctl start grafana-server
```

**4.	Modify tokens in the main program ("climacare.py")**

You must set your InfluxDB token in the "climacare.py" file. In our case, we configured an environment variable for it. For that, add your token here:

```
token = INFLUXDB_TOKEN
```

You must also change the Weatherstack token and use your own.

**5.	Execute the file**

Execute "climacare.py" in the command prompt

```
python3 climacare.py
```

## Built with🛠️

For this project, we have used the following tools:

1.  Python 3: https://docs.python.org/es/3/tutorial/

2.  Raspberry Pi: https://www.raspberrypi.com/

3.  InfluxDB: https://www.influxdata.com/

4.  Grafana: https://grafana.com/

## Wiki 📖

You can find much more on how to use this project and about the sensors we have used on our [Wiki](https://github.com/juanorts/ClimaCare/wiki).

## Authors ✒️

* Andoni Okariz Apaolaza (https://github.com/AndoniOka)
* Juan Orts Madina (https://github.com/juanorts)
