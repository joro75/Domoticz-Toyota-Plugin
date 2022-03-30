# Copyright (C) 2021 John de Rooij
#
# This software is licensed as described in the file LICENSE, which
# you should have received as part of this distribution.
#
# Domoticz-Toyota-Plugin   ( https://github.com/joro75/Domoticz-Toyota-Plugin )
#
# CodingGuidelines 2020-04-11
# pylint:disable=line-too-long
"""
<plugin key="Toyota" name="Toyota" author="joro75" version="0.9.1"
        externallink="https://github.com/joro75/Domoticz-Toyota-Plugin">
    <description>
        <h2>Domoticz Toyota Plugin 0.9.1</h2>
        <p>
        A Domoticz plugin that provides devices for a Toyota car with connected services.
        </p>
        <p>
        It is using the same API that is used by the Toyota MyT connected services.
        This API is however only useable for cars that are purchased in Europe.
        For more information on Toyota MyT see the
        <a href="https://www.toyota.at/service-und-zubehoer/myt.json">Austrian</a>,
        <a href="https://nl.toyota.be/customer-portal/myt">Belgian</a>,
        <a href="https://www.toyota.co.uk/owners/servicing-and-aftercare/my-toyota/myt-and-connected-services">British</a>,
        <a href="https://www.toyota.dk/service-and-accessories/my-toyota/myt#">Danish</a>,
        <a href="https://www.toyota.nl/service-and-accessories/my-toyota/myt.json">Dutch</a>,
        <a href="https://www.toyota-europe.com/service-and-accessories/my-toyota/myt">European</a>,
        <a href="https://www.toyota.fr/service-and-accessories/my-toyota/myt">French</a>,
        <a href="https://www.toyota.de/service_und_zubehoer/myt">German</a>,
        <a href="https://www.toyota.it/gamma/myt-servizi-connessi">Italian</a>,
        <a href="https://www.toyota.es/MyT/">Spanish</a> or
        <a href="https://fr.toyota.ch/owners/myt-app-multimedia">Swiss</a> website.
        </p>
        <p>
        The Toyota car should first be made available in the MyT connected services,
        after which this plugin can retrieve the information, which is then provided as
        several devices in Domoticz.
        </p>
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li>Mileage - Shows the daily and total mileage of the car</li>
            <li>Fuel level - Shows the actual fuel level percentage</li>
            <li>Distance to home - Shows the distance between the car and home</li>
            <li>Locked - Shows if the car is locked or unlocked</li>
            <li>Parking location - Shows the address of the parking location of the car</li>
            <li>Consumed fuel - Shows the average consumed fuel in l/100 km</li>
        </ul>
        <h3>Configuration</h3>
        <ul style="list-style-type:square">
            <li>Username - The username that is also used to login in the myT application.</li>
            <li>Password - The password that is also used to login in the myT application.</li>
            <li>Car - An identifier for the car for which the data should be retrieved,
                if multiple cars are present in the myT application.
                It can be a part of the VIN number, alias, licenseplate or the model.</li>
        </ul>
    </description>
    <params>
        <param field="Username" label="Username" width="200px" required="true"/>
        <param field="Password" label="Password" width="200px" required="true" password="true"/>
        <!-- Mode1 has been used in the past for the Locale. Not reusing it yet. -->
        <param field="Mode2" label="Car" width="200px" required="false" />
    </params>
</plugin>
"""
# pylint:enable=line-too-long

import sys
from abc import ABC, abstractmethod
import asyncio
import datetime
from typing import Any, Union, List, Tuple, Optional, Dict
import arrow         # pylint:disable=import-error

MINIMUM_PYTHON_VERSION = (3, 7)
DO_DOMOTICZ_DEBUGGING: bool = False
MINIMUM_MYTOYOTA_VERSION: str = '0.8.1'
MINIMUM_GEOPY_VERSION: str = '2.2.0'

NOMINATIM_USER_AGENT = 'Domoticz-Toyota-Plugin'

_importErrors = []  # pylint:disable=invalid-name

try:
    import Domoticz  # type: ignore
except (ModuleNotFoundError, ImportError):
    _importErrors += [('The Python Domoticz library is not installed. '
                       'This plugin can only be used in Domoticz. '
                       'Check your Domoticz installation')]

# Fool mypy and pylint that these types are coming from Domoticz
try:
    from Domoticz import Parameters, Devices, Settings, Images
except (ModuleNotFoundError, ImportError):
    pass

