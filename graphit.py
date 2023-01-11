import io,sys
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import dateutil.parser
import datetime
from matplotlib.dates import DateFormatter, DayLocator
from matplotlib.ticker import Formatter
import datetime
from zoneinfo import ZoneInfo
from datetime import datetime
import matplotlib as mpl
from pandasql import sqldf

mpl.rcParams['timezone']='America/Chicago'

lld=[]
with open("data.json",'r') as f:
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




#timestamps = np.int64([ datetime.datetime.timestamp(dateutil.parser.parse(ts)) for ts in pdf.time ])
dates = np.array([ np.datetime64(ts) for ts in pdf.time ])
fig,(ax0,ax1,ax2) = plt.subplots(3)
fig.set_size_inches(8,8)
filt_freq=np.where(np.logical_not(np.isnan(pdf.freq)))[0]
ax0.plot(dates[filt_freq],(pdf.freq[filt_freq]-434)*100,'.--',label="freq")
#ax0.xaxis.set_major_locator(DayLocator())
ax0.xaxis.set_major_formatter(DateFormatter('%a %Hh'))
ax0.legend()
xlim=ax0.get_xlim()
# datetime.datetime.strftime( dateutil.parser.parse("2023-01-07 05:56:52"),"%a %H:%M")

filt_noise = np.logical_not( np.isnan(pdf.noise))
ax1.plot(dates[filt_noise],pdf.noise[filt_noise],'.-',label="noise")
ax1.plot(dates[filt_noise],pdf.rssi[filt_noise],'.-',label="signal")
ax1.legend()
ax1.set_xlim(xlim)
ax1.xaxis.set_major_formatter(DateFormatter('%a %Hh'))

filt_freq1 = np.logical_not(np.isnan(pdf.freq1))
ax2.plot(dates[filt_freq1],(pdf.freq1[filt_freq1]-434)*100,'.--',label="freq1")
ax2.plot(dates[filt_freq1],(pdf.freq2[filt_freq1]-434)*100,'.--',label="freq2")
ax2.fill_between(dates[filt_freq1],(pdf.freq1[filt_freq1]-434)*100, (pdf.freq2[filt_freq1]-434)*100,alpha=0.2)
ax2.legend()
ax2.set_xlim(xlim)
ax2.xaxis.set_major_formatter(DateFormatter('%a %Hh'))
plt.show()

