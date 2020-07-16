#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, jsonify, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm
from flask_migrate import Migrate
from forms import *
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
  name = db.Column(db.String, nullable=False)
  city = db.Column(db.String(120), nullable=False)
  state = db.Column(db.String(120), nullable=False)
  address = db.Column(db.String(120), nullable=False)
  phone = db.Column(db.String(120), nullable=False)
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  genres = db.Column(db.ARRAY(db.String()), nullable=False)
  website = db.Column(db.String(300))
  seeking_talent = db.Column(db.Boolean, default=True)
  seeking_description = db.Column(db.String(300))
  shows = db.relationship('Show', backref='venue')


class Artist(db.Model):
  __tablename__ = 'Artist'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String, nullable=False)
  city = db.Column(db.String(120), nullable=False)
  state = db.Column(db.String(120), nullable=False)
  phone = db.Column(db.String(120), nullable=False)
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  genres = db.Column(db.ARRAY(db.String()), nullable=False)
  website = db.Column(db.String(300))
  seeking_venue = db.Column(db.Boolean, default=True)
  seeking_description = db.Column(db.String(300))
  shows = db.relationship('Show', backref='artist')


class Show(db.Model):
  __tablename__ = 'Show'

  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
  start_time = db.Column(db.DateTime(), nullable=False)


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
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = []
  cities = db.session.query(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
  for i, j in cities:
      venues = Venue.query.filter_by(city=i, state=j).all()
      venues_by_city = {
          "city": i,
          "state": j,
          "venues": venues,
      }
      data.append(venues_by_city)
  return render_template('pages/venues.html', areas=data)
  
@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  data = db.session.query(Venue).filter(Venue.name.ilike(f'%{search_term}%')).all()
  response = {
    "count": len(data),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  shows = db.session.query(Venue, Show).filter_by(id=venue_id).join(Show, Show.venue_id==Venue.id).all()
  upcoming = []
  past = []
  for i in shows:
    if i[1].start_time > datetime.now():
      upcoming.append({
        "artist_id": i[1].artist_id,
        "artist_name": Artist.query.filter_by(id=i[1].artist_id).first().name,
        "artist_image_link": Artist.query.filter_by(id=i[1].artist_id).first().image_link,
        "start_time": format_datetime(str(i[1].start_time))
      })
    else:
      past.append({
        "artist_id": i[1].artist_id,
        "artist_name": Artist.query.filter_by(id=i[1].artist_id).first().name,
        "artist_image_link": Artist.query.filter_by(id=i[1].artist_id).first().image_link,
        "start_time": format_datetime(str(i[1].start_time))
      })
  data = {
      "id": venue.id,
      "name": venue.name,
      "genres": venue.genres,
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website": venue.website,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
      "image_link": venue.image_link,
      "past_shows": past,
      "upcoming_shows": upcoming,
      "past_shows_count": len(past),
      "upcoming_shows_count": len(upcoming)
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
    new_venue_request = VenueForm()
    name = new_venue_request.name.data
    city = new_venue_request.city.data
    state = new_venue_request.state.data
    address = new_venue_request.address.data
    phone = new_venue_request.phone.data
    genres = new_venue_request.genres.data
    facebook_link = new_venue_request.facebook_link.data
    website = new_venue_request.website.data
    image_link = new_venue_request.image_link.data
    seeking_talent = new_venue_request.seeking_talent.data
    seeking_description = new_venue_request.seeking_description.data

    new_venue = Venue(name=name, city=city, state=state, address=address,
                      phone=phone, genres=genres, facebook_link=facebook_link,
                      website=website, image_link=image_link,
                      seeking_talent=seeking_talent,
                      seeking_description=seeking_description)

    db.session.add(new_venue)
    db.session.commit()

    flash('Venue ' + request.form['name'] + ' was successfully listed!')

  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  
  finally:
      db.session.close()

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return jsonify({ 'success': True })

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.order_by('id').all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  data = db.session.query(Artist).filter(Artist.name.ilike(f'%{search_term}%')).all()
  response = {
    "count": len(data),
    "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  shows = db.session.query(Artist, Show).filter_by(id=artist_id).join(Show, Show.artist_id==Artist.id).all()
  upcoming = []
  past = []
  for i in shows:
    if i[1].start_time > datetime.now():
      upcoming.append({
        "venue_id": i[1].venue_id,
        "venue_name": Venue.query.filter_by(id=i[1].venue_id).first().name,
        "venue_image_link": Venue.query.filter_by(id=i[1].venue_id).first().image_link,
        "start_time": format_datetime(str(i[1].start_time))
      })
    else:
      past.append({
        "venue_id": i[1].venue_id,
        "venue_name": Venue.query.filter_by(id=i[1].venue_id).first().name,
        "venue_image_link": Venue.query.filter_by(id=i[1].venue_id).first().image_link,
        "start_time": format_datetime(str(i[1].start_time))
      })

  data = {
      "id": artist.id,
      "name": artist.name,
      "genres": artist.genres,
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "website": artist.website,
      "facebook_link": artist.facebook_link,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link,
      "past_shows": past,
      "upcoming_shows": upcoming,
      "past_shows_count": len(past),
      "upcoming_shows_count": len(upcoming),
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
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
    new_artist_request = ArtistForm()
    name = new_artist_request.name.data
    city = new_artist_request.city.data
    state = new_artist_request.state.data
    phone = new_artist_request.phone.data
    genres = new_artist_request.genres.data
    facebook_link = new_artist_request.facebook_link.data
    website = new_artist_request.website.data
    image_link = new_artist_request.image_link.data
    seeking_venue = new_artist_request.seeking_venue.data
    seeking_description = new_artist_request.seeking_description.data

    new_artist = Artist(name=name, city=city, state=state, phone=phone,
                        genres=genres, facebook_link=facebook_link,
                        website=website, image_link=image_link,
                        seeking_venue=seeking_venue,
                        seeking_description=seeking_description)

    db.session.add(new_artist)
    db.session.commit()

    flash('Artist ' + request.form['name'] + ' was successfully listed!')

  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')

  finally:
    db.session.close()

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = Show.query.all()
  data = []
  for i in shows:
    data.append({
        "venue_id": i.venue_id,
        "venue_name": Venue.query.filter_by(id=i.venue_id).first().name,
        "artist_id": i.artist_id,
        "artist_name": Artist.query.filter_by(id=i.artist_id).first().name,
        "artist_image_link": Artist.query.filter_by(id=i.artist_id).first().image_link,
        "start_time": format_datetime(str(i.start_time))
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']
    show = Show(artist_id=artist_id, venue_id=venue_id,
                start_time=start_time)

    db.session.add(show)
    db.session.commit()

    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')

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
      Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
  )
  app.logger.setLevel(logging.INFO)
  file_handler.setLevel(logging.INFO)
  app.logger.addHandler(file_handler)
  app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
