import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
# scoped_session Ref: https://docs.sqlalchemy.org/en/latest/orm/contextual.html
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from sqlalchemy import create_engine, func
from datetime import datetime as dt
from datetime import timedelta

from flask import Flask, jsonify
#############################################################
# Error Handler Code (Ref:flask.pocoo.org/docs/0.12/patterns)
#############################################################
from flask import jsonify

class UserDefinedError(Exception):
    status_code = 415

    def __init__(self, message, status_code=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        
    def to_dict(self):
        rv = dict(self)
        rv['message'] = self.message
        return rv

# Data base setup
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect the database in to a new model
Base = automap_base()

# Reflect the tables
Base.prepare(engine, reflect=True)

# We can view all of the classes that automap found
Base.classes.keys()

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

#Create our session (link) from Python to Database
#session = Session(engine)
session_factory = scoped_session(sessionmaker(bind=engine))
Session = scoped_session(session_factory)

# Flask Setup
app = Flask(__name__)

# Flask Routes

@app.route("/", methods=['GET'])
def Home():
    """List all available api routes"""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
		f"/api/v1.0/stations<br/>"
		f"/api/v1.0/tobs<br/>"
		f"/api/v1.0/<start_date><br/>"
		f"/api/v1.0/<start_date>/<end_date><br/>"
	)

#* Convert the query results to a Dictionary using `date` as the key and `prcp` as the value.
#* Return the JSON representation of your dictionary.
@app.route("/api/v1.0/precipitation", methods=['GET'])
def precipitation():
    """Return a list of precipitations for all dates"""
    session = Session()
    # Query Measurement table for precipation data
    prcp_results = session.query(Measurement.date, Measurement.prcp).order_by(Measurement.date).all()

    # Convert list of tuples into normal list
    prcp_for_all_dates = []

    # Create a dictionary from the row data and append to a list of
    # precipitations for all dates"
    for row in prcp_results:
        prcp_dict = {}
        prcp_dict["date"] = row.date
        prcp_dict["prcp"] = row.prcp
        prcp_for_all_dates.append(prcp_dict)
    return jsonify(prcp_for_all_dates)

#* Return a JSON list of stations from the dataset.
@app.route("/api/v1.0/stations", methods=['GET'])
def stations():
    session = Session()
	# Query all stations
    station_results = session.query(Station.station).order_by(Station.station).all()

    # Convert list of tuples into normal list
    all_stations = list(np.ravel(station_results))

    return jsonify(all_stations)
	
#* query for the dates and temperature observations for a year from the last data point.
#* Return a JSON list of Temperature Observations (tobs) for the previous year.
@app.route("/api/v1.0/tobs", methods=['GET'])
def tobs():
    session = Session()
    """Query for temperature observations from a year from the last data point"""
    max_date = session.query(func.max(Measurement.date)).first()
    end_date = dt.strptime(max_date[0], r'%Y-%m-%d')
    start_date = end_date - timedelta(days=366)
    """Perform a query to retrieve the data and temperature observations"""
    tobs_results = session.query(Measurement.date, Measurement.tobs).\
                    filter(Measurement.date >= start_date).\
                    filter(Measurement.date <= end_date).\
                    order_by(Measurement.date).all()
    """Convert list of tuples into normal list"""
    tobs_data = list(np.ravel(tobs_results))

    return jsonify(tobs_data)
#* Return a JSON list of the minimum temperature, the average temperature, and the maximum temperature between a given date range
@app.route("/api/v1.0/<start_date>", methods=['GET'])
def calc_temps_from(start_date):
    session = Session()
    """Calculate temperature observations from a given date.

    Args:
        date (str): A date string in the format '%Y-%m-%d'

    Returns:
        A jsonified dictionary containing the temperature min, avg and max
    """
    sel = [func.min(Measurement.tobs).label('tmin'), func.avg(Measurement.tobs).label('tavg'), func.max(Measurement.tobs).label('tmax')]
    calc_temps_from_results = session.query(*sel).filter(Measurement.date >= start_date).all()
    # Convert list of tuples into normal list
    calc_temps_from_data = []
	
    # Convert the query results to a Dictionary using `date` as the key
    # and `tobs` as the value.
    for row in calc_temps_from_results:
        calc_temps_from_dict = {}
        calc_temps_from_dict['tmin'] = row.tmin
        calc_temps_from_dict['tavg'] = row.tavg
        calc_temps_from_dict['tmax'] = row.tmax
        calc_temps_from_data.append(calc_temps_from_dict)
        
    try:
        return jsonify(calc_temps_from_data)
    except:
        raise UserDefinedError('No records found for the given date\(s\)', status_code=415)
# * Same requirements as 'api/v1.0/<start_date>'
# * Return a JSON list of the minimum temperature, the average temperature, and the max.temperature between two dates
@app.route("/api/v1.0/<start_date>/<end_date>", methods=['GET'])
def calc_temps(start_date, end_date):
    session = Session()
    """TMIN, TAVG, and TMAX for a list of dates.
    
    Args:
        start_date (string): A date string in the format %Y-%m-%d
        end_date (string): A date string in the format %Y-%m-%d
        
    Returns:
        TMIN, TAVG, and TMAX
    """
    sel = [func.min(Measurement.tobs).label('tmin'), func.avg(Measurement.tobs).label('tavg'), func.max(Measurement.tobs).label('tmax')]
    calc_temps_results = session.query(*sel).filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()
    # Convert list of tuples into normal list
    calc_temps_data = []
    """Convert the query results to a Dictionary using `date` as the key"""
    """ and `tobs` as the value."""
    for row in calc_temps_results:
        calc_temps_dict = {}
        calc_temps_dict['tmin'] = row.tmin
        calc_temps_dict['tavg'] = row.tavg
        calc_temps_dict['tmax'] = row.tmax
        calc_temps_data.append(calc_temps_dict)
    try:
        return jsonify(calc_temps_data)
    except:
        raise UserDefinedError('No records found for the given date\(s\)', status_code=415)
# Register a error handler to handle user defined errors (other than HTTP 404)
@app.errorhandler(UserDefinedError)
def handle_user_defined(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

if __name__ == '__main__':
    app.run(debug=True)
