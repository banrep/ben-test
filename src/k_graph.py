#! /usr/bin/python3
#

import re
import sys
import gc
import time
import matplotlib.pyplot as pyplot
import numpy as np
from k_header import *


gMaxY = 0
gMinY = 0

def setGraphMaxMin(max,min):
    global gMaxY, gMinY   
    gMaxY = max
    gMinY = min

def getGraphMaxMin():
    global gMaxY, gMinY   
    return(gMaxY, gMinY)

def drawGraph(data,FileName):
    global comment
    comment="Running Graph All"
    print("start graph All")
    fig=pyplot.figure()
    ax=fig.add_subplot(111)
    ax.set_title('Whole Fireing', fontsize=6)
    ax.set_xlabel('Time/Hours', fontsize=6)
    ax.set_ylabel('Temperature/degC', fontsize=6)
    ax.yaxis.tick_right()
    ax.yaxis.set_ticks_position('both')
    ax.tick_params(axis='both', which='major', labelsize=6)
    ax.tick_params(axis='both', which='minor', labelsize=6)
    ax.yaxis.grid() #vertical lines
    ax.xaxis.grid() #horizontal lines
    
    EndPoint=len(data[0]) -3
    print("EndPoint:", EndPoint)
    if (EndPoint < 3 ):
        print("EndPoint", EndPoint)
        return()
    if data[1][1] < data[2][1]:
        ymin =data[1][1]
    else:
        ymin =data[2][1]
    if data[1][2] > data[2][2]:
        ymax = data[1][2]
    else:
        ymax = data[2][2]
    print('min=', ymin, " max=",ymax)
    if (ymax > 1300):
        ymax = 1300
    if (ymin < -300):
        ymin = -300
    if gMaxY != 0:
        ymax = gMaxY
    if gMinY != 0:
        ymin = gMinY
    print('min=', ymin, " max=",ymax)
    pyplot.ylim((ymin,ymax))
    pyplot.yticks(np.arange(ymin, ymax+20, 20))
    #pyplot.xticks(np.arange(0, (data[0][EndPoint] +1), 10))
     #   pyplot.xticks(np.arange(0, data[0][EndPoint] +1, 0.166666667))

    CM=0
    #print("time:",data[0]['timeE'])
    for plotLine in data[1:]:
        #print("plotline:",plotLine)
        pyplot.plot(data[0][3:],plotLine[3:],label=plotLine[0],linewidth=LineWidthMap[CM],color=ColourMap[CM])
        time.sleep(.1)
        CM += 1
    pyplot.legend(loc=2,prop={'size':6})
#    pyplot.set_size_inches(8.5,11)
    pyplot.savefig(FileName, dpi=150)
    fig.clf()
    pyplot.close()
    gc.collect()
    print("End graph")
    return()


if __name__ == '__main__':
    from k_log import point, readLog, log
    readLog("./log/1.log")
    print("log len",len(log))
    d = point.selectGraph(300, ('timeE', 'tempTop','tempBot',"tempTopRate5m","gasPos",'tempBotRate30s'))
              #["timeE", min, max, data....]
    print("d len",len(d[0]))
    drawGraph(d, "xx")
    exit()
    if sys.argv[1] == "graph":
        from k_log import point, readLog, log
        readLog("./log/1.log")
        
        d = point.selectGraph(400, ('timeE', 'tempTop',"tempTopRate10s"))
        drawGraph(d, "xx")
        