try:
    import setuptools    # type: ignore
    Version = setuptools.distutils.version.LooseVersion
except (ModuleNotFoundError, ImportError):
    _importErrors += ['The python setuptools library is not installed.']

try:
    import mytoyota  # type: ignore

    try:
        mytoyota_version = Version(mytoyota.__version__)
        if mytoyota_version < Version(MINIMUM_MYTOYOTA_VERSION):
            _importErrors += ['The mytoyota version is too old, an update is needed.']
            del mytoyota
            del sys.modules['mytoyota']
    except AttributeError:
        _importErrors += ['The mytoyota version is too old, an update is needed.']

    if 'mytoyota' in sys.modules:
        from mytoyota import MyT  # type: ignore
        import mytoyota.exceptions  # type: ignore
        import mytoyota.models.vehicle  # type: ignore
except (ModuleNotFoundError, ImportError):
    _importErrors += ['The Python mytoyota library is not installed.']

try:
    import geopy.distance  # type: ignore
    geopy_version = Version(geopy.__version__)
    if geopy_version < Version(MINIMUM_GEOPY_VERSION):
        _importErrors += ['The geopy version is too old, an update is needed.']
        del geopy
        del sys.modules['geopy']

    if 'geopy' in sys.modules:
        from geopy.geocoders import Nominatim  # type: ignore
except (ModuleNotFoundError, ImportError):
    _importErrors += ['The python geopy library is not installed.']


UNIT_MILEAGE_INDEX: int = 1
UNIT_FUEL_INDEX: int = 2
UNIT_DISTANCE_INDEX: int = 3
UNIT_CAR_LOCKED_INDEX: int = 4
UNIT_PARKING_LOCATION_INDEX: int = 5
UNIT_CONSUMED_FUEL_INDEX: int = 6

class ReducedHeartBeat(ABC):
    """Helper class that only calls the update of the devices every ... heartbeat."""

    _heartbeat_interval: int = 10

    def __init__(self) -> None:
        super().__init__()
        self._heartbeat_count = self._heartbeat_interval

    def onHeartbeat(self) -> None:  # pylint:disable=invalid-name
        """Callback from Domoticz that the plugin can perform some work."""
        self._heartbeat_count += 1
        if self._heartbeat_count > self._heartbeat_interval:
            self._heartbeat_count = 0
            self.update_devices()

    @abstractmethod
    def update_devices(self) -> None:
        """Retrieve the status of the device and update the Domoticz devices."""
        return

class ToyotaMyTConnector():
    """Provide a connection to the Toyota MyT service."""

    def __init__(self) -> None:
        super().__init__()
        self._logged_on = False
        self._client: MyT = None
        self._car: Optional[Dict[str, Any]] = None

    def _lookup_car(self, cars: Optional[List[Dict[str, Any]]],   # pylint:disable=no-self-use
                identifier: str) -> Optional[Dict[str, Any]]:
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
                               password=Parameters['Password'])
            asyncio.run(self._client.login())
            cars = asyncio.run(self._client.get_vehicles())
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
            if self._car:
                connected = True
        return connected

    def retrieve_vehicle_status(self) -> Union[Any, None]:
        """Retrieve and return the status information of the vehicle."""
        vehicle = None
        if self._ensure_connected():
            Domoticz.Log('Updating vehicle status')
            try:
                vehicle = asyncio.run(self._client.get_vehicle_status(self._car))
            except mytoyota.exceptions.ToyotaInternalError:
                pass
        if vehicle is None:
            Domoticz.Error('Vehicle status could not be retrieved')
        return vehicle

    def retrieve_statistics(self) -> Optional[Dict[str, str]]:
        """Retrieve the statistics of today"""
        statistics = None
        if self._ensure_connected():
            Domoticz.Log('Retrieving vehicle statistics')
            try:
                vin: str = self._car.get('vin', '') if self._car else ''
                statistics = asyncio.run(self._client.get_driving_statistics(vin, interval='day'))
            except mytoyota.exceptions.ToyotaInternalError:
                pass
            except TypeError as inst:
                Domoticz.Error(f'TypeError exception raised: {inst}')
                Domoticz.Dump()
            Domoticz.Log('Vehicle statistics received')

        stats_today = None
        Domoticz.Log('Looking up statistics of today')
        if statistics is None:
            Domoticz.Error('Vehicle statistics could not be retrieved')
        else:
            today = datetime.date.today().isoformat()
            for record in statistics:
                bucket_data = record.get('bucket', None)
                date = bucket_data.get('date', '') if bucket_data else ''
                if date == today:
                    stats_today = record.get('data', None)
                    break
        return stats_today

    def disconnect(self) -> None:
        """Disconnect from the Toyota MyT servers."""
        self._client = None


