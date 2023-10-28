# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import sys
# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# DONE: connect to a local postgresql database -- DONE in Config

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    show = db.relationship("Show", backref="venue_shows", cascade="all, delete", lazy='dynamic')

    def __repr__(self):
        return f'<Venue id: {self.id}, name: {self.name}>'

    def json(self):
        upcoming_shows = self.show.filter(Show.start_time > datetime.now()).all()
        past_shows = self.show.filter(Show.start_time < datetime.now()).all()

        return {
            'id': self.id,
            'name': self.name,
            'city': self.city,
            'state': self.state,
            'address': self.address,
            'phone': self.phone,
            'genres':  json.loads(self.genres),
            'image_link': self.image_link,
            'facebook_link': self.facebook_link,
            'website': self.website,
            'seeking_talent': self.seeking_talent,
            'seeking_description': self.seeking_description,
            'upcoming_shows_count': len(upcoming_shows),
            'upcoming_shows': upcoming_shows,
            'past_shows_count': len(past_shows),
            'past_shows': past_shows,
        }


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    show = db.relationship("Show", backref="artist_shows", cascade="all, delete", lazy='dynamic')

    def __repr__(self):
        return f'<Artist id: {self.id}, name: {self.name}>'

    def json(self):
        upcoming_shows = self.show.filter(Show.start_time > datetime.now()).all()
        past_shows = self.show.filter(Show.start_time < datetime.now()).all()

        return {
        'id': self.id,
        'name': self.name,
        'city': self.city,
        'state': self.state,
        'phone': self.phone,
        'genres': json.loads(self.genres),
        'image_link': self.image_link,
        'facebook_link': self.facebook_link,
        'website': self.website,
        'seeking_venue': self.seeking_venue,
        'seeking_description': self.seeking_description,
        'upcoming_shows_count': len(upcoming_shows),
        'upcoming_shows': upcoming_shows,
        'past_shows_count': len(past_shows),
        'past_shows': past_shows,
        }


