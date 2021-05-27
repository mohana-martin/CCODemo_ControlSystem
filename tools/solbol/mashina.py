import sys

from PyQt5.QtCore import (QObject, QTimer, pyqtSignal, pyqtSlot)
from PyQt5.QtWidgets import (QApplication)

from tools.general.checker import GeneralChecker as Checker
from tools.general.checker import CheckerMaster

import logging


class SolBolMashina(QObject):
    r"""This is the SolBol machine.

    Holds the functionality of the Solar Boiler system (series of actions bundled into
    simple buttons and knobs). It does not know how these functionalities relate to
    each other or how they interlink.

    Parameters
    ----------
     \: str
        s
    """

    solarPump = pyqtSignal()
    solarTemp = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.checkers = CheckerMaster()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Creating SolBol Mashina")
        self._active_ = False

    def activate(self):
        self.checkers.addChecker(Checker(func=lambda x: x["FI-532.PV"],
                                        settings={"lowlimit": 500},
                                        name="SolarFlowChecker"
                                        ))
        self.checkers["SolarFlowChecker"].inLimit.connect(self._checkStart_)
        self.checkers["SolarFlowChecker"].outLimit.connect(self._checkStop_)

        self.checkers.addChecker(Checker(func=lambda x: x["TICA-101"],
                                         settings={"highlimit": 20},
                                         name="TemperatureDifferenceChecker"))
        self.checkers["TemperatureDifferenceChecker"].inLimit.connect(self._checkStart_)
        self.checkers["TemperatureDifferenceChecker"].outLimit.connect(self._checkStop_)
        self._active_ = True

    @property
    def active(self):
        return self._active_

    def deactivate(self):
        self.checkers.stop()
        self.stop()
        self._active_ = False

    @pyqtSlot()
    def _checkStart_(self):
        self.logger.info(f"{self.sender().objectName()} is in limit.")
        self.checkers.changeStatus(self.sender().objectName(), True)
        if all(self.checkers.statusCheckers.values()):
            self.start()
        else:
            self.stop()

    @pyqtSlot()
    def _checkStop_(self):
        self.logger.info(f"{self.sender().objectName()} is out of limit.")
        self.checkers.changeStatus(self.sender().objectName(), False)
        if not(all(self.checkers.statusCheckers.values())):
            self.stop()

    def start(self):
        self.logger.info("Turn XV-001 toward the Boiler.")
        self.logger.info("Turning P-011 ON.")

    def stop(self):
        self.logger.info("Bypassing boiler XV-001.")
        self.logger.info("Turning P-011 OFF.")

if __name__ == "__main__":
    import logging.handlers

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    fh = logging.handlers.TimedRotatingFileHandler(r"log\\cco.log", when='m', interval=1, backupCount=2)
    fh.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    logger.addHandler(ch)
    logger.addHandler(fh)

    logging.info('Started')


    app = QApplication(sys.argv)


    S = SolBolMashina()

    S.activate()
    timer = QTimer()
    timer.timeout.connect(app.quit)
    timer.start(100000)

    app.exec_()