class DomoticzDevice(ABC):  # pylint:disable=too-few-public-methods
    """Representation of a generic updateable Domoticz devices."""

    def __init__(self, unit_index: int) -> None:
        super().__init__()
        self._unit_index = unit_index
        self._last_update = datetime.datetime.now()
        self._update_interval = 6 * 3600
        self._do_first_update = True

    def exists(self) -> bool:
        """Check if the Domoticz device is present and existing."""
        return (self._unit_index in Devices) and (Devices[self._unit_index])

    def did_update(self) -> None:
        """Remember that an update of the device is done."""
        self._last_update = datetime.datetime.now()
        self._do_first_update = False

    def requires_update(self) -> bool:
        """Determine if an update of the device is needed."""
        diff = datetime.datetime.now() - self._last_update
        return (diff.seconds > self._update_interval) or self._do_first_update

class ToyotaDomoticzDevice(DomoticzDevice):
    """
    A generic updateable Domoticz device, to represent information from
    a Toyota MyT connected services car.
    """

    @abstractmethod
    def create(self, vehicle_status) -> None:
        """Check if the device is present in Domoticz, and otherwise create it."""
        return

    def update(self, vehicle_status) -> None:    # pylint:disable=no-self-use,unused-argument
        """
        Determine the actual value of the instrument and
        update the device in Domoticz.
        """
        return

    def update_statistics(self, statistics) -> None:    # pylint:disable=no-self-use,unused-argument
        """
        Determine the actual value of the statistic of
        today and update the device in Domoticz.
        """
        return

class MileageToyotaDevice(ToyotaDomoticzDevice):
    """The Domoticz device that shows the mileage."""

    def __init__(self) -> None:
        super().__init__(UNIT_MILEAGE_INDEX)
        self._last_mileage: int = 0

    def create(self, vehicle_status) -> None:
        """Check if the device is present in Domoticz, and otherwise create it."""
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
        """Determine the actual value of the instrument and update the device in Domoticz."""
        if vehicle_status and vehicle_status.dashboard:
            if self.exists():
                mileage = vehicle_status.dashboard.odometer
                diff = mileage - self._last_mileage
                if diff > 0 or self.requires_update():
                    # Mileage can only go up
                    Devices[self._unit_index].Update(nValue=0, sValue=f'{diff}')
                    self._last_mileage = mileage
                    self.did_update()


class FuelToyotaDevice(ToyotaDomoticzDevice):
    """The Domoticz device that shows the fuel level percentage."""

    def __init__(self) -> None:
        super().__init__(UNIT_FUEL_INDEX)
        self._last_fuel: float = 0.0

    def create(self, vehicle_status) -> None:
        """Check if the device is present in Domoticz, and otherwise create it."""
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
        """Determine the actual value of the instrument and update the device in Domoticz."""
        if vehicle_status and vehicle_status.dashboard:
            if self.exists():
                fuel = vehicle_status.dashboard.fuel_level
                if fuel != self._last_fuel or self.requires_update():
                    Devices[self._unit_index].Update(nValue=int(float(fuel)), sValue=str(fuel))
                    self._last_fuel = fuel
                    self.did_update()


class DistanceToyotaDevice(ToyotaDomoticzDevice):
    """The Domoticz device that shows the distance between the parked car and home."""

    def __init__(self) -> None:
        super().__init__(UNIT_DISTANCE_INDEX)
        self._last_coords: Tuple[float, ...] = (0.0, 0.0)
        self._coordinates_home: Optional[Tuple[float, ...]] = None
        if Settings['Location']:
            try:
                self._coordinates_home = tuple(float(part) for part in
                                               Settings['Location'].split(';'))
            except ValueError:
                pass

    def create(self, vehicle_status) -> None:
        """Check if the device is present in Domoticz, and otherwise create it."""
        if vehicle_status.parkinglocation:
            if not self.exists() and 'geopy' in sys.modules:
                Domoticz.Device(Name='Distance to home', Unit=self._unit_index,
                                TypeName='Custom Sensor', Type=243, Subtype=31,
                                Options={'Custom': '1;km'},
                                Used=1,
                                Description='The distance between home and the car'
                                ).Create()

    def update(self, vehicle_status) -> None:
        """Determine the actual value of the instrument and update the device in Domoticz."""
        if vehicle_status and vehicle_status.parkinglocation:
            if self.exists() and 'geopy' in sys.modules:
                if not self._coordinates_home is None:
                    coords_car = (float(vehicle_status.parkinglocation.latitude),
                                  float(vehicle_status.parkinglocation.longitude))
                    if coords_car != self._last_coords or self.requires_update():
                        dist = geopy.distance.distance(self._coordinates_home, coords_car).km
                        # Round it to meters.
                        dist = round(dist, 3)
                        Devices[self._unit_index].Update(nValue=0, sValue=f'{dist}')
                        self._last_coords = coords_car
                        self.did_update()

