import sys

from PyQt5.QtCore import (QCoreApplication, QState, QTimer)
from PyQt5.QtWidgets import (QApplication, QMainWindow)

import logging
import logging.handlers
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

from tcs import mashina
import tcs_statemashina

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
fh = logging.handlers.TimedRotatingFileHandler("cco.log", when='m', interval=1, backupCount=2)
fh.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

ch.setFormatter(formatter)
fh.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(fh)

logging.info('Started')

configPath = r"C:/Users/mohanam/PycharmProjects/CCODemoControlSystem/config.json"

if __name__ == "__main__":
    app = QApplication(sys.argv)

    tcs = mashina.TCSMashina()
    TCSstate = tcs_statemashina.statemashina.TCSStateMashina(tcs, configPath, 1000)
    startingpoint = tcs_statemashina.other.StartingPoint()
    TCSstate.addState(startingpoint)

    neutral = tcs_statemashina.neutral.Neutral()
    TCSstate.addState(neutral)

    startingpoint.addTransition(tcs.ready, neutral)

    charging = QState(QState.ParallelStates)
    TCSstate.addState(charging)

    neutral.addTransition(tcs.charge, charging)

    charging_ad = tcs_statemashina.charging.ad.Main(charging)

    charging_ad_phase_1A = tcs_statemashina.charging.ad.Phase_1A(charging_ad)
    charging_ad.setInitialState(charging_ad_phase_1A)

    charging_ad_phase_1B = tcs_statemashina.charging.ad.Phase_1B(charging_ad)
    charging_ad_phase_1A.addTransition(tcs.stableADTemp,
                                       charging_ad_phase_1B)

    charging_ad_phase_2 = tcs_statemashina.charging.ad.Phase_2(charging_ad)
    charging_ad_phase_1B.addTransition(charging_ad_phase_1B.warmup,
                                       charging_ad_phase_2)

    charging_ad_phase_3 = tcs_statemashina.charging.ad.Phase_3(charging_ad)
    charging_ad_phase_3A = tcs_statemashina.charging.ad.Phase_3A(charging_ad_phase_3)
    charging_ad_phase_3B = tcs_statemashina.charging.ad.Phase_3B(charging_ad_phase_3)
    charging_ad_phase_3.setInitialState(charging_ad_phase_3A)

    charging_ad_phase_3A.addTransition(tcs.temperatureReached, charging_ad_phase_3B)
    charging_ad_phase_3B.addTransition(tcs.powerReached, neutral)

    charging_ad_phase_2.addTransition(tcs.temperatureReached,
                                      charging_ad_phase_3)

    charging_ec = tcs_statemashina.charging.ec.Main(charging)

    charging_ec_phase_1A = tcs_statemashina.charging.ec.Phase_1A(charging_ec)
    charging_ec.setInitialState(charging_ec_phase_1A)

    charging.addTransition(tcs.error, neutral)

    TCSstate.setInitialState(startingpoint)
    TCSstate.start()

    timer = QTimer()
    timer.timeout.connect(TCSstate.stop_timers)
    timer.timeout.connect(app.quit)
    timer.start(100000)

    # This is catcher to catch the program from stopping before all is finished.
    app.exec_()
