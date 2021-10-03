# Domoticz-Toyota-Plugin 0.8.0
A Domoticz plugin that provides sensors for a Toyota car with connected services.

It is using the same API that is used by the Toyota MyT connected services. This API is however only useable
for cars that are purchased in Europe. For more information on Toyota MyT see:
https://www.toyota-europe.com/service-and-accessories/my-toyota/myt</a>

The Toyota car should first be made available in the MyT connected services, after which this plugin
can retrieve the information, which is then provided as several sensors in Domoticz.

## Features
* Retrieve actual mileage
* Retrieve actual fuel level percentage
* Shows the distance between the car and home
* Shows the locked / unlocked state of the car

## Dependencies
This plugin uses the '[mytoyota](https://github.com/DurgNomis-drol/mytoyota)' library to communicatie with the Toyota
servers. Also the 'geopy' library is used to calculate distances.

All these dependencies can be installed by using the command
```text
# pip3 install -r requirements.txt
```

## Credits

A huge thanks goes to [@DurgNomis-drol](https://github.com/DurgNomis-drol/) for making [mytoyota](https://github.com/DurgNomis-drol/mytoyota).

The following icons from the [Noun Project](https://thenounproject.com) are used:
* [fuel meter](https://thenounproject.com/search/?q=fuel+meter&i=2690780#) by Phonlaphat Thongsriphong from the Noun Project
* [unlocked](https://thenounproject.com/andrejs/collection/view-thin/?i=3863254) by Andrejs Kirma from the Noun Project
* [locked](https://thenounproject.com/search/?q=car+locked&i=3863407#) by Andrejs Kirma from the Noun Project
