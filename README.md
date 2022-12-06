# Domoticz-Toyota-Plugin 0.9.1
[![PyPI pyversions](https://img.shields.io/badge/python-3.7-blue.svg)]() [![Plugin version](https://img.shields.io/badge/version-0.9.1-red.svg)](https://github.com/joro75/Domoticz-Toyota-Plugin/branches)

A [Domoticz][domoticz] plugin that provides devices for a [Toyota][toyota] car with connected services.

Be aware that since version 0.9.1 also an update of [mytoyota][mytoyota] to version 0.8.1 is required, so ensure that
also the [mytoyota][mytoyota] Python module is updated!

This plugin is using the same API that is used by the Toyota MyT connected services
app. This API is however only useable for cars that are purchased in Europe.
For more information on Toyota MyT see the [Austrian][MyT_Austrian],
[Belgian][MyT_Belgian], [British][MyT_British], [Danish][MyT_Danish],
[Dutch][MyT_Dutch], [European][MyT_European], [French][MyT_French],
[German][MyT_German], [Italian][MyT_Italian], [Spanish][MyT_Spanish] or
[Swiss][MyT_Swiss] website.

The Toyota car should first be made available in the MyT connected services
app, after which this plugin can retrieve the information, which is then provided as several
devices in Domoticz.

## Provided devices
| Device           | Image                                                                                                                                                 | Description                                          |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| Mileage          | <img src='https://github.com/joro75/Domoticz-Toyota-Plugin/raw/main/resources/device_mileage.png' width='353' alt='Mileage device'>                   | Shows the daily and total mileage                    |
| Fuel level       | <img src='https://github.com/joro75/Domoticz-Toyota-Plugin/raw/main/resources/device_fuel_level.png' width='353' alt='Fuel level device'>             | Shows the actual fuel level percentage               |
| Distance to home | <img src='https://github.com/joro75/Domoticz-Toyota-Plugin/raw/main/resources/device_distance_to_home.png' width='353' alt='Distance to home device'> | Shows the distance between the car and home          |
| Locked           | <img src='https://github.com/joro75/Domoticz-Toyota-Plugin/raw/main/resources/device_locked_locked.png' width='353' alt='Locked device'>              | Shows if the car is locked or unlocked               |
| Parking location | <img src='https://github.com/joro75/Domoticz-Toyota-Plugin/raw/main/resources/device_parking_location.png' width='353' alt='Parking location device'> | Shows the address of the parking location of the car |
| Consumed fuel    | <img src='https://github.com/joro75/Domoticz-Toyota-Plugin/blob/main/resources/device_consumed_fuel.png' width='353' alt='Consumed fuel device'>      | Shows the consumed fuel in l/100 km                  |
| Accelerations    |                                                                                                                                                       | Shows the number of hard accelerations               |
| Brakes           |                                                                                                                                                       | Shows the number of hard brakes                      |
| Duration         |                                                                                                                                                       | Shows the total driving duration in seconds          |
| Idle             |                                                                                                                                                       | Shows the total standstill duration in seconds       |

## Installation and Setup
- a running Domoticz installation, tested with version 2021.1 and Python 3.7
- Python >= 3.7
- clone project
    - go to `domoticz/plugins` directory
    - clone the project
        ```bash
        cd domoticz/plugins
        git clone https://github.com/joro75/Domoticz-Toyota-Plugin.git
        ```
- or just download, unzip and copy to `domoticz/plugins`
- install needed python modules:
   - [mytoyota][mytoyota] Version 0.8.1
   - [geopy](https://github.com/geopy/geopy) Version 2.2.0
   - setuptools Version >= 57.0.0
   - for an automated install of these, you can use `sudo pip3 install -r requirements.txt`
- restart Domoticz service
- Now go to **Setup**, **Hardware** in your Domoticz interface. There add the **Toyota** plugin.
- Configure the username and password that is also used for the Toyota MyT connected services.
- If one or more errors are detected during the start of the plugin, this will be reported as errors in the Domoticz log.

### Settings
| Parameter   | Information                                                                                                                                                                                  |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| username    | The username that is also used to login in the MyT application                                                                                                                               |
| password    | The password that is also used to login in the MyT application.                                                                                                                              |
| car         | An identifier for the car for which the data should be retrieved, if multiple cars are present in the myT application. It can be a part of the VIN number, alias, licenseplate or the model. |

## Credits
A huge thanks goes to [@DurgNomis-drol](https://github.com/DurgNomis-drol/) for making [mytoyota](https://github.com/DurgNomis-drol/mytoyota).

The following icons from the [Noun Project](https://thenounproject.com) are used:
* [fuel meter](https://thenounproject.com/search/?q=fuel+meter&i=2690780#) by Phonlaphat Thongsriphong from the Noun Project
* [unlocked](https://thenounproject.com/andrejs/collection/view-thin/?i=3863254) by Andrejs Kirma from the Noun Project
* [locked](https://thenounproject.com/search/?q=car+locked&i=3863407#) by Andrejs Kirma from the Noun Project

## State and development
The current version is working for my situation, and a few others. It will be impossible for me to test the plugin with every Toyota car model
as there is a large variation in the provided data for each Toyota car and they also can have own specific options. However most of the functionality should
be working. The number of provided devices is not complete yet, and future updates will add additional devices.

This plugin is using pre-commit. If you would like to contribute an improvement, fork this repository and
create a new branch, which includes the improvements. Before making a PR, please run `pre-commit run --all-files`
and make sure that all tests are passing before requesting the PR.

[MyT_Austrian]: https://www.toyota.at/owners/myt-and-multimedia
[MyT_Belgian]: https://nl.toyota.be/naverkoop/connected-services/myt
[MyT_British]: https://www.toyota.co.uk/owners/servicing-and-aftercare/my-toyota/myt-and-connected-services
[MyT_Danish]: https://www.toyota.dk/toyota-ejere/din-toyota/myt-connected-services
[MyT_Dutch]: https://www.toyota.nl/toyota-rijders/connected-services1/myt
[MyT_European]: https://www.toyota-europe.com/service-and-accessories/my-toyota/myt
[MyT_French]: https://www.toyota.fr/ma-toyota/application-myt
[MyT_German]: https://www.toyota.de/service_und_zubehoer/myt
[MyT_Italian]: https://www.toyota.it/clienti/multimedia/myt-servizi-connessi
[MyT_Spanish]: https://www.toyota.es/servicios-conectados-myt
[Myt_Swiss]: https://fr.toyota.ch/owners/myt-app-multimedia
[mytoyota]: https://github.com/DurgNomis-drol/mytoyota
[toyota]: https://global.toyota/en/
[domoticz]: https://www.domoticz.com/
