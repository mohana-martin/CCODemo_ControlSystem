import pandas as pd

import findiff
from collections import deque
import numpy as np

from PyQt5.QtCore import QObject, pyqtSignal, QTimer

import logging
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

"""
TODO: change how derivative is calculated.. normalize and correct for time steps
"""


class GeneralChecker(QObject):
    r"""

        A general checker that can be used for all-purpose checking of variables
        and their value.

        Example of usage:
        If the momentary value of variableA should be within a certain range
        and this should be checked once every minute:
            GeneralChecker(func=lambda x: x["variableA"],
                           {"lowlimit":0,
                           "highlimit":10,
                           "interval":60000})
        If the average value of variableA-variableB for the last 10 measurements
        (as measured by cRIO) should be within a certain range and this should
        be checked every 5 seconds:
            GeneralChecker(func=lambda x: x["variableA"] - x["variableB"],
                           {"lowlimit":0,
                           "highlimit":10,
                           "acc":10,
                           "interval":5000})

        Parameters
        ----------
        func \: function
            a function taking one input in the form of what is stored in the
            self.data. Should be pandas.DataFrame
        settings \: dict
                lowlimit \: int or float
                highlimit \: int or float
                der \: int
                 the order of the derivative
                acc \: int
                    the distance from the center point of the window (should be even). Simply can be regarded as the
                    window size.
                interval \: int or float
                    the miliseconds between each check
    """

    outLimit = pyqtSignal()
    inLimit = pyqtSignal()

    defaultParameters = {"lowlimit": -float('inf'),
                         "highlimit": float('inf'),
                         "der": 0,
                         "acc": 0,
                         "window": 1,
                         "interval": 1000
                         }

    def __init__(self, func, settings):
        super().__init__()
        self._func_ = func
        self.logger = logging.getLogger(__name__)
        self.logger.info("Creating checker")
        self.logger.debug(f"Creating checker with the following settings {settings}.")
        self._parameters = settings
        self._timer_ = None
        self._update_parameters()
        self._setup_der_coef()
        self._finalylist_ = deque(self.par["window"] * [np.NAN])
        self._setup_timer()
        self._getData_()

    def _update_parameters(self):
        self.logger.info("Obtaining latest settings.")
        ret_dict = self._parameters.copy()
        self.logger.debug(f"Latest settings obtained: {ret_dict}.")
        for k, v in GeneralChecker.defaultParameters.items():
            ret_dict.setdefault(k, v)
        self.par = ret_dict
        if self._timer_:
            if self._timer_.interval != self.par["interval"]:
                self.logger.info("Changing checker frequency.")
                self.logger.debug(f"Interval {self.par['interval']}")
                self._timer_.setInterval(self.par["interval"])

    def _setup_der_coef(self):
        self._derwindow_ = self.par["acc"] + 1
        if self.par["der"] > 0:
            self._dercoef_ = findiff.coefficients(deriv=self.par["der"],
                                                  acc=self.par["acc"])["backward"]["coefficients"]
        else:
            self._dercoef_ = np.array(self._derwindow_ * [1 / self._derwindow_])
        self._ylist_ = deque(self._derwindow_ * [np.NAN])

    def _setup_timer(self):
        self.logger.info("Initializing the checker timer.")
        self.logger.debug(f"Interval {self.par['interval']}")
        self._timer_ = QTimer()
        self._timer_.setInterval(self.par["interval"])
        self._timer_.timeout.connect(self.run)
        self._timer_.start()

    def _derfunc_(self, y):
        r"""Calculates the derivative of values returned from func.

        It fills up a y-list (initialized with NaN) with new data. This is
        done in case there is not enough data available. This should be changed
        because it can cause mix up of old and new data!

        Parameters
        ----------
        y \: list
            a list containing the new data points

        Returns
        -------
        float
            the derivative of the data
        """
        for i in y:
            self._ylist_.popleft()
            self._ylist_.append(i)
        return np.nansum(self._dercoef_ * np.array(self._ylist_))

    def _getData_(self):
        r"""Get the latest data in the MySQL database.

        Saves the latest data from the MySQL database into memory of the
        checker object.
        """
        try:
            self.data = pd.read_excel(r"C:/Users/mohanam/Desktop/ToDO/CCO_Demo/cRIOTagSimDB.xlsx", index_col=0)
        except:
            pass

    def _check_(self):
        r"""Checks the whether the testing value lays within the lowlimit and
        highlimit.

        Returns
        -------
        boolean
        """
        self.logger.debug(f"Latest list of check variable: {self._finalylist_}.")
        return self.par["lowlimit"] < np.nanmean(self._finalylist_) < self.par["highlimit"]

    def _run_(self):
        r"""Obtains the latests data, does the processing and saves the results in a list.
        """
        self._getData_()
        # run the function on all the data and extract only the part needed for the derivation
        newY = self._func_(self.data).iloc[-self._derwindow_:].to_list()
        # conduct the derivation
        newderY = self._derfunc_(newY)
        # add to a confined list
        self._finalylist_.popleft()
        self._finalylist_.append(newderY)

    def run(self):
        self.logger.info("Running check.")
        self._run_()
        self.logger.debug(f"Latest data: {self.data}.")

        if self._check_():
            self.logger.info("The checked value is within the limits.")
            self.inLimit.emit()
        else:
            self.logger.info("The checked value is out of the limit.")
            self.outLimit.emit()

    def stop(self):
        self.logger.info("Checker stopped.")
        self._timer_.stop()


class CheckerMaster(object):

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Creating CheckerMaster.")
        self._checkers_ = {}

    def stop(self, name=None):
        if not name:
            self.logger.info("Stopping all checkers.")
            name = self.active
        elif type(name) == str:
            name = [name]

        for iName in name:
            self.logger.info(f"Stopping checker {iName}")
            self._checkers_[iName].stop()
            self._checkers_.pop(iName)

    def __getitem__(self, name):
        return self._checkers_[name]

    def __setitem__(self, name, value):
        self._checkers_[name] = value

    @property
    def active(self):
        return list(self._checkers_.keys())
