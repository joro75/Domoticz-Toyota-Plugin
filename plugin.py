# Copyright (C) 2021 John de Rooij
#
# This software is licensed as described in the file LICENSE, which
# you should have received as part of this distribution.
#
# Domoticz-Toyota-Plugin   ( https://github.com/joro75/Domoticz-Toyota-Plugin )
#
# CodingGuidelines 2020-04-11 
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
            <li>Locked - The actual status if the car is locked or unlocked</li>
        </ul>
        <h3>Configuration</h3>
        <ul style="list-style-type:square">
            <li>Username - The username that is also used to login in the myT application.</li>
            <li>Password - The password that is also used to login in the myT application.</li>
            <li>Locale - The locale that should be used. This can be for example 'en-gb' or another locale. 'en-us' doesn't seem to work!</li>
            <li>Car - An identifier for the car for which the data should be retrieved, if multiple cars are present in the myT application.
            It can be a part of the VIN number, alias, licenseplate or the model.</li>
        </ul>
    </description>
    <params>
        <param field="Username" label="Username" width="200px" required="true"/>
        <param field="Password" label="Password" width="200px" required="true" password="true"/>
        <param field="Mode1" label="Locale" width="200px" required="false" default="en-gb"/>
        <param field="Mode2" label="Car" width="200px" required="false" />
    </params>
