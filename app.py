#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='venues', lazy=False, cascade='all, delete-orphan')
    genres = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    shows = db.relationship('Show', backref='artists', lazy=False, cascade='all, delete-orphan')


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


db.create_all()
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html', artists = artists, venues = venues)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    data=[]
    venue_data = Venue.query.distinct(Venue.city, Venue.state).all()

    for location in venue_data:
        venues = Venue.query.filter_by(city=location.city, state=location.state).all()

    for venue in venues:
        data.append({
            "city": location.city,
            "state": location.state,
            "venues": [{
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": Show.query.filter_by(venue_id=venue.id).count()
                    }]
                })

    return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
    venue_search_result = Venue.query.filter(Venue.name.
        ilike('%' + request.form.get('search_term') + '%')).all()

    response = {
        "count": len(venue_search_result),
        "data": venue_search_result
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue = Venue.query.filter(Venue.id == venue_id).first()
    data = venue.__dict__

    shows = Show.query.join(Artist, Venue).filter_by(id = venue_id)
    past_shows = shows.filter(Show.start_time < datetime.now()).all()
    upcoming_shows = shows.filter(Show.start_time >= datetime.now()).all()
    past_shows_count = len(past_shows)
    upcoming_shows_count = len(upcoming_shows)

    for show in upcoming_shows:
        show.start_time = show.start_time.strftime('%d-%m-%Y %H:%M')

    for show in past_shows:
        print(show.artists)
        print(show.venues)
        show.start_time = show.start_time.strftime('%d-%m-%Y %H:%M')

        data["past_shows"] = past_shows
        data["past_shows_count"] = past_shows_count
        data["upcoming_shows"] = upcoming_shows
        data["upcoming_shows_count"] = upcoming_shows_count
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm(request.form)

    try:
        venue = Venue()
        form.populate_obj(venue)
        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        flash('An error occurred. Venue ' +
            request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    error = False
    venue = Venue.query.get(venue_id)

    if venue is None:
        return abort(400)

    try:
        db.session.delete(venue)
        db.session.commit()
        flash('Venue deleted successfully!')
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
        flash('Error occurred: Venue could not be deleted.')
    finally:
        db.session.close()

    if (error):
        abort(500)
    else:
        return jsonify({
            'message': 'Delete Successful'
        })



#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artists = db.session.query(Artist.id, Artist.name).all()
    return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    artist_search_result = Artist.query.filter(
        Artist.name.ilike('%' + request.form.get('search_term') + '%')).all()

    response = {
        "count": len(artist_search_result),
        "data": artist_search_result
    }

    return render_template(
        'pages/search_artists.html', results=response, search_term=request.form.get(
            'search_term', ''))
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    artist = db.session.query(Artist).filter(Artist.id == artist_id).first()
    data = artist.__dict__

    shows = Show.query.join(
        Venue, Artist).filter_by(id = artist_id)
    past_shows = shows.filter(Show.start_time < datetime.now()).all()
    upcoming_shows = shows.filter(Show.start_time >= datetime.now()).all()
    past_shows_count = len(past_shows)
    upcoming_shows_count = len(upcoming_shows)

    for show in upcoming_shows:
        show.start_time = show.start_time.strftime('%d-%m-%Y %H:%M')

    for show in past_shows:
        show.start_time = show.start_time.strftime('%d-%m-%Y %H:%M')

    data["past_shows"] = past_shows
    data["past_shows_count"] = past_shows_count
    data["upcoming_shows"] = upcoming_shows
    data["upcoming_shows_count"] = upcoming_shows_count

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.filter_by(id=artist_id).first()
    form = ArtistForm(obj=artist)
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm(request.form)
    artist = Artist.query.filter_by(id=artist_id).first()

    try:
        form.populate_obj(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        flash('An error occurred. artist ' +
                request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.filter_by(id=venue_id).first()
    form = VenueForm(obj=venue)
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form)
    venue = Venue.query.filter_by(id=venue_id).first()

    try:
        form.populate_obj(venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        flash('An error occurred. Venue ' +
                request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    try:
        form = ArtistForm(request.form)
        artists = Artist()
        form.populate_obj(artists)
        db.session.add(artists)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        flash('Failed to create artist ' + request.form['name'])
    finally:
        db.session.close()

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    data = []
    shows = Show.query.join(Artist).join(Venue).all()

    for show in shows:
        data.append({
            "venue_id": show.venues.id,
            "venue_name": show.venues.name,
            "artist_id": show.artist_id,
            "artist_name": show.artists.name,
            "artist_image_link": show.artists.image_link,
            "start_time": str(show.start_time)
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    try:
        form = ShowForm(request.form)
        show = Show()
        form.populate_obj(show)
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    except:
        db.session.rollback()
        flash('Failed to create show')
    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# Default port:
if __name__ == '__main__':
    app.run()
