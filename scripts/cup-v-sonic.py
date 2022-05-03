from turtle import color
import context
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

from context import data_dir, img_dir


########## INPUTS ########
## file on interest
file_date = "22042960"

## phot time stamp for ubc sensor
wind01 = "2022-05-02-T13:19:23"


###### END INPUTS ########


############## Sonic Data set up ####################
## open and set headers for sonic dataframe
header = ["ID", "U", "V", "W", "units", "sos", "internal temp", "ind1", "ind2"]
sonic_df = pd.read_csv(str(data_dir) + f"/{file_date}.GILL01", names=header)

## parse datetime from timestampe in file name
decimal_end_hour = int(int(file_date[-2:]) / 4)
decimal_end_deciseconds = (
    int(int(file_date[-2:]) / 4) * 60 * 60 / 0.1
)  # decimal end hour
decimal_start_hour = (
    (decimal_end_deciseconds - len(sonic_df)) / 60 / 60 * 0.1
)  # decimal start hour


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


end_hour = gettime(decimal_end_hour)
start_hour = gettime(decimal_start_hour)
print(f"start time {start_hour}")
print(f"end time {end_hour}")


## define stat and end date time for pandas
start_datetime = f"20{file_date[:2]}-{file_date[2:4]}-{file_date[4:6]}-T{start_hour}"
end_datetime = f"20{file_date[:2]}-{file_date[2:4]}-{file_date[4:6]}-T{end_hour}"

## create dataetime array and set as dataframe index
sonic_date_range = pd.date_range(start_datetime, end_datetime, periods=len(sonic_df))
sonic_df = sonic_df.set_index(pd.DatetimeIndex(sonic_date_range))
################################################################################


############## UBC Cup Anemometer Data set up ####################
# cup_df = pd.read_csv(str(data_dir) + f"/wind01/{file_date[:-2]}.TXT", names = header)

cup_df = pd.read_csv(str(data_dir) + f"/wind01/{220502}.TXT", sep="\t")
cup_df[["wsp", "wdir"]] = cup_df[["wsp", "wdir"]].apply(pd.to_numeric)
# freq = cup_df['time'].diff()
cup_date_range = pd.date_range(wind01, periods=len(cup_df), freq="3S")
cup_df = cup_df.set_index(pd.DatetimeIndex(cup_date_range))

################################################################################


## conver u and v to wind speed and direction
sonic_df["U"][sonic_df["U"] > 40] = sonic_df["U"].mean()
sonic_df["V"][sonic_df["V"] > 40] = sonic_df["V"].mean()
wsp = np.sqrt(sonic_df["U"] ** 2 + sonic_df["V"] ** 2)
wdir = (180 / np.pi) * np.arctan2(-sonic_df["U"], -sonic_df["V"])
wdir[wdir <= 0] = wdir + 360


## plot comparsion
colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
fig = plt.figure(figsize=(10, 4))  # (Width, height) in inches.
ax = fig.add_subplot(2, 1, 1)
# ax.plot(sonic_df.index, wsp, color=colors[0])
ax.plot(cup_df.index, cup_df["wsp"], color=colors[1])
# ax.set_ylabel("Wind Speed \n"  + r"$\frac{m}{s^{-1}}$", fontsize=12)
ax.set_ylabel("Wind Speed \n (m s^-1)", fontsize=12)
ax.set_xticklabels([])


ax = fig.add_subplot(2, 1, 2)
# ax.plot(sonic_df.index, wdir, color=colors[0], label="sonic")
ax.plot(cup_df.index, cup_df["wdir"], color=colors[1], label="cup")
ax.set_ylabel("Wind Direction \n (Degs)", fontsize=12)
ax.set_xlabel("DateTime (HH:MM:SS)", fontsize=12)
myFmt = DateFormatter("%H:%M:%S")
ax.xaxis.set_major_formatter(myFmt)
ax.yaxis.set_ticks(np.arange(0, 360 + 90, 90))

ax.legend(
    loc="upper center",
    bbox_to_anchor=(0.45, 2.5),
    ncol=6,
    fancybox=True,
    shadow=True,
)

plt.savefig(str(img_dir) + f"/test.png", dpi=300, bbox_inches="tight")
