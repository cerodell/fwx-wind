import context
import numpy as np
import pandas as pd
from pathlib import Path
from functools import reduce

import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

from context import data_dir, img_dir
from utils.wind import get_sonic

import warnings

warnings.filterwarnings("ignore")

########## INPUTS ########
## file on interest
file_date = "220502"
ubc_winds = ["%.2d" % i for i in range(1, 6)]

###### END INPUTS ########


############## Sonic Data set up ####################

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

################################################################################


############## UBC Cup Anemometer Data set up ####################
wdir_correction = 160

for ubc_wind in ubc_winds:
    cup_in = sorted(
        Path(str(data_dir) + f"/wind{ubc_wind}/").glob(f"20{file_date}*.TXT")
    )

    direction = ["north", "east", "south", "west"]
    for i in range(len(cup_in)):
        filein = str(cup_in[i])
        cup_df = pd.read_csv(filein, sep="\t")
        cup_df[["wsp", "wdir"]] = cup_df[["wsp", "wdir"]].apply(pd.to_numeric)
        # freq = cup_df['time'].diff()

        cup_date_range = pd.date_range(
            "20" + file_date + "T" + filein[-12:-4], periods=len(cup_df), freq="3S"
        )
        cup_df = cup_df.set_index(pd.DatetimeIndex(cup_date_range))

        ## adjust wind direction from 160 offset in clock wise direction from true north
        cup_df["wdir"] = cup_df["wdir"] - wdir_correction
        cup_df["wdir"][cup_df["wdir"] < 0] = cup_df["wdir"] + 360

        # ################################################################################

        ##################### Clean and solve for Wsp and Wdir for Sonic ##########################
        ## convert u and v to wind speed and direction
        sonic_df["U"][(sonic_df["U"] > 10) | (sonic_df["U"] < -10)] = sonic_df[
            "U"
        ].mean()
        sonic_df["V"][(sonic_df["V"] > 10) | (sonic_df["V"] < -10)] = sonic_df[
            "V"
        ].mean()
        # wsp = np.sqrt((sonic_df["U"] ** 2) + (sonic_df["V"] ** 2))
        wsp = ((sonic_df["U"] ** 2) + (sonic_df["V"] ** 2)) ** 0.5

        sonic_df["wsp"] = wsp
        wdir = (180 / np.pi) * np.arctan2(sonic_df["V"], -sonic_df["U"])
        wdir[wdir <= 0] = wdir + 360
        sonic_df["wdir"] = wdir

        ## index to match cup
        # sonic_df = sonic_df.resample('3S').mean()
        sonic_dfi = sonic_df[str(cup_df.index[0]) : str(cup_df.index[-1])]
        # ################################################################################

        sonic_dfi = sonic_dfi.resample("30S").mean()
        cup_df = cup_df.resample("30S").mean()

        ###################### plot comparsion ##############################

        colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]

        fig = plt.figure(figsize=(10, 4))  # (Width, height) in inches.
        fig.suptitle(f"Wind{ubc_wind} with direction {direction[i]}")
        ax = fig.add_subplot(2, 1, 1)
        ax.plot(sonic_dfi.index, sonic_dfi["wsp"], color=colors[0])
        ax.plot(cup_df.index, cup_df["wsp"], color=colors[1])
        # ax.set_ylabel("Wind Speed \n"  + r"$\frac{m}{s^{-1}}$", fontsize=12)
        ax.set_ylabel("Wind Speed \n (m s^-1)", fontsize=12)
        ax.set_xticklabels([])

        ax = fig.add_subplot(2, 1, 2)
        ax.plot(sonic_dfi.index, sonic_dfi["wdir"], color=colors[0], label="sonic")
        ax.plot(cup_df.index, cup_df["wdir"], color=colors[1], label="cup")
        ax.set_ylabel("Wind Direction \n (Degs)", fontsize=12)
        ax.set_xlabel("DateTime (HH:MM:SS)", fontsize=12)
        myFmt = DateFormatter("%H:%M:%S")
        ax.xaxis.set_major_formatter(myFmt)
        # ax.yaxis.set_ticks(np.arange(0, 360 + 90, 90))

        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.48, 2.4),
            ncol=6,
            fancybox=True,
            shadow=True,
        )

        plt.savefig(
            str(img_dir) + f"/wind{ubc_wind}-{direction[i]}.png",
            dpi=300,
            bbox_inches="tight",
        )
