#!/usr/bin/env python3
#! /usr/bin/python3

#i2cdetect -y 1

import time 
from time import gmtime, strftime
import os
from k_temp import get as k_temp_get
from k_motor import getFlue, getGas, gasZero, flueZero, gasChange, flueChange
from k_log import addPoint, selectGraph, writePoint, logWrite, point, makeTimeFile, makeLogFile, createGuidList, getNextStep, getLogTop, getCurrentStep
import socket
if socket.gethostname() == "raspberrypi":
    from k_gas import get as gas_get
else:
    def gas_get():
        return 15
from k_header import CTempTop, CTempBot, TRiseError, GasStep

OPT=True
#soak=False
Auto=True

RunLog=False
RunGraph=False
RunFire=False
RunLogP=False
RunGraphP=False
RunFireP=False
RuningLog=False
RuningGraph=False
RuningFire=False

graphStepTime=300
fireSleepTime = 20
logSleepTime = 5
graphSleepTime=300


wholeFireGraph=""

def rm(filename):
    if os.path.exists(filename):
        os.remove(filename)

#def setGraphSetTime(n):
#    global graphStepTime
#    graphStepTime = n

def setGraphLoopTime(n):
    global graphSleepTime
    graphSleepTime = n

def setLogLoopTime(n):
    global logSleepTime
    logSleepTime = n

def getLoopTime():
    global graphSleepTime, logSleepTime
    return(logSleepTime, graphSleepTime)

def getGraphFile():
    return wholeFireGraph

def getStatus():
    return([{"Log":RuningLog}, {"Graph":RuningGraph}, {"Fire":RuningFire}])

####################################################################################################
def graphRun(action=""):
    global RunGraph, RunGraphP, wholeFireGraph, runningGraph, graphStepTime
    if action == "pause":
        RunGraphP = False
    elif action == "restart":
        RunGraphP = True
    elif action == "stop":
        RunGraph = False   
    elif action == "start" or action == "":
        RunGraph=True
        RunGraphP=True
        from k_graph import drawGraph
        logWrite("I Starting - Graph ")
        new=""
        old=""
        while (RunGraph):
            while (RunGraphP):
                runningGraph = True
                d = selectGraph(graphStepTime, ('timeE', 'tempTop','tempBot',"tempTopRate5m",'tempBotRate30s','gas','gasRate60s'))
                if d[0] != 0:
                    #["timeE", min, max, data....]
                    #print("d len",len(d[0]))
                    new = makeTimeFile("wholeFireGraph.png")
                    drawGraph(d,new )
                    old = wholeFireGraph
                    wholeFireGraph = new
                    rm(old)
                logWrite("I, Graph file created " + new + " Old: " + old)
                time.sleep(graphSleepTime)
        runningGraph = False
        logWrite("I, Ending - Graph ")
                

#########
def fireRun(action=""):
    global RunFire, RunFireP, runningFire
    if action == "pause":
        RunFireP = False
    elif action == "restart":
        RunFireP = True
    elif action == "stop":
        RunFire = False   
    elif action == "start" or action == "":
        global TempStepAve
        global FireRunEnd
        global comment
        global GuideStep
        soak = False
        RunFire = True
        RunFireP = True
        time.sleep(2)
        NewStep=True
        endSoakTime=0
        logWrite("I, Starting - Fire ")
        createGuidList(0)
        guideStep = getNextStep()
        while RunFire:
            while RunFireP:
                runningFire = True
                currentTopLog = getLogTop()
                logWrite("F, GuideStep: " + str(guideStep["step"]))
                if (guideStep["step"] == 0):
                #End of run, finish
                    NewStep=False
                    RunFire=False
                    RunFireP=False
                    setGas(0)
                    setFlue(0)
                    logWrite("F, Ending Fire Run")
                    break
                
                if (NewStep):
            # Set Flue only when its a new step
                    setFlue(guideStep["flue"])
                    NewStep=False

                if (guideStep["setRate"] == 0 and not soak):
                #Start a new Soak if we are not doing one, cant have two soaks together
                    endSoakTime=currentTopLog["timeE"] + (guideStep["soakTime"] * 60)
                    logWrite("F, Starting Soak " + str(endSoakTime))
                    soak=True
                                     
                # Now see if we need to go faster or slower temp can change in 35 sec
                SetRate(guideStep["setRate"])
            #   optimise()
            #   reduce(GuideList[GuideStep][GReduce])
                logWrite("Soak=" +str(soak) +" Guide=" +str(guideStep["setTemp"]) +" current=" +str(currentTopLog["tempTopAve10s"]))
                if (soak and endSoakTime > currentTopLog["timeE"]) or (not soak and (guideStep["setTemp"] < currentTopLog["tempTopAve10s"])):
            # Set new Step
                    guideStep = getNextStep()
                    NewStep=True
                    StepStartTime = getLogTop()["timeE"] # save the start point of this step StepStartTime
                    info = "F, New Guide " +str(guideStep)
                    logWrite(info)
                time.sleep(fireSleepTime)

            #setGas(OFF)
            #setFlue(OFF)
            logWrite("F, Ending - Fire ")
            FireRunEnd=True
            runningFire = False
            return