</plugin>
"""

import sys
import json
import asyncio

global _importErrors
_importErrors = ''

try:
    import Domoticz
except ImportError:
    _importErrors += ('The Python Domoticz library is not installed. '
                      'This plugin can only be installed in Domoticz. Check your Domoticz installation')
    
try:
    import mytoyota
    from mytoyota.client import MyT
    import mytoyota.exceptions
except ImportError:
    _importErrors += ('The Python mytoyota library is not installed. '
                      'Use pip to install mytoyota: pip3 install -r requirements.txt')

try:
    import geopy.distance
except ImportError:
    _importErrors += ('The python geopy library is not installed. '
                      'Use pip to install geopy: pip3 install -r requirements.txt')
                   
MINIMUM_PYTHON_VERSION = (3, 6)
DO_DOMOTICZ_DEBUGGING: bool = False
    
UNIT_MILEAGE_INDEX: int = 1

UNIT_FUEL_INDEX: int = 2

UNIT_DISTANCE_INDEX: int = 3

UNIT_CAR_LOCKED_INDEX: int = 4

class ToyotaPlugin:
    """Domoticz plugin function implementation to get information from Toyota MyT."""
    
    def __init__(self):
        self._heartbeat_count = 100
        self._logged_on = False
        self._last_mileage = 0
        self._last_fuel = 0
        self._coordinates_home = None
        return
    
    def _lookup_car(self, cars, identifier):
        """Find and eturn the first car from cars that confirms to the passed identifier."""
        if not cars is None and len(identifier) > 0:
            id = identifier.upper().strip()
            for car in cars:
                if id in car.get('alias', '').upper():
                    return car
                if id in car.get('licensePlate', '').upper():
                    return car
                if id in car.get('vin', '').upper():
                    return car
                if id in car.get('modelName', '').upper():
                    return car
        return None

    def _connect_to_MyT(self):
        """Connect to the Toyota MyT servers."""
        self._logged_on = False
        self._loop = asyncio.get_event_loop()
        cars = None
        try:
            self._client = MyT(username=Parameters['Username'],
                               password=Parameters['Password'],
                               locale=Parameters['Mode1'],
                               region='europe')
            self._loop.run_until_complete(self._client.login())
            cars = self._loop.run_until_complete(self._client.get_vehicles())
            self._logged_on = True
        except mytoyota.exceptions.ToyotaLoginError as ex:
            Domoticz.Error(f'Login Error: {ex}')
        except mytoyota.exceptions.ToyotaInvalidUsername as ex:
            Domoticz.Error(f'Invalid username: {ex}')
        if self._logged_on:
            Domoticz.Log('Succesfully logged on')
            self._car = self._lookup_car(cars, Parameters['Mode2'])
            if self._car is None:
                self._car = self._lookup_car(cars, Parameters['Name'])
            if self._car is None:
                Domoticz.Error('Could not find the desired car in the MyT information')
        else:
            Domoticz.Error('Logon failed')
            
    def _ensure_connected(self):
        """Check and return if a connection to Toyota MyT servers is present, also trying to connect."""
        if not self._is_connected():
            self._connect_to_MyT()
        return self._is_connected()
        
    def _is_connected(self):
        """Check and return if a connection to Toyota MyT servers is present."""
        connected = False
        if self._logged_on:
            if self._loop:
                if self._car:
                    connected = True
        return connected

    def _retrieve_vehicle_status(self):
        """Retrieve and return the status information of the vehicle."""
        vehicle = None
        if self._ensure_connected():
            Domoticz.Log('Updating vehicle status')
            try:
                vehicle = self._loop.run_until_complete(self._client.get_vehicle_status(self._car))
            except mytoyota.Exceptions.ToyotaInternalError:
                pass
        if vehicle is None:
            Domoticz.Error('Vehicle status could not be retrieved')    
        return vehicle
            
    def _update_sensors(self):
        """Retreive the status of the vehicle and update the Domoticz sensors."""
        vehicle = self._retrieve_vehicle_status()
        if not vehicle is None:
            if not vehicle.odometer is None:
                if UNIT_MILEAGE_INDEX in Devices:
                    mileage = vehicle.odometer.mileage
                    diff = mileage - self._last_mileage
                    if diff != 0:
                        Devices[UNIT_MILEAGE_INDEX].Update(nValue=0, sValue=f'{diff}')
                        self._last_mileage = mileage
                if UNIT_FUEL_INDEX in Devices:
                    fuel = vehicle.odometer.fuel
                    if fuel != self._last_fuel:
                        Devices[UNIT_FUEL_INDEX].Update(nValue=int(float(fuel)), sValue=str(fuel))
                        self._last_fuel = fuel
            
            if not vehicle.parking is None:
                if not self._coordinates_home is None:
                    if UNIT_DISTANCE_INDEX in Devices:
                        coords_car = (float(vehicle.parking.latitude), float(vehicle.parking.longitude))
                        dist = geopy.distance.distance(self._coordinates_home, coords_car).km
                        # Round it to meters.
                        dist = round(dist, 3)
                        Devices[UNIT_DISTANCE_INDEX].Update(nValue=0, sValue=f'{dist}')
            
            if not vehicle.status.doors is None:
                if UNIT_CAR_LOCKED_INDEX in Devices:
                    locked = True
                    for door in vehicle.status.doors.as_dict():
                        try:
                            locked = locked and door.get('locked', True)
                        except AttributeError:
                            pass
                    state = 1 if locked else 0
                    Devices[UNIT_CAR_LOCKED_INDEX].Update(nValue=state, sValue=str(state))
                            
    def _create_devices(self):
        """Create the appropiate sensors in Domoticz for the vehicle."""
        vehicle = self._retrieve_vehicle_status()
        if not vehicle is None:
            if not UNIT_MILEAGE_INDEX in Devices or Devices[UNIT_MILEAGE_INDEX] is None:
                Domoticz.Device(Name='Mileage', Unit=UNIT_MILEAGE_INDEX, 
                                TypeName='Counter Incremental', Switchtype=3,
                                Used=1,
                                Description='Counter to hold the overall mileage',
                                Options={'ValueUnits': 'km',
                                         'ValueQuantity': 'km'}
                                ).Create()
            if not UNIT_FUEL_INDEX in Devices or Devices[UNIT_FUEL_INDEX] is None:
                Domoticz.Image('ToyotaFuelMeter.zip').Create()
                Domoticz.Device(Name='Fuel level', Unit=UNIT_FUEL_INDEX, 
                                TypeName='Percentage',
                                Used=1,
                                Description='The filled percentage of the fuel tank',
                                Image=Images['ToyotaFuelMeter'].ID
                                ).Create()
            if not UNIT_DISTANCE_INDEX in Devices or Devices[UNIT_DISTANCE_INDEX] is None:
                Domoticz.Device(Name='Distance to home', Unit=UNIT_DISTANCE_INDEX, 
                                TypeName='Custom Sensor', Type=243, Subtype=31,
                                Options={'Custom': '1;km'},
                                Used=1,
                                Description='The distance between home and the car'
                                ).Create()
            if not UNIT_CAR_LOCKED_INDEX in Devices or Devices[UNIT_CAR_LOCKED_INDEX] is None:
                Domoticz.Image('ToyotaLocked.zip').Create()
                Domoticz.Device(Name='Locked', Unit=UNIT_CAR_LOCKED_INDEX,
                                TypeName='Light/Switch', Type=244, Subtype=73, Switchtype=19,
                                Used=1,
                                Description='The locked/unlocked state of the car',
                                Image=Images['ToyotaLocked'].ID
                                ).Create()    
                                
    def onStart(self):
        """Callback from Domoticz that the plugin is started."""
        if DO_DOMOTICZ_DEBUGGING:
            Domoticz.Debugging(1)
            DumpConfigToLog()

        self._coordinates_home = None
        if len(Settings['Location']) > 0:
            try:
                self._coordinates_home = tuple([float(part) for part in Settings['Location'].split(';')])
            except ValueError:
                pass
                            
        self._create_devices()
                
        # Retrieve the last mileage that is already known in Domoticz
        if UNIT_MILEAGE_INDEX in Devices and not Devices[UNIT_MILEAGE_INDEX] is None:
            try:
                self._last_mileage = int(Devices[UNIT_MILEAGE_INDEX].sValue)
            except ValueError:
                self._last_mileage = 0
        if UNIT_FUEL_INDEX in Devices and not Devices[UNIT_FUEL_INDEX] is None:
            try:
                self._last_fuel = float(Devices[UNIT_FUEL_INDEX].sValue)
            except ValueError:
                self._last_fuel = 0
                        
    def onStop(self):
        """Callback from Domoticz that the plugin is stopped."""
        self._client = None
        if self._loop:
            self._loop.close()

    def onHeartbeat(self):
        """Callback from Domoticz that the plugin can perform some work."""
        self._heartbeat_count += 1
        if self._heartbeat_count > 10:
            self._heartbeat_count = 0
            self._update_sensors()
                                                
global _plugin
_plugin = ToyotaPlugin()

def onStart():
    """Callback from Domoticz that the plugin is started."""
    if sys.version_info < MINIMUM_PYTHON_VERSION:
        Domoticz.Error(f'Python version {sys.version_info} is not supported, at least {MINIMUM_PYTHON_VERSION} is required.')
    else:
        global _importErrors
        if _importErrors:
            Domoticz.Error(_importErrors)
        else:
            global _plugin
            _plugin.onStart()

def onStop():
    """Callback from Domoticz that the plugin is stopped."""
    global _plugin
    _plugin.onStop()

def onHeartbeat():
    """Callback from Domoticz that the plugin can perform some work."""
    global _plugin
    _plugin.onHeartbeat()

def DumpConfigToLog():
    """Dump the configuration of the plugin to the Domoticz debug log."""
    for x in Parameters:
        if Parameters[x] != '':
            value = '******' if x.lower() in ['username', 'password'] else str(Parameters[x])
            Domoticz.Debug( "'" + x + "': '" + value + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
    