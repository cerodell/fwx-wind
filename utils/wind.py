import context
import pandas as pd


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

    ## open and set headers for sonic dataframe
    header = ["ID", "U", "V", "W", "units", "sos", "internal temp", "ind1", "ind2"]
    # print(filein)
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
