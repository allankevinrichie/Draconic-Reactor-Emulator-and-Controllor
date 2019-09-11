import logging
from pprint import pformat
from threading import Timer

from core import *


class Emulator(object):
    core: DraconicReactor

    def __init__(self, core, tps=20, logging_interval=1):
        self.tps = tps
        self.core = core
        self.timer = Timer(1 / tps, self.step)
        self.is_start = False

        self.eir = 0
        self.eor = 0

        self.logger = self.makeLogger()
        self.logging_interval = logging_interval

    def makeLogger(self, warp_methods=("info", "warning", "debug")):
        logger = logging.getLogger(self.__class__.__name__)
        methods = dict()
        for method in warp_methods:
            def _(*args, **kwargs):
                if not (self.core.tick % self.logging_interval):
                    return getattr(logger, method)(*args, extra=self.core.info, **kwargs)
            methods[method] = _
        return type("WarpedLogger", (object, ), methods)

    def setInputEnergy(self, rfpt):
        self.eir = rfpt

    def setOutputEnergy(self, rfpt):
        self.eor = rfpt

    def addFuel(self, fuel):
        if not self.core.startupInitialized:
            self.core.reactableFuel += fuel
            self.logger.info(f"{fuel} fuel added.")
        else:
            self.logger.info(f"Cannot add fuel.")

    def chargeReactor(self):
        self.core.chargeReactor()

    def activateReactor(self):
        self.core.activateReactor()

    def shutdownReactor(self):
        self.core.shutdownReactor()

    def toggleFailSafe(self):
        self.core.toggleFailSafe()

    def step(self):
        self.logger.debug(f"Try to inject {self.eir} RF energy.")
        ei = self.core.injectEnergy(self.eir)
        self.logger.debug(f"{ei} RF energy was injected.")
        self.core.update()
        self.logger.debug(f"Try to extract {self.eor} RF energy.")
        self.core.extractEnergy(self.eor)
        self.logger.debug(f"\nstate: {pformat(self.core.info)}")
        if self.is_start:
            self.reload()

    def start(self):
        self.logger.info(f"Starting emulator.")
        self.is_start = True
        self.timer.start()
        return self.timer

    def reload(self):
        self.timer = Timer(1 / self.tps, self.step)
        self.timer.start()

    def stop(self):
        self.logger.info(f"Stopping emulator.")
        self.timer.cancel()
        self.is_start = False


if __name__ == '__main__':
    fmt = "%(name)s::%(levelname)s::[%(tick)d] %(message)s"
    logging.basicConfig(format=fmt, level=logging.DEBUG)
    emu = Emulator(DraconicReactor(), 20)
    emu.start()
    emu.addFuel(300)
    emu.chargeReactor()
    emu.setInputEnergy(100000)
    while not emu.core.canActivate():
        pass
    emu.stop()
