#!/usr/bin/env python3
from flask import (
    Flask, render_template, jsonify, flash,
    url_for, request, logging, redirect, g)
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from cat_db_setup import Base, Breed, Cat
from functools import wraps
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "The CAT-alog"

# DB Setup
engine = create_engine('sqlite:///cats.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def login_required(f):
    @wraps(f)
    def is_logged_in(*args, **kwargs):
        if 'username' not in login_session:
            flash('You must first log-in to add or edit', 'warning')
            return redirect(url_for('main'))
        return f(*args, **kwargs)
    return is_logged_in


# Main Menu
@app.route('/')
@app.route('/main')
def main():
    state = ''.join(
        random.choice(
            string.ascii_uppercase + string.digits)for x in range(32))
    login_session['state'] = state
    return render_template('main.html', STATE=state)


# Google oAuth
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain oauth code
    request.get_data()
    code = request.data.decode('utf-8')

    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    response_string = response.decode('utf-8')
    result = json.loads(response_string)

    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify Token for User
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify token for app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the token
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Import user information
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px; border-radius: 150px;'
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;" > '
    flash("You are now logged in as %s" % login_session['username'], 'info')
    return output


@app.route('/gdisconnect')
@login_required
def gdisconnect():
    access_token = login_session['access_token']
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = (
        'https://accounts.google.com/o/oauth2/revoke?token=%s'
        % access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if (result['status'] == '200') or (result['status'] == '400'):
        del login_session['gplus_id']
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        flash("You have logged out", 'success')
        return redirect(url_for('main'))
    else:
        flash("You have failed to log out", 'warning')
        return redirect(url_for('main'))


# Display Cat Breeds
@app.route('/breed/')
def breed():
    breed = session.query(Breed).order_by(asc(Breed.id))
    return render_template('breeds.html', breed=breed)


# Create New Cat Breed
@app.route('/breed/new/', methods=['GET', 'POST'])
@login_required
def newBreed():
    if 'username' not in login_session:
        flash('You must first log-in to add or edit', 'warning')
        return redirect('/main')
    if request.method == 'POST':
        newBreed = Breed(name=request.form['name'])
        session.add(newBreed)
        flash('New Breed %s Has Been Bred' % newBreed.name, 'info')
        session.commit()
        return redirect(url_for('breed'))
    else:
        return render_template('newbreed.html')


# Edit Cat Breed
@app.route('/breed/<int:breed_id>/edit/', methods=['GET', 'POST'])
@login_required
def editBreed(breed_id):
    if 'username' not in login_session:
        flash('You must first log-in to add or edit', 'warning')
        return redirect('/main')
    editedBreed = session.query(
        Breed).filter_by(id=breed_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedBreed.name = request.form['name']
            flash('Cat Breed Edited %s' % editedBreed.name, 'info')
            return redirect(url_for('breed'))
    else:
        return render_template(
            'editBreed.html', breed=editedBreed)


# Delete a Breed
@app.route('/breed/<int:breed_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteBreed(breed_id):
    if 'username' not in login_session:
        flash('You must first log-in to add or edit', 'warning')
        return redirect('/main')
    breedToDelete = session.query(Breed).filter_by(id=breed_id).one()
    if request.method == 'POST':
        session.delete(breedToDelete)
        flash('%s Are Now Extinct' % breedToDelete.name, 'info')
        session.commit()
        return redirect(url_for('breed', breed_id=breed_id))
    else:
        return render_template('deletebreed.html', breed=breedToDelete)


# Display Cats
@app.route('/breed/<int:breed_id>/')
@app.route('/breed/<int:breed_id>/cat/')
def cats(breed_id):
    breed = session.query(Breed).filter_by(id=breed_id).one()
    cats = session.query(Cat).filter_by(
        breed_id=breed_id).all()
    return render_template('cats.html', cats=cats, breed=breed)


# Add New Cat
@app.route('/breed/<int:breed_id>/cat/new/', methods=['GET', 'POST'])
@login_required
def newCat(breed_id):
    if 'username' not in login_session:
        flash('You must first log-in to add or edit', 'warning')
        return redirect('/main')
    session.query(Breed).filter_by(id=breed_id).one()
    if request.method == 'POST':
        newCat = Cat(
            name=request.form['name'], bio=request.form['bio'],
            breed_id=breed_id)
        session.add(newCat)
        session.commit()
        flash('New Cat %s Is Born' % (newCat.name), 'info')
        return redirect(url_for('cats', breed_id=breed_id))
    else:
        return render_template('newcat.html', breed_id=breed_id)


# Edit a Cat
@app.route(
    '/breed/<int:breed_id>/cat/<int:cat_id>/edit/',
    methods=['GET', 'POST'])
@login_required
def editCat(breed_id, cat_id):
    if 'username' not in login_session:
        flash('You must first log-in to add or edit', 'warning')
        return redirect('/main')
    editedCat = session.query(Cat).filter_by(id=cat_id).one()
    session.query(Breed).filter_by(id=breed_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedCat.name = request.form['name']
        if request.form['bio']:
            editedCat.bio = request.form['bio']
        session.add(editedCat)
        session.commit()
        flash('Cat Genetically Modified!', 'info')
        return redirect(url_for('cats', breed_id=breed_id))
    else:
        return render_template('editcat.html', breed_id=breed_id,
                               cat_id=cat_id, cat=editedCat)


# Delete a Cat
@app.route(
    '/breed/<int:breed_id>/cat/<int:cat_id>/delete/',
    methods=['GET', 'POST'])
@login_required
def deleteCat(breed_id, cat_id):
    if 'username' not in login_session:
        flash('You must first log-in to add or edit', 'warning')
        return redirect('/main')
    catToDelete = session.query(Cat).filter_by(id=cat_id).one()
    session.query(Breed).filter_by(id=breed_id).one()
    if request.method == 'POST':
        session.delete(catToDelete)
        session.commit()
        flash('Rest in peace, %s' % catToDelete.name, 'info')
        return redirect(url_for('cats', breed_id=breed_id))
    else:
        return render_template('deletecat.html', cat=catToDelete)


# Dogs Info
@app.route('/dogs')
def dogs():
    return render_template('dogs.html')


# JSON APIs
@app.route('/breed/<int:breed_id>/cat/JSON/')
def BreedJSON(breed_id):
    session.query(Breed).filter_by(id=breed_id).one()
    cats = session.query(Cat).filter_by(
        breed_id=breed_id).all()
    return jsonify(cats=[i.serialize for i in cats])


@app.route('/breed/<int:breed_id>/cat/<int:cat_id>/JSON/')
def CatJSON(breed_id, cat_id):
    cats = session.query(Cat).filter_by(id=cat_id).one()
    return jsonify(cats=cats.serialize)


@app.route('/breed/JSON/')
def breedsJSON():
    breeds = session.query(Breed).all()
    return jsonify(breeds=[r.serialize for r in breeds])


# executes app / hosts on specified IP / port
if __name__ == '__main__':
    app.secret_key = 'bamboo'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
