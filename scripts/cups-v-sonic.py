import context
import numpy as np
import pandas as pd
from pathlib import Path
from functools import reduce
from pylab import *

import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

from context import data_dir, img_dir
from utils.wind import get_sonic

import warnings

warnings.filterwarnings("ignore")

########## INPUTS ########
## file on interest
file_date = "220504"  # '220504' '220505'
# ubc_winds =   ["%.2d" % i for i in range(16, 21)]
ubc_winds = ["%.2d" % i for i in range(1, 16)]
test_dir = 1  # zero or one options
direction = "ESE"  # 'NNW' 'ESE' 'SSW'
slice_fd = [10, -1]
###### END INPUTS ########


########################### Sonic Data set up #################################

## set path to sonic data and sort all files for date of interest
sonic_in = sorted(Path(str(data_dir) + "/sonic/").glob(f"{file_date}*.GILL01"))

## open reach file as a dataframe and sort in list
sonic_list = [get_sonic(str(filein)) for filein in sonic_in]

## merge the list of dataframes based on time
sonic_df = reduce(lambda df1, df2: pd.merge(df1, df2, how="outer"), sonic_list)

## index dataframe on datetime
sonic_df = sonic_df.set_index(pd.DatetimeIndex(sonic_df["index"]))

## delte old index
del sonic_df["index"]

#################################################################################


# ####################### UBC Cup Anemometer Data set up ###########################

fig = plt.figure(figsize=(10, 4))  # (Width, height) in inches.
cmap = cm.get_cmap("tab20", 16)
colors = []
for i in range(cmap.N):
    rgba = cmap(i)
    # print(matplotlib.colors.rgb2hex(rgba))
    colors.append(matplotlib.colors.rgb2hex(rgba))


fig.suptitle(f"Compare all cup anemometers {direction}", y=1.1)
wsp_ax = fig.add_subplot(2, 1, 1)
wdir_ax = fig.add_subplot(2, 1, 2)

for i in range(len(ubc_winds)):
    test_dir_i = test_dir
    if (direction == "NNW") and (ubc_winds[i] == "01") or (ubc_winds[i] == "03"):
        pass
    elif (direction == "ESE") and (ubc_winds[i] == "01") or (ubc_winds[i] == "03"):
        test_dir_i = 0
    elif (direction == "ESE") and (ubc_winds[i] == "06") or (ubc_winds[i] == "12"):
        pass
    else:
        cup_in = sorted(
            Path(str(data_dir) + f"/wind{ubc_winds[i]}/").glob(f"20{file_date}*.TXT")
        )

        filein = str(cup_in[test_dir_i])
        print(filein)
        cup_df = pd.read_csv(filein, sep="\t")
        cup_df[["wsp", "wdir"]] = cup_df[["wsp", "wdir"]].apply(pd.to_numeric)
        cup_date_range = pd.date_range(
            "20" + file_date + "T" + filein[-12:-4], periods=len(cup_df), freq="3S"
        )
        cup_df = cup_df.set_index(pd.DatetimeIndex(cup_date_range))
        cup_df = cup_df.resample("10S").mean()
        cup_df = cup_df.iloc[slice_fd[0] : slice_fd[1]]

        ## index to match cup
        sonic_dfi = sonic_df[str(cup_df.index[0]) : str(cup_df.index[-1])]
        sonic_dfi = sonic_dfi.resample("10S").mean()
        cup_df = cup_df.resample("10S").mean()

        cup_df = cup_df.reset_index()
        sonic_dfi = sonic_dfi.reset_index()

        ###################### plot comparsion ##############################

        wsp_ax.plot(cup_df.index, cup_df["wsp"] * 0.44704, color=colors[i])
        wsp_ax.plot(sonic_dfi.index, sonic_dfi["wsp"], color=colors[i], linestyle="--")

        wdir_ax.plot(
            cup_df.index, cup_df["wdir"], color=colors[i], label=f"wind{ubc_winds[i]}"
        )

        wdir_ax.plot(
            sonic_dfi.index,
            sonic_dfi["wdir"],
            linestyle="--",
            color=colors[i],
            label=f"sonic{ubc_winds[i]}",
        )

        # ax.yaxis.set_ticks(np.arange(0, 360 + 90, 90))
        wdir_ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.48, 2.68),
            ncol=8,
            fancybox=True,
            shadow=True,
            fontsize=9,
        )

    wsp_ax.set_ylabel("Wind Speed \n (m s^-1)", fontsize=12)
    wsp_ax.set_xticklabels([])
    wdir_ax.set_ylabel("Wind Direction \n (Degs)", fontsize=12)
    wdir_ax.set_xlabel("Time (SS)", fontsize=12)
    # myFmt = DateFormatter("%H:%M:%S")
    # wdir_ax.xaxis.set_major_formatter(myFmt)

plt.savefig(
    str(img_dir) + f"/wind-v-sonic-{direction}-{file_date}.png",
    dpi=300,
    bbox_inches="tight",
)
