# CryptoTracker

This is an example of how you can create a desktop application with PyQT6 Python library. 

## Use case:

1. You have a portfolio csv file with some Crypto assets and quantity
2. You upload this portfolio file to the app
3. Applications hits Kraken api, gets information on current asset's price, and updates value of your porfolio for each asset
4. You can then download the updated portfolio file

## Building options:

#### To run locally as an exe application

First of all `pyinstaller` should be installed:

```
    pip install pyinstaller
```
Once it's installed we can build the application.

Linux/Mac command:

```
pyinstaller --onefile --add-data "config.ini:." crypto_tracker.py
```

Windows command:

```
pyinstaller --onefile --add-data "config.ini;." crypto_tracker.py
```

The `dist` folder will be created with the application file


#### To run anywhere as a docker container

Building image:
```commandline
docker build -t crypto_tracker:0.0.1 .
```

Running image:
```commandline
docker run --shm-size=2g -d -p 8080:6901 crypto_tracker:0.0.1
```

Once launched, go to your browser and hit, password will be headless:
```commandline
localhost:8080
```






## View

![Default output](https://github.com/kolyaiks/crypto_tracker/blob/master/images/screenshot.png)

