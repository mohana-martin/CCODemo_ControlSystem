from PyQt5.QtCore import (QObject, QTimer, pyqtSignal)

from .checker import GeneralChecker as Checker
from .checker import CheckerMaster

import logging


class TCSMashina(QObject):
    r"""This is the TCS machine.

    Holds the functionality of the TCS system (series of actions bundled into
    buttons and knobs). It does not know how these functionalities relate to
    each other or how they interlink.

    Parameters
    ----------
     \: str
        s
    """

    ready = pyqtSignal()

    charge = pyqtSignal()
    discharge = pyqtSignal()
    error = pyqtSignal()

    stableADTemp = pyqtSignal(dict)
    temperatureReached = pyqtSignal()
    powerReached = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.checkers = CheckerMaster()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Creating TCS Mashina")
        QTimer.singleShot(500, self.ready.emit)

    def turnOffAll(self):
        self.logger.info("Closing the storage valve XV-601.")
        self.logger.info("Closing valve XV-104.")
        self.logger.info("Closing valve XV-105.")
        self.logger.info("Setting MV-101 to manual mode with a CV of 0%.")
        self.logger.info("Turning P-111 off.")
        self.logger.info("Turning P-211 off.")

    def neutral(self):
        # Turn off all the equipment related to TCS?
        self.checkers["Charge"] = Checker(lambda x: x["TICA-101"], {"lowlimit": 50})
        self.checkers["Charge"].inLimit.connect(self._charge_)
        self.checkers["Discharge"] = Checker(lambda x: x["TICA-101"], {"highlimit": 20})
        self.checkers["Discharge"].inLimit.connect(self._discharge_)

    def _charge_(self):
        self.checkers.stop()
        self.charge.emit()

    def _discharge_(self):
        self.checkers.stop()
        self.discharge.emit()

    def getStableADTemp(self, Tlimit, Flimit):
        self.logger.info("Opening valve XV-104.")
        self.logger.info("Opening valve XV-105.")
        self.logger.info("Setting MV-101 to manual mode with a CV of 0%.")
        self.logger.info("Setting P-111 to manual mode with a CV of 100%.")
        # Flow checker
        self.logger.info(f"Checking if flow does not go below {Flimit['lowlimit']} m3/h.")
        self.checkers["SufficientF"] = Checker(lambda x: x["P-101"], Flimit)
        self.checkers["SufficientF"].outLimit.connect(self._error_)
        # Goal checker
        self.logger.info(f"Waiting until change of temperature reaches {Tlimit['highlimit']} degC/s.")
        self.checkers["StableADTemp"] = Checker(lambda x: x["TICA-102"], Tlimit)
        self.checkers["StableADTemp"].inLimit.connect(self._stableT_)

    def _stableT_(self):
        self.logger.info("Stable temperature reached.")
        # Get data of the temperature
        # self._data_["TICA-101"].iloc[-100:].mean()
        T = 52
        self.logger.debug(f"Stable temperature: {T}")
        self.checkers.stop("StableADTemp")
        self.checkers.stop("SufficientF")
        self.stableADTemp.emit({"StableTemp": T, "i": 5})

    def heatConstPowerTo(self, deltaT, Tlimit, Flimit, flow=300):
        self.logger.info(f"Setting MV-101 to automatic mode with a delta setpoint of {deltaT} degC.")
        self.logger.info(f"Setting pump P-111 to automatic mode with a setpoint of {flow} m3/h.")
        # Flow checker
        self.logger.info(f"Checking if flow does not go below {Flimit['lowlimit']} m3/h.")
        self.checkers["SufficientF"] = Checker(lambda x: x["P-101"], Flimit)
        self.checkers["SufficientF"].outLimit.connect(self._error_)
        # Goal checker
        self.logger.info(f"Waiting until temperature reaches {Tlimit['lowlimit']} degC.")
        self.checkers["SufficientT"] = Checker(lambda x: x["TICA-101"], Tlimit)
        self.checkers["SufficientT"].inLimit.connect(self._reachedT_)

    def heatConstTempTo(self, T, Tlimit, Flimit, Plimit, flow=300):
        self.logger.info(f"Setting MV-101 to automatic mode with a setpoint of {T} degC.")
        self.logger.info(f"Setting pump P-111 to automatic mode with a setpoint of {flow} m3/h.")
        # Flow checker
        self.checkers["SufficientF"] = Checker(lambda x: x["P-101"], **Flimit)
        self.checkers["SufficientF"].outLimit.connect(self._error_)
        # Temperature into mixing valve checker
        self.checkers["SufficientTin"] = Checker(lambda x: T - x["TICA-101"], **Tlimit)
        self.checkers["SufficientTin"].outLimit.connect(self._error_)
        # Goal checker
        myFunc = lambda x: 4.2 * x["FICA-131.PV"] * (x["TICA-101"] - x["TICA-102"]) / 3.6
        self.checkers["SufficientP"] = Checker(myFunc, **Plimit)
        self.checkers["SufficientP"].inLimit.connect(self._reachedP_)

    def storageValve(self, state):
        self.logger.info("Opening storage valve XV-601.")

    def _reachedT_(self):
        self.logger.info("Temperature limit reached.")
        self.checkers.stop("SufficientT")
        self.checkers.stop("SufficientF")
        self.temperatureReached.emit()

    def _reacherP_(self):
        self.logger.info("Power limit reached.")
        self.checkers.stop("SufficientF")
        self.checkers.stop("SufficientTin")
        self.checkers.stop("SufficientP")
        self.powerReached.emit()

    def _signal_(self, checkers, signals, message=None):
        if type(checkers) == str:
            checkers = [checkers]
        if type(signals) == pyqtSignal:
            signals = [signals]
        if message:
            self.logger.info(message)
        self.checkers.stop(checkers)

        for iSignal in signals:
            iSignal.emit()

    def _error_(self):
        self.checkers.stop()
        self.error.emit()
