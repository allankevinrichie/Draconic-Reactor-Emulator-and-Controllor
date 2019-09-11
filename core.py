# work with brandon3055 commit 9cd2c6a on Jul 9
# simply translate related java code into python code (even comments are kept)

from random import Random


class ReactorState(object):
    INVALID = 0
    COLD = 1
    WARMING_UP = 2
    RUNNING = 3
    STOPPING = 4
    COOLING = 5
    BEYOND_HOPE = 6

    BOOMED = 7


class JAVA(object):
    class Integer(object):
        MAX_VALUE = 2147483647


''' Notes for V2 Logic
    /*
    *
    * Calculation Order: WIP
    *
    * 1: Calculate conversion modifier
    *
    * 2: Saturation calculations
    *
    * 3: Temperature Calculations
    *
    * 4: Energy Calculations then recalculate saturation so the new value is reflected in the shield calculations
    *
    * 5: Shield Calculation
    *
'''


# noinspection PyPep8Naming
class DraconicReactor(object):
    tick: int
    reactorState: int
    reactableFuel: float
    convertedFuel: float
    temperature: float
    shieldCharge: float
    maxShieldCharge: float
    saturation: int
    maxSaturation: int
    tempDrainFactor: float
    generationRate: float
    fieldDrain: int
    fieldInputRate: float
    fuelUseRate: float
    startupInitialized: bool
    failSafeMode: bool

    def __init__(self, reactorOutputMultiplier=1.0, reactorFuelUsageMultiplier=1.0, disableLargeReactorBoom=True):
        self.tick = 0
        self.rand = Random()
        # DEConfig
        self.reactorOutputMultiplier = reactorOutputMultiplier
        self.reactorFuelUsageMultiplier = reactorFuelUsageMultiplier
        self.disableLargeReactorBoom = disableLargeReactorBoom
        # This is the current operational state of the reactor.
        self.reactorState = ReactorState.COLD
        # Remaining fuel that is yet to be consumed by the reaction.
        self.reactableFuel = 0
        # Fuel that has been converted to chaos by the reaction.
        self.convertedFuel = 0
        # temperature
        self.temperature = 0
        self.MAX_TEMPERATURE = 10000
        # shield
        self.shieldCharge = 0
        self.maxShieldCharge = 0
        # This is how saturated the core is with energy.
        self.saturation = 0
        self.maxSaturation = 0
        # dynamic characteristics
        self.tempDrainFactor = 0
        self.generationRate = 0
        self.fieldDrain = 0
        self.fieldInputRate = 0
        self.fuelUseRate = 0

        self.startupInitialized = False
        self.failSafeMode = False

        # Explody Stuff!
        self.explosionCountdown = -1
        self.minExplosionDelay = 0

    def updateCoreLogic(self):
        if self.reactorState in (ReactorState.INVALID, ReactorState.COLD):
            self.updateOfflineState()
        elif self.reactorState == ReactorState.WARMING_UP:
            self.initializeStartup()
        elif self.reactorState == ReactorState.RUNNING:
            self.updateOnlineState()
            if self.failSafeMode and self.temperature < 2500 and self.saturation / self.maxSaturation >= 0.99:
                print("Reactor: Initiating Fail-Safe Shutdown!")
                self.shutdownReactor()
        elif self.reactorState == ReactorState.STOPPING:
            self.updateOnlineState()
            if self.temperature <= 2000:
                self.reactorState = ReactorState.COOLING
        elif self.reactorState == ReactorState.COOLING:
            self.updateOfflineState()
            if self.temperature <= 100:
                self.reactorState = ReactorState.COLD
        elif self.reactorState == ReactorState.BEYOND_HOPE:
            self.updateCriticalState()

    # Update the reactors offline state.
    # This is responsible for things like returning the core temperature to minimum
    # and draining remaining charge after the reactor shuts down.
    def updateOfflineState(self):
        if self.temperature > 20:
            self.temperature -= 0.5

        if self.shieldCharge > 0:
            self.shieldCharge -= self.maxShieldCharge * 0.0005 * self.rand.random()
        elif self.shieldCharge < 0:
            self.shieldCharge = 0

        if self.saturation > 0:
            self.saturation -= int(self.maxSaturation * 0.000002 * self.rand.random())
        elif self.saturation < 0:
            self.saturation = 0

    # This method is fired when the reactor enters the warm up state.
    # The first time this method is fired if initializes all of the reactors key fields.
    def initializeStartup(self):
        if not self.startupInitialized:
            totalFuel = self.reactableFuel + self.convertedFuel
            self.maxShieldCharge = totalFuel * 96.45061728395062 * 100
            self.maxSaturation = int(totalFuel * 96.45061728395062 * 1000)

            if self.saturation > self.maxSaturation:
                self.saturation = self.maxSaturation

            if self.shieldCharge > self.maxShieldCharge:
                self.shieldCharge = self.maxShieldCharge

            self.startupInitialized = True

    def updateOnlineState(self):
        # 1 = Max Saturation
        coreSat = self.saturation / self.maxSaturation
        # 99 = Min Saturation. I believe this tops out at 99 because at 100 things would overflow and break.
        negCSat = (1 - coreSat) * 99
        # 50 = Max Temp. Why? TBD
        temp50 = min((self.temperature / self.MAX_TEMPERATURE) * 50, 99)
        # Total Fuel.
        tFuel = self.convertedFuel + self.reactableFuel
        # Conversion Level sets how much the current conversion level boosts power gen. Range: -0.3 to 1.0
        convLVL = ((self.convertedFuel / tFuel) * 1.3) - 0.3

        # ============= region: Temperature Calculation ============= #
        # Adjusts where the temp falls to at 100% saturation
        tempOffset = 444.7
        # The exponential temperature rise which increases as the core saturation goes down
        # This is just terrible... I cant believe i wrote this stuff...
        tempRiseExpo = (negCSat * negCSat * negCSat) / (100 - negCSat) + tempOffset
        # This is used to add resistance as the temp rises because the hotter something gets the more energy it takes
        # to get it hotter.
        # Mostly Correct... The hotter an object gets the faster it dissipates heat into its surroundings
        # to the more energy it takes to compensate for that energy loss.
        tempRiseResist = (temp50 * temp50 * temp50 * temp50) / (100 - temp50)
        # This puts all the numbers together and gets the value to raise or lower the temp by this tick.
        # This is dealing with very big numbers so the result is divided by 10000
        riseAmount = (tempRiseExpo - (tempRiseResist * (1. - convLVL)) + convLVL * 1000) / 10000

        # Apply energy calculations.
        if self.reactorState == ReactorState.STOPPING and convLVL < 1:
            if self.temperature <= 2001:
                self.reactorState = ReactorState.COOLING
                self.startupInitialized = False
                return None
            if self.saturation >= self.maxSaturation * 0.99 and self.reactableFuel > 0:
                self.temperature -= 1 - convLVL
            else:
                self.temperature += riseAmount * 10
        else:
            self.temperature += riseAmount * 10
        # ============= endregion: Temperature Calculation ============= #

        # ============= region: Energy Calculation ============= #
        baseMaxRFt = int((self.maxSaturation / 1000) * self.reactorOutputMultiplier * 1.5)
        maxRFt = int(baseMaxRFt * (1 + (convLVL * 2)))
        self.generationRate = (1 - coreSat) * maxRFt
        self.saturation += int(self.generationRate)
        # =========== endregion: Energy Calculation ============ #

        # ============= region: Shield Calculation ============= #
        if self.temperature > 8000:
            self.tempDrainFactor = 1 + ((self.temperature - 8000) * (self.temperature - 8000) * 0.0000025)
        elif self.temperature > 2000:
            self.tempDrainFactor = 1
        elif self.temperature > 1000:
            self.tempDrainFactor = (self.temperature - 1000) / 1000
        else:
            self.tempDrainFactor = 0
        # baseMaxRFt/make smaller to increase field power drain
        self.fieldDrain = int(
            min(self.tempDrainFactor * max(0.01, (1 - coreSat)) * (baseMaxRFt / 10.923556), JAVA.Integer.MAX_VALUE)
        )
        fieldNegPercent = 1. - (self.shieldCharge / self.maxShieldCharge)
        self.fieldInputRate = self.fieldDrain / fieldNegPercent
        self.shieldCharge -= min(float(self.fieldDrain), self.shieldCharge)
        # =========== endregion: Shield Calculation ============ #

        # ============== region: Fuel Calculation ============== #
        # Last number is base fuel usage rate
        self.fuelUseRate = self.tempDrainFactor * (1 - coreSat) * (0.001 * self.reactorFuelUsageMultiplier)
        if self.reactableFuel > 0:
            self.convertedFuel += self.fuelUseRate
            self.reactableFuel -= self.fuelUseRate
        # ============ endregion: Fuel Calculation============== #

        # ============== region: Explosion ============== #
        if self.shieldCharge <= 0 and self.temperature > 2000 and self.reactorState != ReactorState.BEYOND_HOPE:
            self.reactorState = ReactorState.BEYOND_HOPE
        # ============ endregion: Explosion ============= #

    def updateCriticalState(self):
        self.shieldCharge = self.rand.randint(0, max(1, int(self.maxShieldCharge * 0.01)))
        if self.disableLargeReactorBoom:
            if self.explosionCountdown == -1:
                self.explosionCountdown = 1200 + self.rand.randint(0, 2400)
            elif self.explosionCountdown <= 0:
                self.Boom()

            return None

        self.minExplosionDelay -= 1

        if self.explosionCountdown == -1:
            self.minExplosionDelay = 1199 + self.rand.randint(0, 2400)
            self.explosionCountdown = (60 * 20) + max(0, self.minExplosionDelay)
        elif self.explosionCountdown <= 0:
            self.Boom()

    def canCharge(self):
        return self.reactorState in (
        ReactorState.COLD, ReactorState.COOLING) and self.reactableFuel + self.convertedFuel >= 144

    def canActivate(self):
        return self.reactorState in (ReactorState.WARMING_UP, ReactorState.STOPPING) and self.temperature >= 2000 and ((self.saturation >= self.maxSaturation // 2 and self.shieldCharge >= self.maxShieldCharge // 2) or self.reactorState == ReactorState.STOPPING)

    def canStop(self):
        return self.reactorState in (ReactorState.RUNNING, ReactorState.WARMING_UP)

    def chargeReactor(self):
        if self.canCharge():
            print("Reactor: Start Charging")
            self.reactorState = ReactorState.WARMING_UP
        else:
            print("Reactor: Cannot Charge")

    def activateReactor(self):
        if self.canActivate():
            print("Reactor: Activate")
            self.reactorState = ReactorState.RUNNING
        else:
            print("Reactor: Cannot Activate")

    def shutdownReactor(self):
        if self.canStop():
            print("Reactor: Shutdown")
            self.reactorState = ReactorState.STOPPING
        else:
            print("Reactor: Cannot Shutdown")

    def toggleFailSafe(self):
        self.failSafeMode = not self.failSafeMode
        print("Reactor: FailSafe" + ('Enabled' if self.failSafeMode else 'Disabled'))

    def Boom(self):
        self.reactorState = ReactorState.BOOMED
        print("Reactor: Boomed")

    def update(self):
        self.updateCoreLogic()
        self.tick += 1

    def injectEnergy(self, rf: int):
        received = 0
        if self.reactorState == ReactorState.WARMING_UP:
            if not self.startupInitialized:
                return 0
            if self.shieldCharge < (self.maxShieldCharge // 2):
                received = min(rf, int(self.maxShieldCharge / 2) - int(self.shieldCharge) + 1)
                self.shieldCharge += float(received)
                if self.shieldCharge > self.maxShieldCharge // 2:
                    self.shieldCharge = self.maxShieldCharge // 2
            elif self.saturation < self.maxSaturation // 2:
                received = min(rf, int(self.maxSaturation / 2) - self.saturation)
                self.saturation += received
            elif self.temperature < 2000:
                received = rf
                self.temperature += received / (1000. + (self.reactableFuel * 10))
                if self.temperature > 2500:
                    self.temperature = 2500.
        elif self.reactorState in (ReactorState.RUNNING, ReactorState.STOPPING):
            tempFactor = 1.
            # If the temperature goes past 15000 force the shield to drain by the time it hits 25000 regardless of input.
            if self.temperature > 15000:
                tempFactor = 1. - min(1., (self.temperature - 15000.) / 10000.)

            self.shieldCharge += min(rf * (1. - (self.shieldCharge / self.maxShieldCharge)), self.maxShieldCharge - self.shieldCharge) * tempFactor
            if self.shieldCharge > self.maxShieldCharge:
                self.shieldCharge = self.maxShieldCharge

            return rf
        return received

    def extractEnergy(self, rf: int):
        if self.reactorState == ReactorState.RUNNING:
            sent = min(rf, self.saturation)
            self.saturation -= sent

    def getCoreDiameter(self):
        volume = (self.reactableFuel + self.convertedFuel) / 1296.
        volume *= 1 + (self.temperature / self.MAX_TEMPERATURE) * 10.
        diameter = (volume / (4 / 3 * 3.1415926)) ** (1. / 3) * 2
        return max(0.5, diameter)

    def reset(self):
        self.tick = 0
        self.rand = Random()
        # This is the current operational state of the reactor.
        self.reactorState = ReactorState.COLD
        # Remaining fuel that is yet to be consumed by the reaction.
        self.reactableFuel = 0
        # Fuel that has been converted to chaos by the reaction.
        self.convertedFuel = 0
        # temperature
        self.temperature = 0
        self.MAX_TEMPERATURE = 10000
        # shield
        self.shieldCharge = 0
        self.maxShieldCharge = 0
        # This is how saturated the core is with energy.
        self.saturation = 0
        self.maxSaturation = 0
        # dynamic characteristics
        self.tempDrainFactor = 0
        self.generationRate = 0
        self.fieldDrain = 0
        self.fieldInputRate = 0
        self.fuelUseRate = 0

        self.startupInitialized = False
        self.failSafeMode = False

        # Explody Stuff!
        self.explosionCountdown = -1
        self.minExplosionDelay = 0

    def getReactorInfo(self):
        info = dict(
            tick=self.tick,
            temperature=self.temperature,
            fieldStrength=self.shieldCharge,
            maxFieldStrength=self.maxShieldCharge,
            energySaturation=self.saturation,
            maxEnergySaturation=self.maxSaturation,
            fuelConversion=self.convertedFuel,
            maxFuelConversion=self.convertedFuel + self.reactableFuel,
            generationRate=self.generationRate,
            fieldDrainRate=self.fieldDrain,
            fuelConversionRate=self.fuelUseRate,
            status=self.reactorState,
            statusName=self.stateName,
            failSafe=self.failSafeMode
        )
        return info

    @property
    def stateName(self):
        for k, v in ReactorState.__dict__.items():
            if isinstance(v, int) and v == self.reactorState:
                return k

    @property
    def info(self):
        return self.getReactorInfo()