class Show(db.Model):
    # Table name
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id', ondelete="CASCADE"), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id', ondelete="CASCADE"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    artist = db.relationship("Artist", backref="show_artists", lazy=True)
    venue = db.relationship("Venue", backref="show_venues", lazy=True)
                            

    def __repr__(self):
        return f'<Show id: {self.id}, artist_id: {self.artist_id}, venue_id: {self.venue_id} start_time: {self.start_time}>'


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    try:
        locations = Venue.query.distinct(Venue.city, Venue.state).all()
        print(locations)
        data = []
        for venue in locations:
            object = {}
            object['city'] = venue.city
            object['state'] = venue.state

            venues = []

            venue_data = Venue.query.filter(
                Venue.state == venue.state, Venue.city == venue.city).all()

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            for this_venue in venue_data:
                current_venue = {}
                current_venue['id'] = this_venue.id
                current_venue['name'] = this_venue.name
                current_venue['num_upcoming_shows'] = Show.query.filter(
                    db.and_(Show.start_time > current_time, Show.venue_id == this_venue.id)).count()
                venues.append(current_venue)
            object['venues'] = venues
            data.append(object)
    except:
        flash(
            f"Sorry due, to an issue on our end, we are unable to display the venues page.", category="error")
        abort(500)
    finally:
        return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # search for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term', '')
    search = "%{}%".format(search_term)
    venues = Venue.query.filter(Venue.name.like(search)).all()
    response={
        "count": len(venues),
        "data": venues
    }

    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # DONE: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.get(venue_id)
    setattr(venue, "genres", venue.genres.split(",")) # convert genre string back to array

    # get past shows
    past_shows = list(filter(lambda show: show.start_time < datetime.now(), venue.show))
    temp_shows = []
    for show in past_shows:
        temp = {}
        temp["artist_name"] = show.artists.name
        temp["artist_id"] = show.artists.id
        temp["artist_image_link"] = show.artists.image_link
        temp["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        temp_shows.append(temp)

    setattr(venue, "past_shows", temp_shows)
    setattr(venue,"past_shows_count", len(past_shows))

    # get future shows
    upcoming_shows = list(filter(lambda show: show.start_time > datetime.now(), venue.show))
    temp_shows = []
    for show in upcoming_shows:
        temp = {}
        temp["artist_name"] = show.artists.name
        temp["artist_id"] = show.artists.id
        temp["artist_image_link"] = show.artists.image_link
        temp["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        temp_shows.append(temp)

    setattr(venue, "upcoming_shows", temp_shows)    
    setattr(venue,"upcoming_shows_count", len(upcoming_shows))

    return render_template('pages/show_venue.html', venue=venue)


#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # DONE: insert form data as a new Venue record in the db, instead
    # DONE: modify data to be the data object returned from db insertion
    form = VenueForm(request.form)

    if form.validate():
        try:
            new_venue = Venue(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                address=form.address.data,
                phone=form.phone.data,
                genres=",".join(form.genres.data), # convert array to string separated by commas
                facebook_link=form.facebook_link.data,
                image_link=form.image_link.data,
                seeking_talent=form.seeking_talent.data,
                seeking_description=form.seeking_description.data,
                website=form.website_link.data
            )
            db.session.add(new_venue)
            db.session.commit()
            flash('Venue ' + request.form['name'] + ' was successfully listed!')

        except Exception:
            db.session.rollback()
            print(sys.exc_info())
            flash('An error occurred. Venue' + ' could not be listed.')

        finally:
            db.session.close()
    else:
        print("\n\n", form.errors)
        flash('An error occurred. Venue' + ' could not be listed.')

    return redirect(url_for("index"))


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    # return None
    error = None

    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        
    except:
        db.session.rollback()
        error = 'Invalid data'
        print(sys.exc_info())

    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue ' + venue_id + ' could not be deleted.')
        abort(500)
    else:
        flash('Venue ' + venue_id + ' was successfully deleted!')
        return redirect(url_for('index'))


#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    artists = Artist.query.all()

    return render_template('pages/artists.html', artists=artists)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')
    search = "%{}%".format(search_term)
    artists = Artist.query.filter(Artist.name.like(search)).all()
    response={
        "count": len(artists),
        "data": artists
    }
    
    return render_template('pages/search_artists.html', results=response, search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)
    setattr(artist, "genres", artist.genres.split(",")) # convert genre string back to array

    # get past shows
    past_shows = list(filter(lambda show: show.start_time < datetime.now(), artist.show))
    temp_shows = []
    for show in past_shows:
        temp = {}
        temp["venue_name"] = show.venues.name
        temp["venue_id"] = show.venues.id
        temp["venue_image_link"] = show.venues.image_link
        temp["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")

        temp_shows.append(temp)

    setattr(artist, "past_shows", temp_shows)
    setattr(artist, "past_shows_count", len(past_shows))


    # get upcoming shows
    upcoming_shows = list(filter(lambda show: show.start_time > datetime.now(), artist.show))
    temp_shows = []
    for show in upcoming_shows:
        temp = {}
        temp["venue_name"] = show.venues.name
        temp["venue_id"] = show.venues.id
        temp["venue_image_link"] = show.venues.image_link
        temp["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")

        temp_shows.append(temp)

    setattr(artist, "upcoming_shows", temp_shows)
    setattr(artist, "upcoming_shows_count", len(upcoming_shows))

    return render_template('pages/show_artist.html', artist=artist)


#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()  
    artist = Artist.query.get(artist_id)
    form.genres.data = artist.genres.split(",") # convert genre string back to array
    
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm(request.form)

    if form.validate():
        try:
            artist = Artist.query.get(artist_id)

            artist.name = form.name.data
            artist.city=form.city.data
            artist.state=form.state.data
            artist.phone=form.phone.data
            artist.genres=",".join(form.genres.data) # convert array to string separated by commas
            artist.facebook_link=form.facebook_link.data
            artist.image_link=form.image_link.data
            artist.seeking_venue=form.seeking_venue.data
            artist.seeking_description=form.seeking_description.data
            artist.website=form.website_link.data

            db.session.add(artist)
            db.session.commit()
            flash("Artist " + artist.name + " was successfully edited!")
        except:
            db.session.rollback()
            print(sys.exc_info())
            flash("Artist was not edited successfully.")
        finally:
            db.session.close()
    else:
        print("\n\n", form.errors)
        flash("Artist was not edited successfully.")

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    form.genres.data = venue.genres.split(",") # convert genre string back to array
    
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form)
    
    if form.validate():
        try:
            venue = Venue.query.get(venue_id)

            venue.name = form.name.data
            venue.city=form.city.data
            venue.state=form.state.data
            venue.address=form.address.data
            venue.phone=form.phone.data
            venue.genres=",".join(form.genres.data) # convert array to string separated by commas
            venue.facebook_link=form.facebook_link.data
            venue.image_link=form.image_link.data
            venue.seeking_talent=form.seeking_talent.data
            venue.seeking_description=form.seeking_description.data
            venue.website=form.website_link.data

            db.session.add(venue)
            db.session.commit()

            flash("Venue " + form.name.data + " edited successfully")
            
        except Exception:
            db.session.rollback()
            print(sys.exc_info())
            flash("Venue was not edited successfully.")
        finally:
            db.session.close()
    else: 
        print("\n\n", form.errors)
        flash("Venue was not edited successfully.")

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm(request.form)

    if form.validate():
        try:
            new_artist = Artist(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                phone=form.phone.data,
                genres=",".join(form.genres.data), # convert array to string separated by commas
                image_link=form.image_link.data,
                facebook_link=form.facebook_link.data,
                website=form.website_link.data,
                seeking_venue=form.seeking_venue.data,
                seeking_description=form.seeking_description.data,
            )
            db.session.add(new_artist)
            db.session.commit()
            flash("Artist " + request.form["name"] + " was successfully listed!")
        except Exception:
            db.session.rollback()
            flash("Artist was not successfully listed.")
        finally:
            db.session.close()
    else:
        print(form.errors)
        flash("Artist was not successfully listed.")

    return redirect(url_for("index"))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    data = []

    shows = Show.query.all()
    for show in shows:
        temp = {}
        temp["venue_id"] = show.venue.id
        temp["venue_name"] = show.venue.name
        temp["artist_id"] = show.artist.id
        temp["artist_name"] = show.artist.name
        temp["artist_image_link"] = show.artist.image_link
        temp["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        
        data.append(temp)
    
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm(request.form)
    
    if form.validate():
        try:
            new_show = Show(
                artist_id=form.artist_id.data,
                venue_id=form.venue_id.data,
                start_time=form.start_time.data
            )
            db.session.add(new_show)
            db.session.commit()
            flash('Show was successfully listed!')
        except Exception:
            db.session.rollback()
            print(sys.exc_info())
            flash('Show was not successfully listed.')
        finally:
            db.session.close()
    else:
        print(form.errors)
        flash('Show was not successfully listed.')

    return redirect(url_for("index"))
    ############################
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead

    # on successful db insert, flash success
    # flash('Show was successfully listed!')
    # # TODO: on unsuccessful db insert, flash an error instead.
    # # e.g., flash('An error occurred. Show could not be listed.')
    # # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    # return render_template('pages/home.html')


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

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
