#!/usr/bin/env python3
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
mpl.rcParams['timezone']='America/Chicago'

lld=[]
for fn in glob('data*.json'):
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

# filter only records that have valid 'id' field (not Nan)
#ids=pdf.id
goodid=np.logical_and(np.logical_not(pd.isna(pdf.id)), np.logical_not(pd.isna(pdf.Consumption)))
pdf = pdf[goodid]
pdf['newid'] = [str(x) for x in pdf.id]

# idenitfy the ID with the most data, that'd be us.
ids = sqldf("select newid,count(*) N,avg(rssi) avg_rssi from pdf group by newid order by avg_rssi")
pdf=pdf[pdf.newid == list(ids.newid)[-1]]

mpl.rcParams['lines.linewidth']=0.3
mpl.rcParams['lines.markersize']=1


#timestamps = np.int64([ datetime.datetime.timestamp(dateutil.parser.parse(ts)) for ts in pdf.time ])
dates = np.array([ np.datetime64(ts) for ts in pdf.time ])
datenums = np.uint64(dates)
regdates = np.arange(datenums.min(),datenums.max(), 30*60)
regy = np.interp(regdates, datenums, pdf.Consumption)

regdatedates = np.datetime64(regdates)




fig,ax = plt.subplots(2,figsize=(14,8))
fig.tight_layout()
fig.set_size_inches(8,12)
fig.set_dpi(100)
cons=np.diff(pdf.Consumption) 
#dates=dates[1:]
n=0

ax[n].plot(regdatedates[:-1],regy,'.-',label="Consumption rate")
ax[n].legend()
#ax[n].set_xlim(xlim)
ax[n].xaxis.set_major_formatter(DateFormatter('%a %Hh'))

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
plt.savefig(f"chart{tstamp}.png")
print(f"eom chart{tstamp}.png")

