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
ubc_winds = ["%.2d" % i for i in range(1, 5)]

###### END INPUTS ########


############## UBC Cup Anemometer Data set up ####################
# wdir_correction = 160

fig = plt.figure(figsize=(10, 4))  # (Width, height) in inches.
colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
direction = ["north", "east", "south", "west"]
fig.suptitle(f"Compare all cup anemometers {direction[1]}")
wsp_ax = fig.add_subplot(2, 1, 1)
wdir_ax = fig.add_subplot(2, 1, 2)

for i in range(len(ubc_winds)):
    cup_in = sorted(
        Path(str(data_dir) + f"/wind{ubc_winds[i]}/").glob(f"20{file_date}*.TXT")
    )

    filein = str(cup_in[1])
    cup_df = pd.read_csv(filein, sep="\t")
    cup_df[["wsp", "wdir"]] = cup_df[["wsp", "wdir"]].apply(pd.to_numeric)
    cup_date_range = pd.date_range(
        "20" + file_date + "T" + filein[-12:-4], periods=len(cup_df), freq="3S"
    )
    cup_df = cup_df.set_index(pd.DatetimeIndex(cup_date_range))
    cup_df = cup_df.resample("10S").mean()
    cup_df = cup_df.reset_index()

    ###################### plot comparsion ##############################

    wsp_ax.plot(cup_df.index, cup_df["wsp"], color=colors[i])
    wdir_ax.plot(
        cup_df.index, cup_df["wdir"], color=colors[i], label=f"wind{ubc_winds[i]}"
    )

    # ax.yaxis.set_ticks(np.arange(0, 360 + 90, 90))
    wdir_ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.48, 2.4),
        ncol=6,
        fancybox=True,
        shadow=True,
    )

wsp_ax.set_ylabel("Wind Speed \n (m s^-1)", fontsize=12)
wsp_ax.set_xticklabels([])
wdir_ax.set_ylabel("Wind Direction \n (Degs)", fontsize=12)
wdir_ax.set_xlabel("Time (SS)", fontsize=12)
# myFmt = DateFormatter("%H:%M:%S")
# wdir_ax.xaxis.set_major_formatter(myFmt)
plt.savefig(str(img_dir) + f"/windALL-{direction[1]}.png", dpi=300, bbox_inches="tight")
