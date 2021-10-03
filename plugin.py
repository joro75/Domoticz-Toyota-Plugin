# Copyright (C) 2021 John de Rooij
#
# This software is licensed as described in the file LICENSE, which
# you should have received as part of this distribution.
#
# Domoticz-Toyota-Plugin   ( https://github.com/joro75/Domoticz-Toyota-Plugin )
#
# CodingGuidelines 2020-04-11
"""
<plugin key="Toyota" name="Toyota" author="joro75" version="0.1.0"
        externallink="https://github.com/joro75/Domoticz-Toyota-Plugin">
    <description>
        <h2>Domoticz Toyota Plugin 0.1.0</h2>
        <p>
        A Domoticz plugin that provides sensors for a Toyota car with connected services.
        </p>
        <p>
        It is using the same API that is used by the Toyota MyT connected services.
        This API is however only useable for cars that are purchased in Europe.
        For more information of Toyota MyT see:
        <a href="https://www.toyota-europe.com/service-and-accessories/my-toyota/myt">
        https://www.toyota-europe.com/service-and-accessories/my-toyota/myt</a>
        </p>
        <p>
        The Toyota car should first be made available in the MyT connected services,
        after which this plugin can retrieve the information, which is then provided as
        several sensors in Domoticz.
        </p>
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Retrieve mileage, fuel level and locked/unlocked state of the car</li>
            <li>Calculate the distance from the parked car and the home location</li>
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
            <li>Locale - The locale that should be used. This can be for example 'en-gb'
                or another locale. 'en-us' doesn't seem to work!</li>
            <li>Car - An identifier for the car for which the data should be retrieved,
                if multiple cars are present in the myT application.
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
from abc import ABC, abstractmethod
import asyncio
from typing import Any, Union, List, Tuple, Optional

_importErrors = ''  # pylint:disable=invalid-name

try:
    import Domoticz  # type: ignore
except ImportError:
    _importErrors += ('The Python Domoticz library is not installed. '
                      'This plugin can only be used in Domoticz. '
                      'Check your Domoticz installation')

# Fool mypy and pylint that these types are coming from Domoticz
try:
    from Domoticz import Parameters, Devices, Settings, Images
except ImportError:
    pass

try:
    import mytoyota  # type: ignore
    from mytoyota.client import MyT  # type: ignore
    import mytoyota.exceptions  # type: ignore
    import mytoyota.vehicle  # type: ignore
except ImportError:
    _importErrors += ('The Python mytoyota library is not installed. '
                      'Use pip to install mytoyota: pip3 install -r requirements.txt')

try:
    import geopy.distance  # type: ignore
except ImportError:
    _importErrors += ('The python geopy library is not installed. '
                      'Use pip to install geopy: pip3 install -r requirements.txt')

MINIMUM_PYTHON_VERSION = (3, 6)
DO_DOMOTICZ_DEBUGGING: bool = False

UNIT_MILEAGE_INDEX: int = 1

UNIT_FUEL_INDEX: int = 2

UNIT_DISTANCE_INDEX: int = 3

UNIT_CAR_LOCKED_INDEX: int = 4

class ReducedHeartBeat(ABC):
    """Helper class that only calls the update of the sensors every ... heartbeat."""

    _heartbeat_interval: int = 10

    def __init__(self) -> None:
        super().__init__()
        self._heartbeat_count = self._heartbeat_interval

    def onHeartbeat(self) -> None:  # pylint:disable=invalid-name
        """Callback from Domoticz that the plugin can perform some work."""
        self._heartbeat_count += 1
        if self._heartbeat_count > self._heartbeat_interval:
            self._heartbeat_count = 0
            self.update_sensors()

    @abstractmethod
    def update_sensors(self) -> None:
        """Retrieve the status of the device and update the Domoticz sensors."""
        return

class ToyotaMyTConnector():
    """Provide a connection to the Toyota MyT service."""

    def __init__(self) -> None:
        super().__init__()
        self._logged_on = False
        self._loop = asyncio.get_event_loop()
        self._client: MyT = None
        self._car: mytoyota.vehicle.Vehicle = None

    def _lookup_car(self, cars: Optional[List], identifier: str) -> mytoyota.vehicle.Vehicle:    # pylint:disable=no-self-use
        """Find and eturn the first car from cars that confirms to the passed identifier."""
        if not cars is None and identifier:
            car_id = identifier.upper().strip()
            for car in cars:
                if car_id in car.get('alias', '').upper():
                    return car
                if car_id in car.get('licensePlate', '').upper():
                    return car
                if car_id in car.get('vin', '').upper():
                    return car
                if car_id in car.get('modelName', '').upper():
                    return car
        return None

    def _connect_to_myt(self) -> None:
        """Connect to the Toyota MyT servers."""
        self._logged_on = False
        cars: Optional[List[Any]] = None
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

    def _ensure_connected(self) -> bool:
        """
        Check and return if a connection to Toyota MyT servers is present,
        also trying to connect.
        """
        if not self._is_connected():
            self._connect_to_myt()
        return self._is_connected()

    def _is_connected(self) -> bool:
        """Check and return if a connection to Toyota MyT servers is present."""
        connected = False
        if self._logged_on:
            if self._loop:
                if self._car:
                    connected = True
        return connected

    def retrieve_vehicle_status(self) -> Union[Any, None]:
        """Retrieve and return the status information of the vehicle."""
        vehicle = None
        if self._ensure_connected():
            Domoticz.Log('Updating vehicle status')
            try:
                vehicle = self._loop.run_until_complete(self._client.get_vehicle_status(self._car))
            except mytoyota.exceptions.ToyotaInternalError:
                pass
        if vehicle is None:
            Domoticz.Error('Vehicle status could not be retrieved')
        return vehicle

    def disconnect(self) -> None:
        """Disconnect from the Toyota MyT servers."""
        self._client = None
        if self._loop:
            self._loop.close()


class DomoticzSensor(ABC):  # pylint:disable=too-few-public-methods
    """Representation of a generic updateable Domoticz sensor."""

    def __init__(self, unit_index: int) -> None:
        super().__init__()
        self._unit_index = unit_index

    def exists(self) -> bool:
        """Check if the Domoticz sensor is present and existing."""
        return (self._unit_index in Devices) and (Devices[self._unit_index])


class ToyotaDomoticzSensor(DomoticzSensor):
    """
    A generic updateable Domoticz sensor, to represent information from
    a Toyota MyT connected services car.
    """

    @abstractmethod
    def create(self, vehicle_status) -> None:
        """Check if the sensor is present in Domoticz, and otherwise create it."""
        return

    @abstractmethod
    def update(self, vehicle_status) -> None:
        """Determine the actual value of the instrument and update the sensor in Domoticz."""
        return


class MileageToyotaSensor(ToyotaDomoticzSensor):
    """The Domoticz sensor that shows the mileage."""

    def __init__(self) -> None:
        super().__init__(UNIT_MILEAGE_INDEX)
        self._last_mileage: int = 0

    def create(self, vehicle_status) -> None:
        """Check if the sensor is present in Domoticz, and otherwise create it."""
        if vehicle_status:
            if not self.exists():
                Domoticz.Device(Name='Mileage', Unit=self._unit_index,
                                TypeName='Counter Incremental', Switchtype=3,
                                Used=1,
                                Description='Counter to hold the overall mileage',
                                Options={'ValueUnits': 'km',
                                         'ValueQuantity': 'km'}
                                ).Create()

        # Retrieve the last mileage that is already known in Domoticz
        if self.exists():
            try:
                self._last_mileage = int(Devices[self._unit_index].sValue)
            except ValueError:
                self._last_mileage = 0

    def update(self, vehicle_status) -> None:
        """Determine the actual value of the instrument and update the sensor in Domoticz."""
        if vehicle_status and vehicle_status.odometer:
            if self.exists():
                mileage = vehicle_status.odometer.mileage
                diff = mileage - self._last_mileage
                if diff != 0:
                    Devices[self._unit_index].Update(nValue=0, sValue=f'{diff}')
                    self._last_mileage = mileage


class FuelToyotaSensor(ToyotaDomoticzSensor):
    """The Domoticz sensor that shows the fuel level percentage."""

    def __init__(self) -> None:
        super().__init__(UNIT_FUEL_INDEX)
        self._last_fuel: float = 0.0

    def create(self, vehicle_status) -> None:
        """Check if the sensor is present in Domoticz, and otherwise create it."""
        if vehicle_status:
            if not self.exists():
                Domoticz.Image('ToyotaFuelMeter.zip').Create()
                Domoticz.Device(Name='Fuel level', Unit=self._unit_index,
                                TypeName='Percentage',
                                Used=1,
                                Description='The filled percentage of the fuel tank',
                                Image=Images['ToyotaFuelMeter'].ID
                                ).Create()

        if self.exists():
            try:
                self._last_fuel = float(Devices[self._unit_index].sValue)
            except ValueError:
                self._last_fuel = 0

    def update(self, vehicle_status) -> None:
        """Determine the actual value of the instrument and update the sensor in Domoticz."""
        if vehicle_status and vehicle_status.energy:
            if self.exists():
                fuel = vehicle_status.energy.level
                if fuel != self._last_fuel:
                    Devices[self._unit_index].Update(nValue=int(float(fuel)), sValue=str(fuel))
                    self._last_fuel = fuel


class DistanceToyotaSensor(ToyotaDomoticzSensor):
    """The Domoticz sensor that shows the distance between the parked car and home."""

    def __init__(self) -> None:
        super().__init__(UNIT_DISTANCE_INDEX)
        self._coordinates_home: Optional[Tuple[float, ...]] = None
        if Settings['Location']:
            try:
                self._coordinates_home = tuple(float(part) for part in
                                               Settings['Location'].split(';'))
            except ValueError:
                pass

    def create(self, vehicle_status) -> None:
        """Check if the sensor is present in Domoticz, and otherwise create it."""
        if vehicle_status:
            if not self.exists():
                Domoticz.Device(Name='Distance to home', Unit=self._unit_index,
                                TypeName='Custom Sensor', Type=243, Subtype=31,
                                Options={'Custom': '1;km'},
                                Used=1,
                                Description='The distance between home and the car'
                                ).Create()

    def update(self, vehicle_status) -> None:
        """Determine the actual value of the instrument and update the sensor in Domoticz."""
        if vehicle_status and vehicle_status.parking:
            if self.exists():
                if not self._coordinates_home is None:
                    coords_car = (float(vehicle_status.parking.latitude),
                                  float(vehicle_status.parking.longitude))
                    dist = geopy.distance.distance(self._coordinates_home, coords_car).km
                    # Round it to meters.
                    dist = round(dist, 3)
                    Devices[self._unit_index].Update(nValue=0, sValue=f'{dist}')


class LockedToyotaSensor(ToyotaDomoticzSensor):
    """The Domoticz sensor that shows the locked/unlocked status of the car."""

    def __init__(self) -> None:
        super().__init__(UNIT_CAR_LOCKED_INDEX)

    def create(self, vehicle_status) -> None:
        """Check if the sensor is present in Domoticz, and otherwise create it."""
        if vehicle_status:
            if not self.exists():
                Domoticz.Image('ToyotaLocked.zip').Create()
                Domoticz.Device(Name='Locked', Unit=self._unit_index,
                                TypeName='Light/Switch', Type=244, Subtype=73, Switchtype=19,
                                Used=1,
                                Description='The locked/unlocked state of the car',
                                Image=Images['ToyotaLocked'].ID
                                ).Create()

    def update(self, vehicle_status) -> None:
        """Determine the actual value of the instrument and update the sensor in Domoticz."""
        if vehicle_status and vehicle_status.sensors.doors:
            if self.exists():
                locked = True
                for door in vehicle_status.sensors.doors.as_dict():
                    try:
                        locked = locked and door.get('locked', True)
                    except AttributeError:
                        pass
                state = 1 if locked else 0
                Devices[self._unit_index].Update(nValue=state, sValue=str(state))

class ToyotaPlugin(ReducedHeartBeat, ToyotaMyTConnector):
    """Domoticz plugin function implementation to get information from Toyota MyT."""

    def __init__(self) -> None:
        super().__init__()
        self._sensors: List[ToyotaDomoticzSensor] = []

    def add_sensors(self) -> None:
        """Add all the sensor classes that are part of this plugin."""
        self._sensors += [MileageToyotaSensor()]
        self._sensors += [FuelToyotaSensor()]
        self._sensors += [DistanceToyotaSensor()]
        self._sensors += [LockedToyotaSensor()]

    def update_sensors(self) -> None:
        """Retrieve the status of the vehicle and update the Domoticz sensors."""
        vehicle_status = self.retrieve_vehicle_status()
        if vehicle_status:
            for sensor in self._sensors:
                sensor.update(vehicle_status)

    def create_sensors(self) -> None:
        """Create the appropiate sensors in Domoticz for the vehicle."""
        vehicle_status = self.retrieve_vehicle_status()
        if vehicle_status:
            for sensor in self._sensors:
                sensor.create(vehicle_status)


_plugin = ToyotaPlugin()  # pylint:disable=invalid-name

def onStart() -> None:  # pylint:disable=invalid-name
    """Callback from Domoticz that the plugin is started."""
    if DO_DOMOTICZ_DEBUGGING:
        Domoticz.Debugging(1)
        dump_config_to_log()
    if sys.version_info < MINIMUM_PYTHON_VERSION:
        Domoticz.Error(f'Python version {sys.version_info} is not supported,'
                       f' at least {MINIMUM_PYTHON_VERSION} is required.')
    else:
        if _importErrors:
            Domoticz.Error(_importErrors)
        else:
            _plugin.add_sensors()
            _plugin.create_sensors()

def onStop() -> None:  # pylint:disable=invalid-name
    """Callback from Domoticz that the plugin is stopped."""
    _plugin.disconnect()

def onHeartbeat() -> None:  # pylint:disable=invalid-name
    """Callback from Domoticz that the plugin can perform some work."""
    _plugin.onHeartbeat()

def dump_config_to_log() -> None:
    """Dump the configuration of the plugin to the Domoticz debug log."""
    for key in Parameters:
        if Parameters[key] != '':
            value = '******' if key.lower() in ['username', 'password'] else str(Parameters[key])
            Domoticz.Debug(f'\'{key}\': \'{value}\'')
    Domoticz.Debug(f'Device count: {str(len(Devices))}')
    for key in Devices:
        Domoticz.Debug(f'Device:           {str(key)} - {str(Devices[key])}')
        Domoticz.Debug(f'Device ID:       \'{str(Devices[key].ID)}\'')
        Domoticz.Debug(f'Device Name:     \'{Devices[key].Name}\'')
        Domoticz.Debug(f'Device nValue:    {str(Devices[key].nValue)}')
        Domoticz.Debug(f'Device sValue:   \'{Devices[key].sValue}\'')
        Domoticz.Debug(f'Device LastLevel: {str(Devices[key].LastLevel)}')
