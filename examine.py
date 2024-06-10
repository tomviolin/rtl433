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
pdfraw=pd.DataFrame(lld)


# filter only records that have valid 'freq' field (not Nan)
#ids=pdf.id
goodfreq=np.logical_not(pd.isna(pdfraw['freq']))
pdfall = pdfraw[goodfreq].copy()
pdfall['newfreq'] = [str(x) for x in pdfall['freq']]
pdfall['newid'] = [str(x) for x in pdfall['id']]
pdfall['recdate'] = np.array([ np.datetime64(ts) for ts in pdfall.time ])

mpl.rcParams['lines.linewidth']=1
mpl.rcParams['lines.markersize']=1.5

# identify the ID with the most data, that'd be us.
idsdf = sqldf("select newid,count(*) N,avg(rssi) avg_rssi from pdfall group by newid order by N desc")

# raw data dates


plt.plot(pdfall['recdate'],pdfall['rssi'])
plt.show()
sys.exit()


for i in range(idsdf.shape[0]):
    pdf=pdfall[pdfall.newid == list(idsdf.newid)[i]]
    plt.scatter(pdf['freq'],pdf['rssi'],s=1, label=pdf['newid'])

plt.legend()
plt.savefig('examine.png')

sys.exit()



#timestamps = np.int64([ datetime.datetime.timestamp(dateutil.parser.parse(ts)) for ts in pdf.time ])


# raw dates converted to numbers
datenums = np.uint64(dates)


# consumption smoothed, then interpolated onto regular spaced dates

comp=pdf.Consumption+0

#find all the places where the meter reading has increased since the last reading
atchange = np.where(np.diff(comp)>0)[0]+1

if atchange[-1] < len(datenums)-1:
    atchange = np.int32(list(atchange) + [(len(datenums)-1)])

# the new value at the time of change is the closest to reality that we can possibly get.

acdates = datenums[atchange]
accons  = np.array(comp)[atchange]

# compute interpolation function
# yyy = CubicHermiteSpline(datenums,comp,comp*0)
yyy = PchipInterpolator(acdates, accons)
#yyy = Akima1DInterpolator(acdates, accons)

# establish rounding interval in seconds
SMOOTH_INT = 60
# regular spaced dates 
regdates = np.arange(datenums.min(),datenums.max(), SMOOTH_INT)

# compute interpolation at regular datetime intervals
sregy1 = yyy(regdates)
sregy2 = np.interp(regdates,acdates,accons)
sregy = (sregy1*0.7 + sregy2*0.3)

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


fig,ax = plt.subplots(2,figsize=(11,8.5))
fig.tight_layout()
fig.set_size_inches(11,8.5)
fig.set_dpi(80)

n=0
ax[n].plot(dates,pdf.Consumption,'.',label="Meter readings")
ax[n].plot(regdatedates,sregy,'-',label='smoothed meter readings',lw=1)
ax[n].legend()
#ax[n].set_xlim(xlim)
ax[n].xaxis.set_major_formatter(DateFormatter('%a %Hh'))
ax[n].set_title('meter readings')

'''
n += 1
#ax[n].plot(regdatedates,regy,'-',label="regularized meter readings",lw=1)
ax[n].plot(regdatedates,sregy,'-',label='smoothed meter readings',lw=1)
ax[n].legend()
#ax[n].set_xlim(xlim)
ax[n].xaxis.set_major_formatter(DateFormatter('%a %Hh'))
ax[n].set_title('regularized meter readings')
'''

n += 1
ax[n].plot(regdatedates[:-1],regcr,'-',label="Consumption rate")

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
        ax[n].axvspan(lastedgenum,thisedgenum,color=spancolor)
        plt.text((lastedgenum+thisedgenum)/2, regcr.max()*0.95, DateFormatter('%a %m/%d')(lastedgenum)+"\n"+lbl,ha='center')
        lastedgenum = thisedgenum
        lastedgefmt = thisedgefmt

