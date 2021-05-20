from PyQt5.QtCore import (QState, pyqtSignal)
import logging
logger = logging.getLogger(__name__)


class Main(QState):

    def onExit(self, event):
        logger.info("Turning off the A/D")


class Phase_1A(QState):
    r"""This is also called the "Determining TCS A/D temperature" state.

    During this state flow through the TCS A/D is initiated and the steady
    state temperature is read out.
    """

    def onEntry(self, event):
        logger.info("Charging AD Phase 1A")
        state_machine = self.machine()
        state_machine.tcs.getStableADTemp(Tlimit=state_machine.constants["Charging"]["AD"]["Phase 1A"]["TICA-102"],
                                          Flimit=state_machine.constants["Charging"]["AD"]["Phase 1A"]["FICA-111"])


class Phase_1B(QState):
    r"""This is also called the "Preheating" state.

    During this state the TCS A/D is slowly warmed up until desired temperature
    and then kept there for a certain amount of time.

    If the temperature is higher than the limit, then it is directly skipped.
    """

    warmup = pyqtSignal()

    def onEntry(self, event):
        logger.info("Charging AD Phase 1B")
        state_machine = self.machine()
        arg = event.arguments()[0]
        if arg["StableTemp"] > state_machine.constants["Charging"]["AD"]["Phase 1B"]["limit"]:
            logger.info("Stable temperature is higher than limit, skipping preheat of Charging_AD_Phase_1B.")
            self.warmup.emit()
        else:
            logger.info("Stable temperature is lower than limit, preheating needed.")
            state_machine.tcs.heatConstPowerTo(deltaT=state_machine.constants["Charging"]["AD"]["Phase 1B"]["deltaT"],
                                               flow=state_machine.constants["Charging"]["AD"]["Phase 1B"]["flow"],
                                               Tlimit=state_machine.constants["Charging"]["AD"]["Phase 1B"]["TICA-101"],
                                               Flimit=state_machine.constants["Charging"]["AD"]["Phase 1B"]["FICA-111"])
            state_machine.tcs.temperatureReached.connect(self.warmup.emit)


class Phase_2(QState):
    r"""This is also called the "Warming Up" state.

    During this state the TCS A/D is brought to the starting temperature at
    which the charging should start.
    """
    def onEntry(self, event):
        logger.info("Charging AD Phase 2")
        state_machine = self.machine()
        state_machine.tcs.heatConstPowerTo(deltaT=state_machine.constants["Charging"]["AD"]["Phase 1B"]["deltaT"],
                             flow=state_machine.constants["Charging"]["AD"]["Phase 1B"]["flow"],
                             Tlimit=state_machine.constants["Charging"]["AD"]["Phase 1B"]["TICA-101"],
                             Flimit=state_machine.constants["Charging"]["AD"]["Phase 1B"]["FICA-111"])


class Phase_3(QState):
    r"""This is also called the "Charging" state.

    During this state the TCS A/D and E/C are interconnected.
    """

    def onEntry(self, event):
        logger.info("Charging AD Phase 3")
        state_machine = self.machine()
        state_machine.tcs.storageValve(True)


class Phase_3A(QState):
    r"""This is also called the "Charging Heating up" state.

    During this state the TCS A/D and E/C are interconnected. The Charging proceeds at constant power. The temperature
    at the inlet is increased to accommodate the constant power demand.
    """
    def onEntry(self, event):
        logger.info("Charging AD Phase 3A")
        state_machine = self.machine()
        state_machine.tcs.heatConstPowerTo(deltaT=state_machine.constants["Charging"]["AD"]["Phase 3A"]["deltaT"],
                                           flow=state_machine.constants["Charging"]["AD"]["Phase 3A"]["flow"],
                                           Tlimit=state_machine.constants["Charging"]["AD"]["Phase 3A"]["TICA-101"],
                                           Flimit=state_machine.constants["Charging"]["AD"]["Phase 3A"]["FICA-111"])


class Phase_3B(QState):
    r"""This is also called the "Charging Max temperature" state.

    During this state the TCS A/D and E/C are interconnected. The Charging proceeds at constant temperature. The as the
    temperature at the outlet increases to the inlet, the power delivered to the TCS decreases signifying the end of
    the charge.
    """
    def onEntry(self, event):
        logger.info("Charging AD Phase 3")
        state_machine = self.machine()
        state_machine.tcs.heatConstTempTo()
        tcs.heatConstTempTo(T=5, Tlimit=82)
