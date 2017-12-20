#!/usr/bin/python
#
# Creates a C code lookup table for doing ADC to temperature conversion
# on a microcontroller
# based on: http://hydraraptor.blogspot.com/2007/10/measuring-temperature-easy-way.html
"""Thermistor Value Lookup Table Generator
Updated by Shohei Aoki, 2017

Generates lookup to temperature values for use in a microcontroller in C format based on:
http://hydraraptor.blogspot.com/2007/10/measuring-temperature-easy-way.html

The main use is for Arduino programs that read data from the circuit board described here:
http://make.rrrf.org/ts-1.0

Usage: python createTemperatureLookup.py [options]

Options:
  -h, --help            show this help
  --r0=...          thermistor rating where # is the ohm rating of the thermistor at t0 (eg: 10K = 10000)
  --t0=...          thermistor temp rating where # is the temperature in Celsuis to get r0 (from your datasheet)
  --beta=...            thermistor beta rating. see http://reprap.org/bin/view/Main/MeasuringThermistorBeta
  --r1=...          R1 rating where # is the ohm rating of R1 (eg: 10K = 10000)
  --r2=...          R2 rating where # is the ohm rating of R2 (eg: 10K = 10000)
  --num-temps=...   the number of temperature points to calculate (default: 20)
  --max-adc=...     the max ADC reading to use.  if you use R1, it limits the top value for the thermistor circuit, and thus the possible range of ADC values
  --vcc=...         Supply voltage Vcc which coordinates with ADC reference Vadc
"""

from math import *
import sys
import getopt

class Thermistor:
    "Class to do the thermistor maths"
    def __init__(self, r0, t0, beta, r1, r2, max_adc, vcc):
        self.r0 = r0                        # stated resistance, e.g. 10K
        self.t0 = t0 + 273.15               # temperature at stated resistance, e.g. 25C
        self.beta = beta                    # stated beta, e.g. 3500
        self.vadc = vcc                     # ADC reference
        self.vcc = vcc                      # supply voltage to potential divider
        self.k = r0 * exp(-beta / self.t0)   # constant part of calculation
        self.max_adc = max_adc

        if r1 > 0:
            self.vs = r1 * self.vcc / (r1 + r2) # effective bias voltage
            self.rs = r1 * r2 / (r1 + r2)       # effective bias impedance
        else:
            self.vs = self.vcc                   # effective bias voltage
            self.rs = r2                         # effective bias impedance

    def temp(self,adc):
        "Convert ADC reading into a temperature in Celcius"
        v = adc * self.vadc / self.max_adc # convert the 10 bit ADC value to a voltage
        r = self.rs * v / (self.vs - v)     # resistance of thermistor
        return (self.beta / log(r / self.k)) - 273.15        # temperature

    def setting(self, t):
        "Convert a temperature into a ADC value"
        r = self.r0 * exp(self.beta * (1 / (t + 273.15) - 1 / self.t0)) # resistance of the thermistor
        v = self.vs * r / (self.rs + r)     # the voltage at the potential divider
        return round(v / self.vadc * self.max_adc)  # the ADC reading

def main(argv):

    r0 = 100000;
    t0 = 25;
    beta = 4267;
    r1 = 0;
    r2 = 4700;
    num_temps = int(61);
    vcc = 3.279
    max_adc_raw = 1023 

    try:
        opts, args = getopt.getopt(argv, "h", ["help", "r0=", "t0=", "beta=", "r1=", "r2=", "max-adc=", "vcc="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt == "--r0":
            r0 = float(arg)
        elif opt == "--t0":
            t0 = int(arg)
        elif opt == "--beta":
            beta = int(arg)
        elif opt == "--r1":
            r1 = float(arg)
        elif opt == "--r2":
            r2 = float(arg)
        elif opt == "--max-adc":
           max_adc_raw = int(arg)
        elif opt == "--vcc":
            vcc = float(arg)

    if r1:
        max_adc = int(max_adc_raw * r1 / (r1 + r2));
    else:
        max_adc = max_adc_raw
    increment = int(max_adc/(num_temps-1));

    t = Thermistor(r0, t0, beta, r1, r2, max_adc, vcc)

    adcs = list(range(1, max_adc, increment));
    #print(adcs)
    # adcs = [1, 18, 35, 52, 69, 86, 103, 120, 137, 154, 171, 188, 205, 222, 239, 256, 273, 290, 307, 324, 341, 358, 375, 392, 409, 426, 443, 460, 477, 494, 511, 528, 545, 562, 579, 596, 613, 630, 647, 664, 681, 698, 715, 732, 749, 766, 783, 800, 817, 834, 851, 868, 885, 902, 919, 936, 953, 970, 987, 1004, 1021]

#   adcs = [1, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 110, 130, 150, 190, 220,  250, 300]
    first = 1

    print("// Thermistor lookup table for RepRap Temperature Sensor Boards (http://make.rrrf.org/ts)")
    print("// Updated by Shohei Aoki, 2017 ")
    print("// Made with createTemperatureLookup.py (http://svn.reprap.org/trunk/reprap/firmware/Arduino/utilities/createTemperatureLookup.py)")
    print("// ./createTemperatureLookup.py --r0=%s --t0=%s --r1=%s --r2=%s --beta=%s --max-adc=%s --vcc=%s" % (r0, t0, r1, r2, beta, max_adc, vcc))
    print("// r0: %s" % (r0))
    print("// t0: %s" % (t0))
    print("// r1: %s" % (r1))
    print("// r2: %s" % (r2))
    print("// beta: %s" % (beta))
    print("// max adc: %s" % (max_adc))
    print("// vcc: %s" % (vcc))
    print("#define NUMTEMPS %s" % (len(adcs)))
    print("short temptable[NUMTEMPS][2] = {")

    counter = 0
    for adc in adcs:
        counter = counter +1
        v = (adc/1024.0)
        T0 = t0 + 273.15               # temperature at stated resistance, e.g. 25C
        k = r0 * exp(-beta / T0)   # constant part of calculation
        if (1000*vcc-3320*v>0):
            temp_adc = int(round( (beta * 1.0) / (log (( 1000*vcc - 3320*v) / (k*v))) - 273.15))
        else:
            temp_adc = 0
        if counter == len(adcs):
            print("   {%s, %s}" % (adc, temp_adc))
        else:
            print("   {%s, %s}," % (adc, temp_adc))
    print("};")

def usage():
    print(__doc__)

if __name__ == "__main__":
    main(sys.argv[1:])