#ax[n].set_xlim(xlim)
ax[n].xaxis.set_major_formatter(DateFormatter('%H:%M'))
ax[n].set_title('smoothed consumption rate')
ticklist = list(minimadatenums/86400)
ticklist = [ regdates[0]/86400 ] + ticklist + [ regdates[-1]/86400 ]
ax[n].xaxis.set_ticks(ticklist);
for i in range(len(minimaraw)+1):
    if i < len(minimaraw):
        ax[n].axvline(minimadates[i],0,0.5,c='#0000FF',linestyle='dashed')
        #ax[n].plot(minimadates[i],minimacf[i],'.',ms=5,color='black')

    if i == len(minimaraw):
        ax[n].axvline(regdates[i]/86400,0,0.5,c='#0000FF', linestyle='dashed')
        lefti = minimaraw[i-1]
        righti = len(sregy)-1
    elif i == 0:
        ax[n].axvline(regdates[-1]/86400,0,0.5,c='#0000FF', linestyle='dashed')
        lefti  = 0
        righti = minimaraw[i]
    else:
        lefti  = minimaraw[i-1]
        righti = minimaraw[i]
    val = sregy[righti]-sregy[lefti]
    val = val * 7.48
    plt.text((regdates[lefti]+regdates[righti])/2/86400,regcr.max()*0.5,f"{val:.2f}\ngallons", ha='center',va='top', color='#0000FF')

ax[n].fill_between(regdatedates[:-1],regcr)


'''
n+=1
filt_noise = np.logical_not( np.isnan(pdf.noise))
ax[n].plot(dates[filt_noise],pdf.noise[filt_noise],'.-',label="noise")
ax[n].plot(dates[filt_noise],pdf.rssi[filt_noise],'.-',label="signal")
ax[n].plot(dates[filt_noise],pdf.rssi[filt_noise]-pdf.noise[filt_noise],'.-',label="SNR")
ax[n].legend()
ax[n].set_xlim(xlim)
ax[n].xaxis.set_major_formatter(DateFormatter('%a %Hh'))
'''
'''
n+=1
filt_freq1 = np.logical_not(np.isnan(pdf.freq1))
ax[n].plot(dates[filt_freq1],(pdf.freq1[filt_freq1]-434)*100,'.--',label="freq1")
ax[n].plot(dates[filt_freq1],(pdf.freq2[filt_freq1]-434)*100,'.--',label="freq2")
ax[n].fill_between(dates[filt_freq1],(pdf.freq1[filt_freq1]-434)*100, (pdf.freq2[filt_freq1]-434)*100,alpha=0.2)
ax[n].legend(loc='upper left')
ax[n].set_xlim(xlim)
ax[n].xaxis.set_major_formatter(DateFormatter('%a %Hh'))
'''
'''
n+=1
filt_tempC = np.logical_and(np.logical_not(np.isnan(pdf.temperature_C)),pdf.temperature_C < 80)
ax[n].plot(dates[filt_tempC],pdf.temperature_C[filt_tempC],'.-',label="temp °C")
ax[n].legend()
ax[n].set_xlim(xlim)
ax[n].xaxis.set_major_formatter(DateFormatter('%a %Hh'))
'''
'''
n+=1

filt_truck = pdf.protocol==201
ax[n].hist(np.concatenate((pdf.freq-434,pdf.freq1-434,pdf.freq2-434)),50)
#ax[n].legend()
#ax[n].set_xlim(xlim)
#ax[n].xaxis.set_major_formatter(DateFormatter('%a %Hh'))
'''



tstamp = datetime.now().strftime('%Y%m%d_%H%M%S')
plt.savefig(f"/var/www/html/waterusage/chart{tstamp}.png")
os.rename(f'/var/www/html/waterusage/chart{tstamp}.png','/var/www/html/waterusage/waterusage.png')