import streamlit as st
from datetime import datetime as dt
import pytz
import pandas as pd
from data import get_data


# We want to stream a editable dataframe that allows the user to input weights for spans of time
# representing parts of the season.

# The user will be able to input the number of time weights they want to use, and then
# they will be able to input the weight for each time weight.


def input_time_weights():
    data = get_data()
    min_date = data["date"].min()
    max_date = data["date"].max()

    number_of_weights = st.number_input(
        "Num of time weights", value=2, min_value=2, max_value=10)

    timespan = (max_date - min_date).days / int(number_of_weights)

    df = pd.DataFrame(columns=["period", "start_date", "end_date", "weight"])
    for i in range(int(number_of_weights)):

        start_date = min_date + pd.Timedelta(days=i*timespan)
        end_date = min_date + pd.Timedelta(days=(i+1)*timespan)

        # Don't let end date be the same as next start date
        if i < int(number_of_weights) - 1:
            end_date -= pd.Timedelta(days=1)

        st.write(end_date - start_date)

        df.loc[i] = [i, start_date, end_date, 1.0]
        st.write(type(df.loc[i, "weight"]))

    # Format date columns as "Mon, Mar 3"
    df["start_date"] = df["start_date"].dt.strftime("%a, %b %-d")
    df["end_date"] = df["end_date"].dt.strftime("%a, %b %-d")

    st.experimental_data_editor(df)
