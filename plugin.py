# Domoticz-Toyota-Plugin
#
# Author: John de Rooij
#
"""
<plugin key="Toyota" name="Toyota" author="joro75" version="0.1.0" externallink="https://github.com/joro75/Domoticz-Toyota-Plugin">
    <description>
        <h2>Domoticz Toyota Plugin 0.1.0</h2>
        <p>
        A Domoticz plugin that provides sensors for a Toyota car with connected services.
        </p>
        <p>
        It is using the same API that is used by the Toyota MyT connected services. This API is however only useable
        for cars that are purchased in Europe. For more information of Toyota MyT see: 
        <a href="https://www.toyota-europe.com/service-and-accessories/my-toyota/myt">
        https://www.toyota-europe.com/service-and-accessories/my-toyota/myt</a>
        </p>
        <p>
        The Toyota car should first be made available in the MyT connected services, after which this plugin
        can retrieve the information, which is then provided as several sensors in Domoticz.
        </p>
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Retrieve actual mileage</li>
            <li>Retrieve actual fuel level percentage</li>
        </ul>
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li>Mileage - The actual mileage of the car</li>
            <li>Fuel level - The actual fuel level of the car</li>
            <li>Distance to home - The actual distance between the car and home</li>
        </ul>
        <h3>Configuration</h3>
        <ul style="list-style-type:square">
            <li>Username - The username that is also used to login in the myT application.</li>
            <li>Password - The password that is also used to login in the myT application.</li>
            <li>Locale - The locale that should be used. This can be for example 'nl-nl' or another locale. 'en-us' doesn't seem to work!</li>
            <li>Car - An identifier for the car for which the data should be retrieved, if multiple cars are present in the myT application.
            It can be a part of the VIN number, alias, licenseplate or the model.</li>
        </ul>
    </description>
    <params>
        <param field="Username" label="Username" width="200px" required="true"/>
        <param field="Password" label="Password" width="200px" required="true" password="true"/>
        <param field="Mode1" label="Locale" width="200px" required="false" default="en-us"/>
        <param field="Mode2" label="Car" width="200px" required="false" />
    </params>
</plugin>
"""

import Domoticz
import json
import asyncio
import mytoyota
from mytoyota.client import MyT
import mytoyota.exceptions
import geopy.distance

UNIT_MILEAGE_INDEX: int = 1

UNIT_FUEL_INDEX: int = 2

UNIT_DISTANCE_INDEX: int = 3

class ToyotaPlugin:
    def __init__(self):
        self._heartbeatCount = 100
        self._loggedOn = False
        self._lastMileage = 0
        return

    def onStart(self):
        print(Devices)
        if not UNIT_MILEAGE_INDEX in Devices or Devices[UNIT_MILEAGE_INDEX] is None:
            Domoticz.Device(Name="Mileage", Unit=UNIT_MILEAGE_INDEX, 
                            TypeName="Counter Incremental", Switchtype=3,
                            Used=1,
                            Description="Counter to hold the overall mileage",
                            Options={"ValueUnits": "km",
                                     "ValueQuantity": "km"}
                            ).Create()
        if not UNIT_FUEL_INDEX in Devices or Devices[UNIT_FUEL_INDEX] is None:
            Domoticz.Device(Name="Fuel level", Unit=UNIT_FUEL_INDEX, 
                            TypeName="Percentage",
                            Used=1,
                            Description="The filled percentage of the fuel tank"
                            ).Create()
        if not UNIT_DISTANCE_INDEX in Devices or Devices[UNIT_DISTANCE_INDEX] is None:
            Domoticz.Device(Name="Distance to home", Unit=UNIT_DISTANCE_INDEX, 
                            TypeName="Custom Sensor", Type=243, Subtype=31,
                            Options={'Custom': '1;km'},
                            Used=1,
                            Description="The distance between home and the car"
                            ).Create()

        Domoticz.Debugging(1)
        DumpConfigToLog()

        self._homeLocation = Settings['Location']
                
        # Retrieve the last mileage that is already known in Domoticz
        if UNIT_MILEAGE_INDEX in Devices and not Devices[UNIT_MILEAGE_INDEX] is None:
            self._lastMileage = int(Devices[UNIT_MILEAGE_INDEX].sValue)
        
        
        self._client = MyT(username=Parameters["Username"],
                           password=Parameters["Password"],
                           locale=Parameters["Mode1"],
                           region="europe")
        self._loop = asyncio.get_event_loop()
        try:
            self._loop.run_until_complete(self._client.login())
            self._loggedOn = True
        except mytoyota.exceptions.ToyotaLoginError as ex:
            Domoticz.Log(str(ex))
        # TODO: Handle other logon errors and exceptions
        if self._loggedOn:
            Domoticz.Log("Succesfully logged on")
            cars = self._loop.run_until_complete(self._client.get_vehicles())
            self._car = self._lookupCar(cars)
            if self._car is None:
                Domoticz.Error("Could not find the desired car in the MyT information")

    def _lookupCar(self, cars):
        if len(Parameters["Mode2"]) > 0:
            id = Parameters["Mode2"].upper().strip()
            for car in cars:
                if id in car.get('alias', '').upper():
                    return car
                if id in car.get('licensePlate', '').upper():
                    return car
                if id in car.get('vin', '').upper():
                    return car
                if id in car.get('modelName', '').upper():
                    return car
        return cars[0]
        
    def onStop(self):
        self._client = None
        if self._loop:
            self._loop.close()

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")
                
    def onHeartbeat(self):
        self._heartbeatCount += 1
        if self._heartbeatCount > 10:
            self._heartbeatCount = 0
            if self._loggedOn:
                if self._loop:
                    if self._car:
                        Domoticz.Log("Updating vehicle status")
                        vehicle = self._loop.run_until_complete(self._client.get_vehicle_status(self._car))
                        if not vehicle.odometer is None:
                            if UNIT_MILEAGE_INDEX in Devices:
                                mileage = vehicle.odometer.mileage
                                diff = mileage - self._lastMileage
                                if diff != 0:
                                    Devices[UNIT_MILEAGE_INDEX].Update(nValue=0, sValue=f'{diff}')
                                    self._lastMileage = mileage
                            if UNIT_FUEL_INDEX in Devices:
                                fuel = vehicle.odometer.fuel
                                Devices[UNIT_FUEL_INDEX].Update(nValue=int(fuel), sValue=str(fuel))

                            if UNIT_DISTANCE_INDEX in Devices:
                                if len(self._homeLocation) > 0:
                                    coords_home = tuple([float(part) for part in self._homeLocation.split(';')])
                                    coords_car = (float(vehicle.parking.latitude), float(vehicle.parking.longitude))
                                    dist = geopy.distance.distance(coords_home, coords_car).km
                                    # Round it to meters.
                                    dist = round(dist, 3)
                                    Devices[UNIT_DISTANCE_INDEX].Update(nValue=0, sValue=f'{dist}')
                            
global _plugin
_plugin = ToyotaPlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
    