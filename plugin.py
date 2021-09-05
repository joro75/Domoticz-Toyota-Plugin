# Domoticz-Toyota-Plugin
#
# Author: John de Rooij
#
"""
<plugin key="Toyota" name="Toyota" author="joro75" version="0.0.1" externallink="https://github.com/joro75/Domoticz-Toyota-Plugin">
    <description>
        <h2>Domoticz Toyota Plugin 0.0.1</h2>
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
        </ul>
        <h3>Configuration</h3>
        <ul style="list-style-type:square">
            <li>Username - The username that is also used to login in the myT application.</li>
            <li>Password - The password that is also used to login in the myT application.</li>
            <li>Locale - The locale that should be used. This can be 'en-us' or another locale.</li>
            <li>Car - An identifier for the car for which the data should be retrieved, if multiple cars are present in the myT application.
            It can be a part of the VIN number, a part of the alias or the model.</li>
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

class ToyotaPlugin:
    def __init__(self):
        return

    def onStart(self):
        Domoticz.Log("onStart called")
        if (len(Devices) == 0):
            Domoticz.Device(Name="Mileage", Unit=1, TypeName="Counter Incremental").Create()
            Domoticz.Device(Name="Fuel level", Unit=2, TypeName="Percentage").Create()
            Domoticz.Log("Devices created.")

    def onStop(self):
        Domoticz.Log("onStop called")

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
        Domoticz.Log("onHeartbeat called")

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
    