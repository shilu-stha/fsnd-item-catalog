import time
from functools import update_wrapper
from flask import request
from flask import Flask, jsonify, render_template, url_for, flash
from models import Base, Item, Category, User

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import desc

# New import for oauth
from flask import session as login_session
import random, string

import json
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import requests
from flask import make_response
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth() 


engine = create_engine('sqlite:///bigbazar.db')

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Udacity FSND - Catalog App"

#Show all catalog
@app.route('/')
@app.route('/catalog')
def homePage():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    
    categories = session.query(Category).all()
    items = session.query(Item).all()
    for i in items:
		print ('Name:', i.name)
		print ('Created Date:', i.created_date)
    # get only the latest created items
    latest = session.query(Item).order_by(desc(Item.created_date)).limit(5).all()
    for item in latest:
        print('Name:', item.name)

    access_token = login_session.get('access_token')
    if access_token is None:
        return render_template('publichomepage.html', categories = categories, items = items, latest = latest)
    else:
        return render_template('homepage.html', categories = categories, items = items, latest = latest)

# Shows category and its item list
@app.route('/catalog/<string:category_name>/items') 
def showCategoryAndItems(category_name):     
    category = session.query(Category).filter_by(name = category_name).one()
    items = session.query(Item).filter_by(category_id = category.id).all()
    
    #creator = getUserInfo(category.user_id)   
    #if creator != login_session['user_id']:
    #    return render_template('category.html', category = category, items = items)
    #else:
    #access_token = login_session.get('access_token')
    access_token = login_session.get('access_token')
    if access_token is None:
    	return render_template('publiccategory.html', category = category, items = items)
    else:
        return render_template('category.html', category = category, items = items)
        
#Show specific info of the item
@app.route('/catalog/<string:category_name>/<string:item_name>') 
def showSpecificItem(category_name, item_name):     
    category = session.query(Category).filter_by(name = category_name).one()
    item = session.query(Item).filter_by(category_id = category.id).filter_by(name = item_name).one()
    access_token = login_session.get('access_token')
    if access_token is None:
        return render_template('publicitemspage.html', item = item)
    else:
        return render_template('itemspage.html', item = item)


#Create a new restaurant
@app.route('/catalog/new/', methods=['GET','POST'])
@auth.login_required
def addItem():
    now = datetime.datetime.now()

    access_token = login_session.get('access_token')
    if access_token is None:
        return redirect('/login')
    
    if request.method == 'POST':
        newItem = Item(name = request.form['name'], description = request.form['description'],
            price = request.form['price'], created_date = now.strftime("%Y-%m-%d"),
            user_id =login_session['user_id'])
        session.add(newItem)
        flash('New Item %s Successfully Created' % newItem.name)
        session.commit()
        return redirect(url_for('homePage.html'))
    else:
        return render_template('addItem.html')

#Edit a restaurant
@app.route('/<string:category_name>/<int:category_id>/edit/', methods = ['GET', 'POST'])
@auth.login_required
def editItems(category_id):
    access_token = login_session.get('access_token')
    if access_token is None:
        return redirect('/login')
    
    editedItem = session.query(Item).filter_by(id = category_id).one()
    if request.method == 'POST':
      if request.form['name']:
        editedRestaurant.name = request.form['name']
        flash('Restaurant Successfully Edited %s' % editedRestaurant.name)
        return redirect(url_for('homePage.html'))
    else:
        return render_template('editItem.html', restaurant = editedRestaurant)

##### Authorization #####
@app.route('/oauth/<provider>', methods = ['POST'])
def login(provider):
    auth_code = request.json.get('auth_code')
    if provider == 'google':
        try:
            # Upgrade the authorization code into a credentials object
            oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
            oauth_flow.redirect_uri = 'postmessage'
            credentials = oauth_flow.step2_exchange(auth_code)
        except FlowExchangeError:
            response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response
          
        # Check that the access token is valid.
        access_token = credentials.access_token
        url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
        h = httplib2.Http()
        result = json.loads(h.request(url, 'GET')[1])
        # If there was an error in the access token info, abort.
        if result.get('error') is not None:
            response = make_response(json.dumps(result.get('error')), 500)
            response.headers['Content-Type'] = 'application/json'
            
        # # Verify that the access token is used for the intended user.
        # gplus_id = credentials.id_token['sub']
        # if result['user_id'] != gplus_id:
        #     response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
        #     response.headers['Content-Type'] = 'application/json'
        #     return response

        # # Verify that the access token is valid for this app.
        # if result['issued_to'] != CLIENT_ID:
        #     response = make_response(json.dumps("Token's client ID does not match app's."), 401)
        #     response.headers['Content-Type'] = 'application/json'
        #     return response

        # stored_credentials = login_session.get('credentials')
        # stored_gplus_id = login_session.get('gplus_id')
        # if stored_credentials is not None and gplus_id == stored_gplus_id:
        #     response = make_response(json.dumps('Current user is already connected.'), 200)
        #     response.headers['Content-Type'] = 'application/json'
        #     return response
        print "Step 2 Complete! Access Token : %s " % credentials.access_token

        #STEP 3 - Find User or make a new one
        
        #Get user info
        h = httplib2.Http()
        userinfo_url =  "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {'access_token': credentials.access_token, 'alt':'json'}
        answer = requests.get(userinfo_url, params=params)
      
        data = answer.json()

        name = data['name']
        picture = data['picture']
        email = data['email']
        
        
     
        #see if user exists, if it doesn't make a new one
        user = session.query(User).filter_by(email=email).first()
        if not user:
            user = User(username = name, picture = picture, email = email)
            session.add(user)
            session.commit()

        
        #STEP 4 - Make token
        token = user.generate_auth_token(600)

        

        #STEP 5 - Send back token to the client 
        return jsonify({'token': token.decode('ascii')})
        
        #return jsonify({'token': token.decode('ascii'), 'duration': 600})
    else:
        return 'Unrecoginized Provider'

# G-Connect
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    userId = getUserID(login_session["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
 
    print login_session['user_id']
    return output

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

        return None

#ADD a /users route here
@app.route('/login', methods =['GET','POST'])
def new_user():
    if request.method == 'POST':
        #name = request.json.get('name')
        username = request.json.get('uname')
        password = request.json.get('password')
        if username is None or password is None:
            print "missing arguments"
            abort(400) 
            
        if session.query(User).filter_by(username = username).first() is not None:
            print "existing user"
            user = session.query(User).filter_by(username=username).first()
            return jsonify({'message':'user already exists'}), 200#, {'Location': url_for('get_user', id = user.id, _external = True)}
            
        user = User(username = username)
        user.hash_password(password)
        session.add(user)
        session.commit()
        #return jsonify({ 'username': user.username }), 201
        return redirect(url_for('homePage'))
    else:
        return render_template('login.html')

#ADD @auth.verify_password here
@auth.verify_password
def verify_password(username_or_token, password):
    user_id = User.verify_auth_token(username_or_token)
    if user_id:
        user = session.query(User).filter_by(id = user_id).one()
    else:
        user = session.query(User).filter_by(username = username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True

#ADD a /users route here
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    
    if newUser is None or password is None:
        print "missing arguments"
        abort(400) 
    
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

@app.route('/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})

@app.route('/users/<int:id>')
def get_user(id):
    user = session.query(User).filter_by(id=id).one()
    if not user:
        abort(400)
    return jsonify({'username': user.username})

def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None
##### END Authorization #####

if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host = '0.0.0.0', port = 8000)
	  