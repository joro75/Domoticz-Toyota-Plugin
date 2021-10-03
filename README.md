# Domoticz-Toyota-Plugin 0.8.0
[![PyPI pyversions](https://img.shields.io/badge/python-3.7-blue.svg)]() [![Plugin version](https://img.shields.io/badge/version-0.8.0-red.svg)](https://github.com/joro75/Domoticz-Toyota-Plugin/branches)

A Domoticz plugin that provides devices for a Toyota car with connected services.

It is using the same API that is used by the Toyota MyT connected services
app. This API is however only useable for cars that are purchased in Europe.
For more information on Toyota MyT see:
[https://www.toyota-europe.com/service-and-accessories/my-toyota/myt](https://www.toyota-europe.com/service-and-accessories/my-toyota/myt)

The Toyota car should first be made available in the MyT connected services
app, after which this plugin can retrieve the information, which is then provided as several
devices in Domoticz.

## Provided devices
| Device           | Image                                                                                                                                                 | Description                                  |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| Mileage          | <img src='https://github.com/joro75/Domoticz-Toyota-Plugin/raw/main/resources/device_mileage.png' width='353' alt='Mileage device'>                   | Show actual mileage                          |
| Fuel level       | <img src='https://github.com/joro75/Domoticz-Toyota-Plugin/raw/main/resources/device_fuel_level.png' width='353' alt='Fuel level device'>             | Show actual fuel level percentage            |
| Distance to home | <img src='https://github.com/joro75/Domoticz-Toyota-Plugin/raw/main/resources/device_distance_to_home.png' width='353' alt='Distance to home device'> | Shows the distance between the car and home  |
| Locked           | <img src='https://github.com/joro75/Domoticz-Toyota-Plugin/raw/main/resources/device_locked_locked.png' width='353' alt='Locked device'>              | Shows the locked / unlocked state of the car |

## Installation and Setup
- a running Domoticz installation, tested with version 2021.1 and Python 3.7
- Python >= 3.6
- install needed python modules:
   - [mytoyota](https://github.com/DurgNomis-drol/mytoyota) Version 0.6.2
   - [geopy](https://github.com/geopy/geopy) Version 2.2.0
   - you can use `sudo pip3 install -r requirements.txt`
- clone project
    - go to `domoticz/plugins` directory
    - clone the project
        ```bash
        cd domoticz/plugins
        git clone https://github.com/joro75/Domoticz-Toyota-Plugin.git
        ```
- or just download, unzip and copy to `domoticz/plugins`
- no need on Raspbian for sys path adaption if using sudo for pip3
- restart Domoticz service
- Now go to **Setup**, **Hardware** in your Domoticz interface. There add **Toyota Plugin**.

### Settings
| Parameter   | Information                                                                                                                                                                                  |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| username    | The username that is also used to login in the MyT application                                                                                                                               |
| password    | The password that is also used to login in the MyT application.                                                                                                                              |
| locale      | The locale that should be used. This can be for example 'en-gb' or another locale. 'en-us' doesn't seem to work!                                                                             |
| car         | An identifier for the car for which the data should be retrieved, if multiple cars are present in the myT application. It can be a part of the VIN number, alias, licenseplate or the model. |

## Credits
A huge thanks goes to [@DurgNomis-drol](https://github.com/DurgNomis-drol/) for making [mytoyota](https://github.com/DurgNomis-drol/mytoyota).

The following icons from the [Noun Project](https://thenounproject.com) are used:
* [fuel meter](https://thenounproject.com/search/?q=fuel+meter&i=2690780#) by Phonlaphat Thongsriphong from the Noun Project
* [unlocked](https://thenounproject.com/andrejs/collection/view-thin/?i=3863254) by Andrejs Kirma from the Noun Project
* [locked](https://thenounproject.com/search/?q=car+locked&i=3863407#) by Andrejs Kirma from the Noun Project

## State and development
The current version is working for my situation. It however is not tested yet by other users, but it should
be working. The number of provided devicess is not complete yet, and future updates will add additional devices.

This plugin is using pre-commit. If you would like to contribute an improvement, fork this repository and
create a new branch. Before making a PR, please run `pre-commit run --all-files` and make sure that all
tests passes locally first.
