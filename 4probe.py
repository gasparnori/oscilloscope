import csv
import visa
import math
from datetime import datetime, timedelta
import time
import sys
import untangle
import re

Debugging=True

if not Debugging:
###################### defining paths on the experiment computer ###########
    filepath='C:/GluSense/Calibration/'
    logPath = "C:/GluSense/GluSense Monitoring Software/Log/InVitroApp.txt"
else:
###################### defining paths for debugging ###########
    filePath = 'C:/Users/admin/OneDrive - Glusense medical/Nora/ivs calibration/'
    logPath = "InVitroApp.txt"

############# defining constants################

STDthres=150
VOLthres=30
TIMEthres=10000
fieldnames = ['concentration [mg/dL]', 'volume [mL]', 'V mean [mV]', 'V std [uV]', 'I mean [mA]',
              'I std [uA]', 'conductance [uS]', 'timestamp']

class measurement:
    """
    measurement point
    """
    def __init__(self, results):
        """

        :param results: a string
        """
        #self.timestamp=datetime.isoformat(datetime.now())
        self.timestamp=datetime.today()
        self.timestring=datetime.strftime(self.timestamp, '%d/%m/%Y %H:%M')

        r = results.split(',')
        print (r)
        #################  this needs to be updated  ######################
        ######channel 2
        self.I=1#float(r[.])*1000/50 # converted into mV then divided by 50 Ohm-->
        self.Istd=1#float(r[.+1])*1000000/50 # converted into uV then divided by 50 Ohm--> mA
        self.V=1#float(r[..])-float(r[...])*1000 # converted into mV
        self.Vstd = 1#float(r[19])*1000000 #converted into uV
        self.conductivity=self.I/self.V*(10^6) #10^6 is for uS conversion

    def getLog(self):
        """
        Opening log file getting current volume and concentration data

        :return:
        """
        ######open log file##########
        with open(logPath, 'r', encoding='utf8') as f:
            f = f.readlines()
            lastinfo = None
            for line in f:
                if "Current concentration" in line:
                    lastconcentration = line
                if "Current volume" in line:
                    lastvolume = line

        #checking if the timestamps are close enough
        date = datetime.strptime(lastconcentration.split(' [')[0], '%d/%m/%Y %H:%M')
        tdiff=int(abs((date - self.timestamp).total_seconds()) / 60) #in minutes
        if tdiff > TIMEthres:#the timestamp is more than 15 minutes old
            print ("Too old concentration values...")
            c='0'
            v='0'
            self.concentration=0
            self.volume=0
        else:
            c = lastconcentration.split('Current concentration')[1].split('\n')[0]
            self.concentration = float(c) if c is not None else None
            v=lastvolume.split('Current volume')[1].split('\n')[0]
            self.volume = float(v) if v is not None else None

        print("measurement at " + self.timestring + " \n\t",
              "concentration: ", c, " ml\n\t",
              "volume: ", v, " ml\n\t",
              " V:", str(self.V), "mV\n\t",
              " I:", str(self.I), "mV\n\t",
              "conductivity", str(self.conductivity))



#################initialization######################
def connectOsci():
    """
    Connecting to oscilloscope through pyvisa: It's important to have the right version \
    of VISA installed (in this case Keysight's own version)

    :return: oscilloscope object
    """
    try:
        rm = visa.ResourceManager()
        reslist = rm.list_resources()
        osci = None
        if len(reslist) > 0:
            osci = rm.open_resource(reslist[0])
        print(osci.query('*IDN?'))
        osci.timeout = 15000
        #osci.clear()
        #osci.write(':RECall:SETup:STARt "setup_0"')
        time.sleep(5)
        return osci
    except:
        print ("Oscilloscope not available")
        return None

def writeResultsAll(rows, filename):
    """
    Writing all results at once to the output file
    :param rows: list of ordered dicts
    :param filename: filename
    """
    with open(filename, mode='w') as results:
        writer = csv.DictWriter(results, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

def initOutput(filename):
    """
    initializing output file

    :param filename:
    """
    with open(filename, mode='w') as results:
        writer = csv.DictWriter(results, fieldnames=fieldnames, delimiter =",",lineterminator='\n')
        writer.writeheader()

def appendRow(filename, row):
    """
    Appending a row to the output file

    :param filename:
    :param row:
    """
    with open(filename, mode='a', delimiter =",",lineterminator='\n') as results:
        writer = csv.writer(results)
        writer.writerow(row)

def main():
    """
    main entry point. Uses ':MEASure:RESults?' query to measure the current settings on the oscilloscope.

    :return:
    """
    filename = datetime.strftime(datetime.now(), filePath + 'results_%Y_%m_%d_%H_%M.csv')
    osci = connectOsci()
    initOutput(filename)

    print("started recording at ", datetime.strftime(datetime.now(), '%m/%d/%Y %H:%M:%S'))

    offset=300
    step_done=False

    while True:
        if not step_done:
            if osci is not None:
                osci.write(':MEASure:STATistics ON')
                osci.write(':MEASure:STATistics:RESet')
                time.sleep(20)
                m=measurement(osci.query(':MEASure:RESults?'))
            else:
                m=measurement("1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21")
            m.getLog()

            if m.concentration is not None and m.volume is not None:
                if m.volume>=VOLthres and m.V2std < STDthres and m.diffrms < STDthres:
                    r=([{'concentration [mg/dL]': m.concentration,
                         'volume [mL]': m.volume,
                         'V mean [mV]': m.V,
                         'V std [uV]' : m.Vstd,
                         'I mean [mA]': m.I,
                         'I std [uA]': m.Istd,
                         'conductance [uS]': m.conductivity,
                         'timestamp': m.timestring}])
                    appendRow(filename, r)
                    step_done=True
                else:
                    ##unsuccesful measurement
                    time.sleep(10)
                    step_done=False
            else:
                time.sleep(offset)
                step_done=False
    print ("experiment finished")

main()
sys.exit(0)





