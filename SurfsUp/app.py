# import the dependencies.
import numpy as np
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify


#################################################
# database setup
#################################################
engine = create_engine("sqlite:///../Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# flask setup
#################################################
app = Flask(__name__)

#################################################
# flask routes
#################################################


# one year from last date function
def oneyearfromlastdate():

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # one year from last calculation for further use
    one_year_from_last_date = dt.date(2017,8,23) - dt.timedelta(days=365)

    # close session
    session.close()

    return one_year_from_last_date


# home page route
@app.route("/")
def homepage():
    """List all available api routes."""
    return( 
        f"Welcome to Climate App<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt;</br>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;</br>"
    )

# precipitation API route
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # get last 12 months precipitation data
    precipitation_scores = session.query(Measurement.date,Measurement.prcp).filter(Measurement.date >= oneyearfromlastdate()).all()

    # close session
    session.close()

    # creating dictionary for results
    precipitation_scores_dictionary = {}
    for r in precipitation_scores:
        if type(r[1]) == float:            
            precipitation_scores_dictionary[r[0]]=r[1]
    
    # return jsonified dictionary
    return jsonify(precipitation_scores_dictionary)


# stations API route
@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # get list of stations from the dataset and save query to stations variable
    stations = session.query(Station).all()

    # close session
    session.close()

    # creating dictionary for results
    stations_dictionary = {}
    for r in stations:
        stations_dictionary[r.station] = {"name":r.name,
                                "latitude":r.latitude,
                                "longitude":r.longitude,
                                "elevation":r.elevation
                               }
    # return jsonified dictionary
    return jsonify(stations_dictionary)

@app.route('/api/v1.0/tobs')
def tobs():
    # create our session (link) from Python to the DB
    session = Session(engine)
    
    # query the dates and temperature observations of the most-active station for the previous year of data.
    most_active_station = session.query(Measurement).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).first().station
    
    # use results of previous code ("most_active_station") to filter stations and one_year_from_last_date() function to filter dates
    tobs = session.query(Measurement.date, Measurement.tobs).filter(Measurement.station == most_active_station).filter(Measurement.date >= oneyearfromlastdate()).all()
    
    # close session
    session.close()
    
    # create dictionary to save results
    tobs_dictionary = {}
    for r in tobs:
        tobs_dictionary[r[0]]=r[1]
    
    #Return jsonified dictionary
    return jsonify(tobs_dictionary)  


@app.route("/api/v1.0/<start>",defaults={"end":None})       
@app.route("/api/v1.0/<start>/<end>")                       
def start_end_dates(start,end):

    # create our session (link) from Python to the DB
    session = Session(engine)

    # create selector for further query
    sel=[func.min(Measurement.tobs),
         func.avg(Measurement.tobs),
         func.max(Measurement.tobs),
         func.min(Measurement.date),
         func.max(Measurement.date)]

    # option 1: query without end parameter
    if end == None:
        (TMIN, TAVG, TMAX, DMIN, DMAX) = session.query(*sel).filter(Measurement.date >= start).one()

    # option 2: query with end parameter
    else:
        (TMIN, TAVG, TMAX, DMIN, DMAX) = session.query(*sel).filter(Measurement.date >= start).filter(Measurement.date <= end).one()
    
    # close session
    session.close()

    # create dictionary to save results
    temp_dictionary = {"from date":DMIN,
               "to date":DMAX,
               "min temperature":TMIN,
               "max temperature":TMAX,
               "avg temperature":TAVG}
    # return jsonified dictionary
    return jsonify(temp_dictionary)


# run climate app
if __name__ == '__main__':
    app.run(debug=True)