####################################################################################################
def logRun(action=""):
    global RunLog, RunLogP, runningLog
    if action == "pause":
        RunLogP = False
    elif action == "restart":
        RunLogP = True
    elif action == "stop":
        RunLog = False   
    elif action == "start" or action == "":
        RunLog=True
        RunLogP=True
        makeLogFile()
        p=point()
        r=[]
        for item in p.data:
            r.append(item)
        rr="H, "+str(r).strip('[]')
        logWrite(rr)
        logWrite("I, Starting - Logging ")
        while (RunLog):
            while (RunLogP):
                runningLog = True
                #logWrite("1")
                tempT, vTop = k_temp_get(CTempTop)
                tempB, vBot = k_temp_get(CTempBot)
                #logWrite("2")
                gasP = getGas()
                gasN = gas_get()
                #logWrite("3")
                flueP = getFlue()
                #logWrite("4")
                opt = 0
                comment = ""
                p = addPoint(tempT,tempB,gasP,gasN,flueP,opt,vTop,vBot,comment)
                #print("p=",p.data)
                writePoint(p)
                time.sleep(logSleepTime)
        runningLog = False
#Stopping Logging
        logWrite("I, Ending Logging in 100s")
        time.sleep(100)
        logWrite("I, Ended Logging NOW")
        logClose()


def heartBeat():
    startTime=time.time()
    return

########################################################################
def optimiseRun():
    global opt
    global comment
    time.sleep(30)
    comment="Starting Optimise"
    info = "I, " + comment
    logWrite(info)
    while Run:
        while OPT:
            sleep(2)
        FlueChange(-FlueStep)
        time.sleep(FlueChangeSleep)
        while (RateChange(FlueChangeSleep) > 0):
            print("Opt",RateChange(FlueChangeSleep))
            FlueChange(-FlueStep)
            time.sleep(FlueChangeSleep)
        while (RateChange(FlueChangeSleep) < 0):
            print("Opt",RateChange(FlueChangeSleep))
            FlueChange(+FlueStep * 2)
            time.sleep(FlueChangeSleep)
        FlueChange(FlueStep)
        opt = True
        comment="Optimise done"
        info = "I, " + comment
        time.sleep(100)
    comment="Optimise End"
    info = "I, " + comment
    logWrite(info)
    return()
########################################################################


def optimiseRun2():
    global opt
    global comment
    time.sleep(30)
    comment="Starting Optimise2"
    print("Starting Optimise2")
    while Run:
        while OPT:
            sleep(2)
        FlueChange(-FlueStep)
        time.sleep(FlueChangeSleep)
        print("opt rate=",RateChange(FlueChangeSleep))
        if (RateChange(FlueChangeSleep) > 0):	 #test to see if change in temp rate is up
            print("Opt",RateChange(FlueChangeSleep))
            FlueChange(-FlueStep)		 #close the flue a bit
            time.sleep(FlueChangeSleep)
        if (RateChange(FlueChangeSleep) < 0):
            print("Opt",RateChange(FlueChangeSleep))
            FlueChange(+FlueStep * 2)
            time.sleep(FlueChangeSleep)
        FlueChange(FlueStep)
        opt = True
        comment="Optimise done"
        print("Optimise done")
        time.sleep(10)
    comment="Optimise End"
    print("Optimise End")
    return()
########################################################################

	
def optimise():
    global opt
    print("Optimise Start")
    FlueChange(-FlueStep)
    time.sleep(FlueChangeSleep)
    while (RateChange(FlueChangeSleep) > 0):
        print("Opt",RateChange(FlueChangeSleep))
        FlueChange(-FlueStep)
        time.sleep(FlueChangeSleep)
    FlueChange(FlueStep)
    opt = True
    print("Optimise End")
    return()

##########
def SetRate(rise):
    if (not Auto):
        return()
    #end=len(log)-1
    GasStepMult=2
    currentLog = getLogTop()
    currentStep = getCurrentStep()
    info = "F, Wanted Rise=" +str(rise) +" 10s=" +str(currentLog['tempTopRate10s']) +" 30s=" +str(currentLog['tempTopRate10s']) +" 5m="+ str(currentLog['tempTopRate5m']) +" Step=" +str(currentStep['step']) +" Err=" +str(TRiseError*rise)
    logWrite(info)
    
    if (abs( rise * 10) > abs(currentLog['tempTopRate30s']) ): #See how far away we are
        GasStepMult=4
        info="F, Change Step Fast=" + str(GasStepMult)
        logWrite(info)
        
    if ( (DiffError( currentLog['tempTopRate5m'], rise, TRiseError*rise) == 1) or (DiffError(currentLog['tempStepRate'], rise, TRiseError*rise) == 1) ): #going too fast
        gasChange(-GasStep*GasStepMult*2)
        info="F, Going too Fast"
        logWrite(info)
