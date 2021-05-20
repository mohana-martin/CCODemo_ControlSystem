from PyQt5.QtCore import QState
import logging
logger = logging.getLogger(__name__)


class StartingPoint(QState):
    r"""
    This is a pseudo-state to initialize the system and provide the state
    machine a reference to the TCS mashina.
    """

    def onEntry(self, event):
        logger.info("Starting")

    def onExit(self, event):
        logger.info("Proceeding to Neutral")


class Error(QState):

    def onEntry(self, event):
        logger.info("Received error!")


class Emergency(QState):

    def onEntry(self, event):
        logger.info("The TCS system has an alarm.")