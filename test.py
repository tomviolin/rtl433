
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from glob import glob
import os,sys

for f in sorted(glob("data*.json")):
    df = pd.read_json(f, lines=True)
    plt.plot(df['freq'],df['rssi'],'.')
    plt.savefig(os.path.basename(f).split('.')[0]+'.png')