#	optimise()
        return()

    if (DiffError(currentLog['tempTopRate10s'], rise, TRiseError*rise * 0.5) == -1): #Go faster
        info="F, Going too SLow"
        logWrite(info)
#	FlueChange(FlueStep)
        gasChange(GasStep*GasStepMult)
#	optimise()
        return()

    info="F, Going About Right"
    logWrite(info)
    return()


"""
def optimize(wantedrise, reduction):
	if wanted rise < actual rise then 
	{
		Gas += 1
		if rate of rise < then
		{
 			flue ++ until rate of rise platoes
  		}
	}
	if wanted rise > actual rise then
	{
 		gas.until rate correct
	return
"""

#

"""
get planned reduction
get reduction
if reduction < planned reduction then flue.
if reduction > planned reduction then flu++
"""

##########
def reduce(rate):
    if (rate == 0): return
    optimise()
    FlueChange(-FlueChange)
    return

############
def InitAll():
    global LogOut
    global RunLog
    global RunGraph
    global RunFire
    

    RunLog=True
    RunGraph=True
    RunFire=True
    LogExt=strftime("%Y%m%d%H%M", gmtime())
    LogFile="./"+LogExt+".log"
    print("I, Starting - Logging ",LogFile)
    LogOut=open(LogFile,"w")
##########
def ReadUserComment():
    line=""
    if (os.path.exists(CommentFile)):
        fd=open(CommentFile, "r")
        line=fd.read()
        line=line.rstrip('\n')
        fd.close()
        os.remove(CommentFile)
    #read from web page
    return(line)

##########
def PLog(row):
    global PLogH
    if ((PLogH%10) == 0):
        print('%4d'%row[CLogStep], '=%5.2f' % (row[CTimeE] - log[0][CTimeE]))
#	print(' '.join('%5s' % x for x in FullHeading))
        print(' '.join('%5s' % x for x in Heading1))
        print(' '.join('%5s' % x for x in Heading2))
    print (' '.join('%5.1f' % row[x] for x in range(2, len(row)-1)))
#   print('%s' %row[len(row)-1])
    PLogH += 1

##########
def GasRun():
    global GasPos
    global GasStep
    global comment
    print ("Starting - GasRun")
    comment="Starting - GasRun"
    while Run:
        gasChange(GasStep)
        LogOut.write("G, "+str(GasStep)+'\n')
        time.sleep(.1)
    print ("Ended - GasRun")
    comment="Ended - GasRun"

##########
def FlueRun():
    global FluePos
    global FlueStep
    global comment
    comment="Starting - FlueRun"
    print ("Starting - FlueRun")
    while Run:
        FlueChange(-FlueStep)
        LogOut.write("F, "+str(-FlueStep)+'\n')
        time.sleep(.1)
    comment="Ended - FlueRun"
    print ("Ended - FlueRun")
    return()

#######################################################################
# find the difference within the error
def DiffError(actual,wanted,error): 
    if ((actual - error) > wanted):# if the actual is bigger then wanted with in error
        return 1
    if ((actual + error) < wanted):# if the wanted is bigger then actual with in error
        return -1
    return(0) # they are the same within error
	


def startAll():
    return()


import sys
if __name__ == '__main__':
    from k_motor import init
    init()
    while True:
        flue=int(input("flue:"))
        print("FluePos1:", fluePos)
        setFlue(flue)
        print("FluePos2:", fluePos)
    #if sys.argv[1] == "vt":
        #exit()
    #else:
    #logRun()


'''
#TESTING
###########################################################
#Readv2t()
#Readv2t()
#print("Temp",GetTemp(CTempTop))
##############################################

#############################################################################################
InitAll()
ReadGuide(1)
vt = Readv2t(v2tFile)
vtTop = Readv2t(v2tTopFile)
vtBot = Readv2t(v2tBotFile)
threading.Thread(target = LogRun).start()
time.sleep(2)
threading.Thread(target = HttpServerRun).start()
threading.Thread(target = ReadUserComment).start() 
time.sleep(20)
threading.Thread(target = DrawGraphRun).start()
time.sleep(2)
threading.Thread(target = FireRun).start()

time.sleep(20)
#threading.Thread(target = OptimiseRun2).start()

#Testing Apps
#threading.Thread(target = FlueTest).start() 
#threading.Thread(target = GasTest).start() 
#threading.Thread(target = FlueRun).start() 
#threading.Thread(target = GasRun).start()
#threading.Thread(target = DrawGraph2Run).start()

#FireRun()
#LogRun()

print("Runnin and now waiting")
s=""
#While (s != "stop"):
s=input()
print("Still running, use stop to stop")

print("Stopping and now waiting to Stop")
RunFire=False
time.sleep(5)
FreeMove(1)

print("Runnin and now waiting")
s=""
#While (s != "stop"):
s=input()
print("Waiting for all to stop")
time.sleep(100)
FreeMove(1)
quit()
'''
