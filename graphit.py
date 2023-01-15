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

mpl.rcParams['lines.linewidth']=0.3
mpl.rcParams['lines.markersize']=1


#timestamps = np.int64([ datetime.datetime.timestamp(dateutil.parser.parse(ts)) for ts in pdf.time ])
dates = np.array([ np.datetime64(ts) for ts in pdf.time ])
fig,ax = plt.subplots(5)
fig.tight_layout()
fig.set_size_inches(8,12)
fig.set_dpi(100)
n=0
filt_freq=np.where(np.logical_not(np.isnan(pdf.freq)))[0]
ax[n].plot(dates[filt_freq],(pdf.freq[filt_freq]-434)*100,'.--',label="freq")
#ax0.xaxis.set_major_locator(DayLocator())
ax[n].xaxis.set_major_formatter(DateFormatter('%a %Hh'))
ax[n].legend()
xlim=ax[n].get_xlim()
# datetime.datetime.strftime( dateutil.parser.parse("2023-01-07 05:56:52"),"%a %H:%M")
n+=1
filt_noise = np.logical_not( np.isnan(pdf.noise))
ax[n].plot(dates[filt_noise],pdf.noise[filt_noise],'.-',label="noise")
ax[n].plot(dates[filt_noise],pdf.rssi[filt_noise],'.-',label="signal")
ax[n].plot(dates[filt_noise],pdf.rssi[filt_noise]-pdf.noise[filt_noise],'.-',label="SNR")
ax[n].legend()
ax[n].set_xlim(xlim)
ax[n].xaxis.set_major_formatter(DateFormatter('%a %Hh'))

n+=1
filt_freq1 = np.logical_not(np.isnan(pdf.freq1))
ax[n].plot(dates[filt_freq1],(pdf.freq1[filt_freq1]-434)*100,'.--',label="freq1")
ax[n].plot(dates[filt_freq1],(pdf.freq2[filt_freq1]-434)*100,'.--',label="freq2")
ax[n].fill_between(dates[filt_freq1],(pdf.freq1[filt_freq1]-434)*100, (pdf.freq2[filt_freq1]-434)*100,alpha=0.2)
ax[n].legend()
ax[n].set_xlim(xlim)
ax[n].xaxis.set_major_formatter(DateFormatter('%a %Hh'))
n+=1
filt_tempC = np.logical_not(np.isnan(pdf.temperature_C))
ax[n].plot(dates[filt_tempC],pdf.temperature_C[filt_tempC],'.-',label="temp °C")
ax[n].legend()
ax[n].set_xlim(xlim)
ax[n].xaxis.set_major_formatter(DateFormatter('%a %Hh'))

n+=1

filt_truck = pdf.protocol==201
ax[n].hist(pdf.rssi,10)
#ax[n].legend()
#ax[n].set_xlim(xlim)
#ax[n].xaxis.set_major_formatter(DateFormatter('%a %Hh'))


plt.savefig("chart.png")
os.system("eom chart.png")

