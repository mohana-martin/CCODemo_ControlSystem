from PyQt5.QtCore import QStateMachine, QTimer

import json

import logging
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


class TCSStateMashina(QStateMachine):

    def __init__(self, tcsmashina, constpath, interval=15000):
        super(TCSStateMashina, self).__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Creating TCS State Mashina")
        self.logger.debug(f"Configuration: {constpath} checked at every {interval} ms.")
        self.tcs = tcsmashina
        self._constPath_ = constpath
        self._timerInterval = interval
        self.constants = None
        self._load_constants_()
        self._setup_timer_()

    def _setup_timer_(self):
        self.logger.info("Initializing the configuration checker timer.")
        self.logger.debug(f"Interval {self._timerInterval}")
        self._timer_ = QTimer()
        self._timer_.setInterval(self._timerInterval)
        self._timer_.timeout.connect(self._load_constants_)
        self._timer_.start()

    def _load_constants_(self):
        self.logger.info("Getting new configuration.")
        try:
            with open(self._constPath_, mode="r") as file:
                self.constants = json.load(file)
                self.logger.debug(f"Configuration: {self.constants}")
        except Exception as E:
            self.logger.critical(f"Latest configuration not loaded!: {E}")

    def stop_timers(self):
        self.tcs.checkers.stop()
        self._timer_.stop()
