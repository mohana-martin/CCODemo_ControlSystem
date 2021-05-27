from PyQt5.QtCore import QState
import logging
logger = logging.getLogger(__name__)


class Neutral(QState):
    r"""
    During this state TCS is waiting for opportunity.
    """

    def onEntry(self, event):
        logger.info("Neutral State Initialized")
        state_machine = self.machine()
        state_machine.tcs.turnOffAll()
        state_machine.tcs.neutral()
