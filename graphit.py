#!/home/tomh/rtl433/venv/bin/python3
import io,sys,os
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import dateutil.parser
from pandasql import sqldf
import datetime
from matplotlib.dates import DateFormatter, DayLocator
from matplotlib.ticker import Formatter
import matplotlib.dates as mpd
import datetime
from zoneinfo import ZoneInfo
from datetime import datetime
import matplotlib as mpl
from glob2 import glob

from scipy.signal import savgol_filter
from scipy.interpolate import CubicHermiteSpline, Akima1DInterpolator, PchipInterpolator
mpl.rcParams['timezone']='America/Chicago'

lld=[]
for fn in sorted(glob('data*.json')):
    with open(fn,'r') as f:
        try:
            lis = f.readlines()
        except Exception as e:
            print(f"while reading file 'data.json': {e}")
            sys.exit(0)

        for li in lis:
            if li == "": 
                print("read empty line.")
                continue
            try:
                ld = json.loads(li)
            except Exception as e:
                print(f"exception while json.load line: {e}")
                print(li)
                continue
            lld.append(ld)


plt.close('all')
pdf=pd.DataFrame(lld)

pdf['timestamp'] = [ mpd.dateutil.parser.parse(x).timestamp() for x in list(pdf['time']) ]

# select dates within 1 week

mostrecentdate =mpd.dateutil.parser.parse(list(pdf['time'])[-1]).timestamp()
print(mostrecentdate)


# filter only records that have valid 'id' field (not Nan)
#ids=pdf.id
goodid= (~(pd.isna(pdf.id))) &  (~(pd.isna(pdf.Consumption))) & (pdf['timestamp'] > (mostrecentdate - 60*60*24*6))
pdf = pdf[goodid]
pdf['newid'] = [str(x) for x in pdf.id]

# idenitfy the ID with the most data, that'd be us.
ids = sqldf("select newid,count(*) N,avg(rssi) avg_rssi from pdf group by newid order by avg_rssi")
pdf=pdf[pdf.newid == list(ids.newid)[-1]]

mpl.rcParams['lines.linewidth']=1
mpl.rcParams['lines.markersize']=1.5



#timestamps = np.int64([ datetime.datetime.timestamp(dateutil.parser.parse(ts)) for ts in pdf.time ])

# raw data dates
dates = np.array([ np.datetime64(ts) for ts in pdf.time ])

# raw dates converted to numbers
datenums = np.uint64(dates)


# consumption smoothed, then interpolated onto regular spaced dates

comp=np.int32(pdf.Consumption)

#find all the places where the meter reading has increased since the last reading
atchange = np.where(np.diff(comp)>0)[0]+1

if atchange[-1] < len(datenums)-1:
    atchange = np.int32(list(atchange) + [(len(datenums)-1)])

if atchange[0] > 0:
    dates = dates[atchange[0]:]
    datenums = datenums[atchange[0]:]
    comp = comp[atchange[0]:]
    atchange = atchange - atchange[0]

# the new value at the time of change is the closest to reality that we can possibly get.

acdates = datenums[atchange]
accons  = np.array(comp)[atchange]

# compute interpolation function
#yyy = CubicHermiteSpline(datenums,comp,1)
yyy = PchipInterpolator(acdates, accons)
#yyy = Akima1DInterpolator(acdates, accons, method='makima')

# establish rounding interval in seconds
SMOOTH_INT = 60
# regular spaced dates 
regdates = np.arange(datenums.min(),datenums.max(), SMOOTH_INT)

# compute interpolation at regular datetime intervals
sregy1 = yyy(regdates)
sregy2 = np.interp(regdates,acdates,accons)
sregy = (sregy1*0.9 + sregy2*0.1)

#sregy = savgol_filter(regy, 5, 1, deriv=0, mode='interp' )


# diff of consumption == consumption rate of cf/hr
INT_PER_HR = 60*60/SMOOTH_INT
regcr = np.diff(sregy)/(1/INT_PER_HR)

# regular spaced date numbers converted back to dates
regdatedates = pd.to_datetime(regdates,unit='s',utc=True)

# find relative minima to help identify likely water usage events
#first smooth the curve
smoothcr = savgol_filter(regcr,95,1)

diffcr = np.diff(smoothcr)
diffcr1 = diffcr[1:]
diffcr0 = diffcr[:-1]
minimaraw = np.where((diffcr0<0) & (diffcr1>0))[0]+1

minimadates = regdatedates[minimaraw]
minimadatenums = regdates[minimaraw]
minimacf = regcr[minimaraw]


fig,ax = plt.subplots(2,figsize=(11,8.5), height_ratios=[1,3])
fig.tight_layout()
fig.set_size_inches(11,8.5)
fig.set_dpi(80)

n=0
m=1
ax[n].plot(dates,comp,'.',label="Meter readings")
ax[n].plot(regdatedates,sregy,'-',label='smoothed meter readings',lw=1)
ax[n].plot(acdates/60/60/24,accons,'.',ms=4, label='interpolation points', color='#FF5555')
ax[n].legend()
#ax[n].set_xlim(xlim)
ax[n].xaxis.set_major_formatter(DateFormatter('%a %Hh'))
ax[n].set_title('meter readings')