class ParkingLocationToyotaDevice(ToyotaDomoticzDevice):
    """The Domoticz device that shows the address of the parking location of the car."""

    def __init__(self) -> None:
        super().__init__(UNIT_PARKING_LOCATION_INDEX)
        self._last_coords: Tuple[str, ...] = ('', '')

    def create(self, vehicle_status) -> None:
        """Check if the device is present in Domoticz, and otherwise create it."""
        if vehicle_status.parkinglocation:
            if not self.exists() and 'geopy' in sys.modules:
                Domoticz.Device(Name='Parking location', Unit=self._unit_index,
                                TypeName='Text', Type=243, Subtype=19,
                                Used=1,
                                Description='The address of the parking location of the car'
                                ).Create()

    def update(self, vehicle_status) -> None:
        """Determine the actual value of the instrument and update the device in Domoticz."""
        if vehicle_status and vehicle_status.parkinglocation:
            if self.exists() and 'geopy' in sys.modules:
                coords_car = (str(vehicle_status.parkinglocation.latitude),
                              str(vehicle_status.parkinglocation.longitude))
                if coords_car != self._last_coords or self.requires_update():
                    address = self._lookup_address(coords_car)
                    Devices[self._unit_index].Update(nValue=0, sValue=f'{address}')
                    self._last_coords = coords_car
                    self.did_update()

    def _lookup_address(self, coords: Tuple[str, ...]) -> str:     # pylint:disable=no-self-use
        """Determines the address of the given coordinates"""
        coord_str = ','.join(coordinate.strip().lower() for coordinate in coords[0:2])
        geolocator = Nominatim(user_agent=NOMINATIM_USER_AGENT)
        location = geolocator.reverse(coord_str)
        return (location.address if location else '')

class LockedToyotaDevice(ToyotaDomoticzDevice):
    """The Domoticz device that shows the locked/unlocked status of the car."""

    def __init__(self) -> None:
        super().__init__(UNIT_CAR_LOCKED_INDEX)
        self._last_state = -1

    def create(self, vehicle_status) -> None:
        """Check if the device is present in Domoticz, and otherwise create it."""
        if vehicle_status:
            if not self.exists() and self._has_info(vehicle_status):
                Domoticz.Image('ToyotaLocked.zip').Create()
                Domoticz.Device(Name='Locked', Unit=self._unit_index,
                                TypeName='Light/Switch', Type=244, Subtype=73, Switchtype=19,
                                Used=1,
                                Description='The locked/unlocked state of the car',
                                Image=Images['ToyotaLocked'].ID
                                ).Create()

    def _get_doors(self, vehicle_status):    # pylint:disable=no-self-use
        """Return an array of individual door instances"""
        doors = []
        if vehicle_status and vehicle_status.sensors.doors:
            direct = vehicle_status.sensors.doors
            try:
                doors = [direct.driver_seat, direct.passenger_seat,
                         direct.leftrear_seat, direct.rightrear_seat,
                         direct.trunk]
            except (AttributeError, TypeError):
                pass
        return doors

    def _has_info(self, vehicle_status) -> bool:     # pylint:disable=no-self-use
        """Determine if the information of the locked state is available."""
        present = False
        for door in self._get_doors(vehicle_status):
            present = present or door is not None
        return present

    def update(self, vehicle_status) -> None:
        """Determine the actual value of the instrument and update the device in Domoticz."""
        if self.exists():
            locked = True
            for door in self._get_doors(vehicle_status):
                try:
                    locked = locked and door.locked if door is not None else True
                except AttributeError:
                    pass
            state = 1 if locked else 0
            if state != self._last_state or self.requires_update():
                Devices[self._unit_index].Update(nValue=state, sValue=str(state))
                self._last_state = state
                self.did_update()


