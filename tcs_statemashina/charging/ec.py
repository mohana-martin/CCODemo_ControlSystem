from PyQt5.QtCore import QState
import logging
logger = logging.getLogger(__name__)


class Main(QState):

    def onExit(self, event):
        logger.info("Turning off the E/C")


class Phase_1A(QState):
    r"""This is also called the "Running the E/C" state.

    During this state flow through the TCS E/C vessel is initiated.
    """

    def onEntry(self, event):
        logger.info("Charging EC Phase 1A")
        tcs = self.machine().tcs