ax[m].plot(regdatedates[:-1],regcr,'-',label="Consumption rate")
ax[m].set_ylim(0,regcr.max()*1.3)
leftedge = regdates[0]/86400
rightedge = regdates[-1]/86400
lastedgenum = regdates[0]/86400
lastedgefmt = DateFormatter("%d %H")(lastedgenum)
for di in range(1,len(regdates)+1):
    if di == len(regdates):
        if int(lastedgefmt[3:]) < 12:
            thisedgefmt = 'xx 12'
        else:
            thisedgefmt = 'xx 00'
    else:
        thisedgenum = regdates[di]/86400
        thisedgefmt = DateFormatter("%d %H")(thisedgenum)
    #print(f"thisedgefmt={thisedgefmt} hr={thisedgefmt[3:]}")
    if lastedgefmt != thisedgefmt and thisedgefmt[3:] in ['00','12']:
        # make new rectangle from lastedge to here
        if thisedgefmt[3:]=='00':
            spancolor='#eeeeee'
            lbl = "PM"
        else:
            spancolor='#ffffff'
            lbl = "AM"
        ax[m].axvspan(lastedgenum,thisedgenum,color=spancolor)
        ax[n].axvspan(lastedgenum,thisedgenum,color=spancolor)
        ax[m].text((lastedgenum+thisedgenum)/2, regcr.max()*1.12, DateFormatter('%a\n%m/%d')(lastedgenum).upper()+"\n"+lbl,ha='center')
        ax[n].text((lastedgenum+thisedgenum)/2, regcr.max()*1.12, DateFormatter('%a\n%m/%d')(lastedgenum).upper()+"\n"+lbl,ha='center')
        lastedgenum = thisedgenum
        lastedgefmt = thisedgefmt

#ax[m].set_xlim(xlim)
ax[m].xaxis.set_major_formatter(DateFormatter('%H:%M'))
ax[m].set_title('smoothed consumption rate')
ticklist = list(minimadatenums/86400)
ticklist = [ regdates[0]/86400 ] + ticklist + [ regdates[-1]/86400 ]
ax[m].xaxis.set_ticks(ticklist);
for i in range(len(minimaraw)+1):
    if i < len(minimaraw):
        ax[m].axvline(minimadates[i],0,0.021,c='#0000FF',linestyle='dashed')
        ax[m].axvline(minimadates[i],0,1,c='#aaaaFF',linestyle='dashed')
        ax[n].axvline(minimadates[i],0,1,c='#0000FF',linestyle='dashed')
        #ax[m].plot(minimadates[i],minimacf[i],'.',ms=5,color='black')

    if i == len(minimaraw):
        ax[m].axvline(regdates[i]/86400,0,0.021,c='#0000FF', linestyle='dashed')
        ax[m].axvline(regdates[i]/86400,0,1,c='#aaaaFF', linestyle='dashed')
        ax[n].axvline(regdates[i]/86400,0,1,c='#0000FF', linestyle='dashed')
        lefti = minimaraw[i-1]
        righti = len(sregy)-1
    elif i == 0:
        ax[m].axvline(regdates[-1]/86400,0,0.021,c='#0000FF', linestyle='dashed')
        ax[m].axvline(regdates[-1]/86400,0,1,c='#aaaaFF', linestyle='dashed')
        ax[n].axvline(regdates[-1]/86400,0,1,c='#0000FF', linestyle='dashed')
        lefti  = 0
        righti = minimaraw[i]
    else:
        lefti  = minimaraw[i-1]
        righti = minimaraw[i]
    val = sregy[righti]-sregy[lefti]
    maxcr = regcr[lefti:righti].max()
    avgcr = regcr[lefti:righti].mean()
    maxi = np.where(regcr[lefti:righti]==maxcr)[0]
    maxdate = regdates[lefti+maxi]/86400
    middate = (regdates[lefti]+regdates[righti])/2/86400
    if maxcr < avgcr*2:
        plotdate = middate
    else:
        plotdate = maxdate
    val = val * 7.48
    if maxcr < regcr.max()*0.02:
        maxcr =regcr.max()*0.02
    ax[m].text(
            #(regdates[lefti]+regdates[righti])/2/86400,
            plotdate,
            maxcr,f"{val:.0f}", ha='center',va='bottom', color='#0000FF', fontsize=9)

ax[m].fill_between(regdatedates[:-1],regcr)

labels=ax[m].get_xticklabels()
for lbl in labels:
    lbl.set_rotation(70)
    lbl.set_rotation_mode('anchor')
    lbl.set_va('center')
    lbl.set_ha('right')
    lbl.set_fontsize(8)

tstamp = datetime.now().strftime('%Y%m%d_%H%M%S')
plt.savefig(f"/var/www/html/waterusage/chart{tstamp}.png")
os.rename(f'/var/www/html/waterusage/chart{tstamp}.png','/var/www/html/waterusage/waterusage.png')