class ConsumedFuelToyotaDevice(ToyotaDomoticzDevice):
    """The Domoticz device that shows the average consumed fuelage in l/100 km."""

    def __init__(self) -> None:
        super().__init__(UNIT_CONSUMED_FUEL_INDEX)
        self._last_consumed_fuel: float = 0.0

    def create(self, vehicle_status) -> None:
        """Check if the device is present in Domoticz, and otherwise create it."""
        if vehicle_status:
            if not self.exists():
                Domoticz.Device(Name='Consumed fuel', Unit=self._unit_index,
                                TypeName='Counter Incremental', Switchtype=3,
                                Used=1,
                                Description='Average consumed fuel in l/100 km',
                                Options={'ValueUnits': 'l/100 km',
                                         'ValueQuantity': 'l/100 km'}
                                ).Create()
        if self.exists():
            try:
                self._last_consumed_fuel = float(Devices[self._unit_index].sValue)
            except ValueError:
                self._last_consumed_fuel = 0

    def update_statistics(self, statistics) -> None:
        """Determine the actual value of the statistics and update the device in Domoticz."""
        if self.exists():
            Domoticz.Log(f'{statistics}')
            fuel = float(statistics.get('totalFuelConsumedInL', 0.0)) if statistics else 0.0
            Domoticz.Log(f'Fuel consumed: {fuel}')
            if fuel != self._last_consumed_fuel or self.requires_update():
                # Restore the counter to 0
                Devices[self._unit_index].Update(nValue=0, sValue=f'-{self._last_consumed_fuel}')
                # Set the actual value for today
                Devices[self._unit_index].Update(nValue=0, sValue=f'{fuel}')
                self._last_consumed_fuel = fuel
                self.did_update()


class ToyotaPlugin(ReducedHeartBeat, ToyotaMyTConnector):
    """Domoticz plugin function implementation to get information from Toyota MyT."""

    def __init__(self) -> None:
        super().__init__()
        self._devices: List[ToyotaDomoticzDevice] = []
        self._now = arrow.now()

    def add_devices(self) -> None:
        """Add all the device classes that are part of this plugin."""
        self._devices += [MileageToyotaDevice()]
        self._devices += [FuelToyotaDevice()]
        self._devices += [DistanceToyotaDevice()]
        self._devices += [LockedToyotaDevice()]
        self._devices += [ParkingLocationToyotaDevice()]
        self._devices += [ConsumedFuelToyotaDevice()]

    def update_devices(self) -> None:
        """Retrieve the status of the vehicle and update the Domoticz devices."""
        vehicle_status = self.retrieve_vehicle_status()
        if vehicle_status:
            for device in self._devices:
                device.update(vehicle_status)
        statistics = self.retrieve_statistics()
        if statistics:
            for device in self._devices:
                device.update_statistics(statistics)

    def create_devices(self) -> None:
        """Create the appropiate devices in Domoticz for the vehicle."""
        vehicle_status = self.retrieve_vehicle_status()
        if vehicle_status:
            for device in self._devices:
                device.create(vehicle_status)


_plugin = ToyotaPlugin() if 'mytoyota' in sys.modules else None  # pylint:disable=invalid-name

def onStart() -> None:  # pylint:disable=invalid-name
    """Callback from Domoticz that the plugin is started."""
    if DO_DOMOTICZ_DEBUGGING:
        Domoticz.Debugging(1)
        dump_config_to_log()
    if sys.version_info < MINIMUM_PYTHON_VERSION:
        Domoticz.Error(f'Python version {sys.version_info} is not supported,'
                       f' at least {MINIMUM_PYTHON_VERSION} is required.')
    else:
        global _importErrors      # pylint:disable=invalid-name,global-statement
        if _importErrors:
            _importErrors += [('Use pip to install required packages: '
                               'pip3 install -r requirements.txt')]
            for err in _importErrors:
                Domoticz.Error(err)
        elif _plugin:
            _plugin.add_devices()
            _plugin.create_devices()

def onStop() -> None:  # pylint:disable=invalid-name
    """Callback from Domoticz that the plugin is stopped."""
    if _plugin:
        _plugin.disconnect()

def onHeartbeat() -> None:  # pylint:disable=invalid-name
    """Callback from Domoticz that the plugin can perform some work."""
    if _plugin:
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
