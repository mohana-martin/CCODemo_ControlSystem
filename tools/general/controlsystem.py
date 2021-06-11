# -*- coding: utf-8 -*-
"""
Created on Thu May 27 13:27:36 2021

@author: mohanam
"""

from functools import partial
from types import MethodType
import datetime as dt

from cRIO_comms.cRIOFormats import cRIOSetpoint
from cRIO_comms.cRIOCommunication import cRIOWebServerComms


class ControlSystemMap(object):
    
    def __init__(self, **kwargs):
        '''
        Starts up the communication, gets the current data and constructs a map
        of the control system in question.
        Parameters
        ----------
        ip: str
            the ip address of the cRIO
        '''
        self.crio_communication = cRIOWebServerComms(**kwargs)
        self.getCurrentData()
        sys = self.crio_communication.getSystemInformation()
        
        for iGroup, iTagDict in sys["Tag Information"].items():
            iDict = {}
            for iTag, iAttributes in iTagDict.items():
                iDict[iTag] = Tag(self, tag=iTag,**iAttributes)
            setattr(self, iGroup.replace(" ","_"), iDict)
    
    
    def getCurrentData(self):
        '''
        Requests latest data from the cRIO and saves the result also 
        internally.

        Returns
        -------
        pandas.Series
            index being the tag name, values containing the values
        '''
        self.__data, self.__units = self.crio_communication.getCurrentData()
        self.__dataTime = dt.datetime.now()
        return self.__data
        
    def getLastData(self, window=5):
        '''
        Gets the last data from the cRIO stored internally as long as it is 
        not older than the window.
        
        Parameters
        ----------
        window: float or int
            number of seconds
        
        Returns
        -------
        pandas.Series
            index being the tag name, values containing the values
        '''
        if dt.datetime.now()-self.__dataTime <= dt.timedelta(seconds=window):
            return self.__data
        else:
            return self.getCurrentData()


class Attribute(object):
    
    def __init__(self, control_system, full_tag, **properties):
        '''
        Holds an attribute of a Tag and its properties.
        E.g. MV-101.On-Out has properties like Settable, Unit, etc.
        It is therefore Tag Attribute Properties. Default properties are Value.
        set_Value appears only when the property is Settable.
        
        Parameters
        ----------
        control_system: ControlSystemMap
            contains the link to the communication wrapper to the cRIO
        full_tag: str
            important, as it is used as a reference for getting and setting the
            value
        **properties: dict
            contains keys and values of the properties of the attribute which 
            will be saved in this object.
        '''
        self.system = control_system
        self.tag = full_tag
        self.key = "_".join(full_tag.split(".")[1:])
        
        for iProperty, iValue in properties.items():
            iPropertyName = iProperty.replace(".","_")
            setattr(self, f"_{iPropertyName}", iValue)
            setattr(self, f"get_{iPropertyName}", partial(self._get_x, x=iPropertyName, obj=self))
        
        if "Settable" in properties:
                if properties["Settable"]:
                    setattr(self, "set_Value", partial(self._set_Value, obj=self))
    
    @staticmethod
    def _get_x(obj, x):
        return getattr(obj, f"_{x}")
    
    def get_Value(self):
        return self.system.getLastData()[self.tag]
    
    @staticmethod
    def _set_Value(x, obj):
        if hasattr(obj, "get_Range_Min") and hasattr(obj, "get_Range_Max"):
            if not(obj.get_Range_Min() <= x <= obj.get_Range_Max()):
                raise ValueError("Command not sent. Value seems to be out of bounds.")
        obj.system.crio_communication.setSetpoint(cRIOSetpoint(obj.tag, x))


class Tag(object):
    
    def __init__(self, control_system, tag, **attributes):
        '''
        Holds a tag with it attributes and its properties.
        E.g. MV-101.On-Out has properties like Settable, Unit, etc.
        It is therefore Tag Attribute Properties. Default properties are Value.
        set_Value appears only when the property is Settable.
        
        Parameters
        ----------
        control_system: ControlSystemMap
            contains the link to the communication wrapper to the cRIO
        tag: str
        **attributes: dict
            contains keys and values of the attributes with their properties
            which will be saved in this object and Attributes constructed.
        '''
        self.system = control_system
        self.tag = tag
        
        for iAttribute, iProperties in attributes.items():
            iAttributeName = "_".join(iAttribute.split(".")[1:]).replace(".","_").replace("-","_")
            setattr(self, f"{iAttributeName}", Attribute(control_system, iAttribute, **iProperties))
            
if __name__ == "__main__":
    c = ControlSystemMap(ip='http://10.120.210.251:8002/cRIO-Webservice/')
    MV = c.Controllers["TICSA-123"]
    MV.Auto.get_Settable()
    
    _loops = {
    "Solar": {"Flow":"FI-532",
               "T_in": "TI-521a",
               "T_out": "TI-521b"},
     "HX": {"Flow":"FICSA-031",
            "T_in": "TI-021a",
            "T_out": "TI-021b"},
     "Boiler": {"Flow":"FICSA-031",
                "T_in": "TI-022a",
                "T_out": "TI-022b"},
     "TCS_Hot": {"Flow":"FICSA-131",
                 "T_in": "TIA-121a",
                 "T_out": "TIA-121b"},
     "TCS_Cold": {"Flow":"FI-532",
                  "T_in": "TI-221a",
                  "T_out": "TISA-221b"},
      "Shower": {"Flow":"FI-431",
                 "T_in": "TI-421a",
                 "T_out": "TI-422b"}
              }
     
    loops = {}
    for iLoop, iSensors in _loops.items():
        loops[iLoop] = {"Flow": c.Process_Values[iSensors["Flow"]].PV.get_Value,
                         "dT": partial(lambda x: c.Process_Values[x["T_out"]].PV.get_Value() - c.Process_Values[x["T_in"]].PV.get_Value(),x=iSensors)}
        loops[iLoop]["Power"] = partial(lambda x: loops[x]["Flow"]() * loops[x]["dT"]() * 4200 / 3600, x=iLoop)