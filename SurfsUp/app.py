# Import the dependencies.
import datetime as dt
import numpy as np
import pandas as pd

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################

# Create engine using the `hawaii.sqlite` database file
engine = create_engine("sqlite:///SurfsUp/Resources/hawaii.sqlite")

# Declare a Base using `automap_base()`
Base = automap_base()

# Use the Base class to reflect the database tables
Base.prepare(engine, reflect=True)

print(Base.metadata.tables.keys())

# Assign the measurement class to a variable called `Measurement` and
# the station class to a variable called `Station`
Station = Base.classes.station
Measurement = Base.classes.measurement

# Create a session
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    return (
        f"Available Routes:<br/>"
        f"<br/>Preciptitation from all stations:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"<br/>All station IDs:<br/>"
        f"/api/v1.0/stations<br/>"
        f"<br/>One year's worth of temperatures from the most active station:<br/>"
        f"/api/v1.0/tobs<br/>"
        f"<br/>Temperatures within date ranges:<br/>"
        f"Available date ranges: 2010-01-1 to 2017-08-23"
        f"<br/>Starting date only:<br/>"
        f"/api/v1.0/2010-01-1 <br/>"
        f"<br/>Start and end date:<br/>"
        f"/api/v1.0/2010-01-1/2017-08-23<br/>"
        f"<br/>Quick test date range:<br/>"
        f"/api/v1.0/2014-01-1/2015-01-1"
    )

# Return precipitation data
@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)

    # Collect data, all precipitation data added into respective dates
    results = session.query(Measurement.date, func.round(func.sum(Measurement.prcp),2)).group_by(Measurement.date).all()
    session.close()

    # Create dict for json
    precipitation_dict = {}

    for date, prcp_sum in results:
        precipitation_dict[date] = prcp_sum

    return jsonify(precipitation_dict)


# Return station ids
@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)

    # Simple query for station ids
    results = session.query(Station.station).all()

    # Create list
    station_ids = [row[0] for row in results]
    session.close()

    return jsonify(station_ids)

# Return one year of temp observations from the most active station
@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)

    # Get the date from one year before the most recent date
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).\
                        first()
    most_recent_date_str = most_recent_date[0]
    most_recent_date_obj = dt.datetime.strptime(most_recent_date_str, '%Y-%m-%d')
    one_year_ago_date = most_recent_date_obj - dt.timedelta(days=365)

    # Get the active stations and then find the most active station
    active_stations = session.query(Measurement.station, func.count(Measurement.station)).\
                    group_by(Measurement.station).\
                    order_by(func.count(Measurement.station).desc()).all()
    
    most_active_station = active_stations[0][0]
    
    # Get the full year of temperature measurements
    year_of_temps = session.query(Measurement.tobs).\
    filter(Measurement.date >= one_year_ago_date).\
    filter(Measurement.station == most_active_station).all()

    # Strip tuples for temps
    year_temps = [x[0] for x in year_of_temps]
    session.close()

    return jsonify(year_temps)

# Find temperature min, max and average after start date
@app.route("/api/v1.0/<start>")
def start_date(start):
    session = Session(engine)

    # Get the temps from the start date
    dates_temps = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.date >= start).\
        order_by(Measurement.date).all()
    
    # Get default last date in the .csv for display
    final_date = session.query(Measurement.date).\
                order_by(Measurement.date.desc()).first()

    # Statistics
    start_df = pd.DataFrame(dates_temps, columns=['dates', 'tobs'])
    start_min = start_df['tobs'].min()
    start_max = start_df['tobs'].max()
    start_mean = start_df['tobs'].mean()

    # Create dict for json
    start_dict = {
        "Start Date": start,
        "End Date (Default)": final_date[0],
        "Minimum Temp": start_min,
        "Maximum Temp": start_max,
        "Average Temp": start_mean
    }

    session.close()

    return jsonify(start_dict)

# Find temperature min, max and average in between start and end date
@app.route("/api/v1.0/<start>/<end>")
def date_range(start, end):
    session = Session(engine)

    # Get the temps from the start date to the end date
    dates_temps = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.date >= start).\
        filter(Measurement.date <= end).\
        order_by(Measurement.date).all()
    
    # Statistics
    start_end_df = pd.DataFrame(dates_temps, columns=['dates', 'tobs'])
    start_end_min = start_end_df['tobs'].min()
    start_end_max = start_end_df['tobs'].max()
    start_end_mean = start_end_df['tobs'].mean()

    # Create dict for json
    start_end_dict = {
        "Start Date": start,
        "End Date": end,
        "Minimum Temp": start_end_min,
        "Maximum Temp": start_end_max,
        "Average Temp": start_end_mean
    }

    session.close()

    return jsonify(start_end_dict)

if __name__ == "__main__":
    app.run(debug=True)