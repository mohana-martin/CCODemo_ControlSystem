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


class ControlSystem(object):
    
    def __init__(self, **kwargs):
        self.crio_communication = cRIOWebServerComms(**kwargs)
        self.getCurrentData()
        sys = self.crio_communication.getSystemInformation()
        
        for iGroup, iTagDict in sys["Tag Information"].items():
            iDict = {}
            for iTag, iAttributes in iTagDict.items():
                iDict[iTag] = Tag(self, tag=iTag,**iAttributes)
            setattr(self, iGroup, iDict)
    
    
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
        self.system = control_system
        self.tag = full_tag
        self.key = "_".join(full_tag.split(".")[1:])
        
        for iProperty, iValue in properties.items():
            iPropertyName = iProperty.replace(".","_")
            setattr(self, f"_{iPropertyName}", iValue)
            setattr(self, f"get_{iPropertyName}", partial(self._get_x, obj=self, x=iPropertyName))
        
        if "Settable" in properties:
                if properties["Settable"]:
                    setattr(self, "set_Value", partial(self._set_Value, obj=self))
    
    @staticmethod
    def _get_x(obj, x):
        return getattr(obj, f"_{x}")
    
    def get_Value(self):
        return self.system.getLastData()[self.tag]
    
    @staticmethod
    def _set_Value(obj, x):
        obj.system.crio_communication.setSetpoint(cRIOSetpoint(obj.tag, x))


class Tag(object):
    
    def __init__(self, control_system, tag, **attributes):
        self.system = control_system
        self.tag = tag
        
        for iAttribute, iProperties in attributes.items():
            iAttributeName = "_".join(iAttribute.split(".")[1:]).replace(".","_").replace("-","_")
            setattr(self, f"{iAttributeName}", Attribute(control_system, iAttribute, **iProperties))