import context
import numpy as np
import pandas as pd
from pathlib import Path
from functools import reduce

import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

from context import data_dir, img_dir

import warnings

warnings.filterwarnings("ignore")

########## INPUTS ########
## file on interest
file_date = "220502"
ubc_winds = ["%.2d" % i for i in range(1, 6)]

###### END INPUTS ########


############## Sonic Data set up ####################
## open and set headers for sonic dataframe
header = ["ID", "U", "V", "W", "units", "sos", "internal temp", "ind1", "ind2"]

sonic_in = sorted(Path(str(data_dir) + "/sonic/").glob(f"{file_date}*.GILL01"))


def gettime(time_of_int):
    """
    input
        str in decimal hours
    returns
        HH:mm:ss.SSS string for time on int
    """
    hour = int(time_of_int)
    minute = (time_of_int * 60) % 60
    seconds = (time_of_int * 3600) % 60
    decisecond = (time_of_int * 36000) % 60
    datetime_of_int = "%d:%02d:%02d.%d" % (hour, minute, seconds, decisecond)
    return datetime_of_int


def get_sonic(filein):

    sonic_df = pd.read_csv(filein, names=header)
    file_date = filein[-15:-7]
    ## parse datetime from timestampe in file name
    decimal_end_hour = float(int(file_date[-2:]) / 4)
    decimal_end_deciseconds = decimal_end_hour * 60 * 60 / 0.1  # decimal end hour
    decimal_start_hour = (
        (decimal_end_deciseconds - len(sonic_df)) / 60 / 60 * 0.1
    )  # decimal start hour

    end_hour = gettime(decimal_end_hour)
    start_hour = gettime(decimal_start_hour)
    # print(f"start time {start_hour}")
    # print(f"end time {end_hour}")

    ## define stat and end date time for pandas
    start_datetime = (
        f"20{file_date[:2]}-{file_date[2:4]}-{file_date[4:6]}-T{start_hour}"
    )
    end_datetime = f"20{file_date[:2]}-{file_date[2:4]}-{file_date[4:6]}-T{end_hour}"

    ## create dataetime array and set as dataframe index
    sonic_date_range = pd.date_range(
        start_datetime, end_datetime, periods=len(sonic_df)
    )
    sonic_df = sonic_df.set_index(pd.DatetimeIndex(sonic_date_range))
    sonic_df = sonic_df.dropna()
    del sonic_df["ID"]
    del sonic_df["units"]
    del sonic_df["ind1"]
    del sonic_df["ind2"]
    sonic_df["U"] = sonic_df["U"].replace("+", "")
    sonic_df["V"] = sonic_df["V"].replace("+", "")
    sonic_df["W"] = sonic_df["W"].replace("+", "")
    sonic_df = sonic_df.apply(pd.to_numeric)  # convert all columns of DataFrame
    sonic_df = sonic_df.reset_index()
    return sonic_df


sonic_list = []
for filein in sonic_in:
    # print(str(filein))
    df = get_sonic(str(filein))
    sonic_list.append(df)


sonic_df = reduce(lambda df1, df2: pd.merge(df1, df2, how="outer"), sonic_list)
sonic_df = sonic_df.set_index(pd.DatetimeIndex(sonic_df["index"]))
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
