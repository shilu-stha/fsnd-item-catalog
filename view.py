from flask import request, Flask, jsonify, render_template, url_for, flash, redirect, make_response
from models import Base, Item, Category, User
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import desc
from flask import session as login_session
import random, string, json, httplib2, requests
from datetime import datetime
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id'] 

engine = create_engine('sqlite:///bigbazar.db', connect_args={'check_same_thread': False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

#ADD a /users route here
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])    
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

#Show all catalog
@app.route('/')
@app.route('/catalog')
def homePage():    
    categories = session.query(Category).all()
    items = session.query(Item).all()

    # get only the latest created items
    latest = session.query(Item).order_by(desc(Item.created_date)).limit(5).all()

    return render_template('homepage.html', categories = categories, items = items, latest = latest)

# Shows category and its item list
@app.route('/catalog/<string:category_name>/items') 
def showCategoryAndItems(category_name):     
    category = session.query(Category).filter_by(name = category_name).one()
    items = session.query(Item).filter_by(category_id = category.id).all()

    return render_template('category.html', category = category, items = items)
        
#Show specific info of the item
@app.route('/catalog/<string:category_name>/<string:item_name>') 
def showSpecificItem(category_name, item_name):     
    category = session.query(Category).filter_by(name = category_name).one()   
    item = session.query(Item).filter_by(category_id = category.id).filter_by(name = item_name).one()

    return render_template('itemspage.html', item = item)

#Add a new category
@app.route('/catalog/add', methods=['GET','POST'])
def addCategory():
    if 'username' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
        categories = session.query(Category).all()
        for category in categories:
            if category.name == request.form['name']:
                return "Duplicate entires are not allowed"

        currenttime = datetime.now()
        newCategory = Category(name = request.form['name'], description = request.form['description'],
                         created_date = currenttime, user_id = login_session['user_id'])
        session.add(newCategory)
        session.commit()
        flash('New Category %s Successfully Added' % newCategory.name)
        
        return redirect(url_for('homePage'))
    else:
        return render_template('addCategory.html')


#Add new Category Item
@app.route('/catalog/item/add', methods=['GET','POST'])
def addCategoryItem():
    if 'username' not in login_session:
        return redirect('/login')
     
    if request.method == 'POST':
        # Check for duplicate entires
        if session.query(Item).filter_by(name = request.form['name']).filter_by(category_id = request.form['category_id']).first() is not None:
            return "Duplicate entires are not allowed"

        currenttime = datetime.now()
        newItem = Item(name = request.form['name'], description = request.form['description'],
                       price = request.form['price'], created_date = currenttime,
                       category_id = request.form['category_id'],
                       user_id =login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash('New Item %s Successfully Added' % newItem.name)
        return redirect(url_for('homePage'))
    else:
        categories = session.query(Category).all()

        return render_template('addItem.html', categories = categories)

#Edit a restaurant
@app.route('/catalog/<string:item_name>/edit/', methods = ['GET', 'POST'])
def editCategoryItem(item_name):
    # we have made item_name unique
    editedItem = session.query(Item).filter_by(name = item_name).one()

    if 'username' not in login_session:
        return redirect('/login')

    creator = getUserInfo(editedItem.user_id)

    if creator.id != login_session['user_id']:
        return redirect('/login')

    categories = session.query(Category).all()

    if request.method == 'POST':
        currenttime = datetime.now()
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        if request.form['category_id']:
            editedItem.category_id = request.form['category_id']

        editedItem.updated_date = currenttime
        session.add(editedItem)
        session.commit()
        flash('Item Successfully Edited %s' % editedItem.name)
        return redirect(url_for('homePage'))
    else:
        return render_template('editItem.html', item = editedItem, categories = categories)


@app.route('/catalog/<string:item_name>/delete/', methods = ['GET', 'POST'])
def deleteCategoryItem(item_name):
    if 'username' not in login_session:
        return redirect('/login')

    selectedItem = session.query(Item).filter_by(name = item_name).one()

    creator = getUserInfo(selectedItem.user_id)

    if creator.id != login_session['user_id']:
        return redirect('/login')
  
    if request.method == 'POST':
        session.delete(selectedItem)
    	session.commit()
        flash('Item Successfully Deleted %s' % selectedItem.name)
        return redirect(url_for('homePage'))
    else:
        return render_template('deleteItem.html', selectedItem = selectedItem)

##### Authorization #####
@app.route('/login')
def login():
    # Create anti-forgery state token
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state

    return render_template('login.html', STATE=state)

@app.route('/logout')
def logout():
    if login_session['provider'] == 'google':
        gdisconnect()
        del login_session['gplus_id']
        del login_session['access_token']

    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['user_id']
    del login_session['provider']

    return redirect(url_for('homePage'))

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate anti-forgery state token
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
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')

    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
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
    login_session['provider'] = 'google'

    # See if user exists
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    return "Login Successful"

@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')

    if access_token is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

##### END Authorization #####

@app.route('/catalog/JSON')
def showCategoriesJSON():
	categories = session.query(Category).all()
	return jsonify(categories = [category.serialize for category in categories])

@app.route('/catalog/<int:catalog_id>/JSON')
@app.route('/catalog/<int:catalog_id>/items/JSON')
def showCategoryJSON(catalog_id):
	categoryItems = session.query(Item).filter_by(category_id = catalog_id).all()
	return jsonify(categoryItems = [categoryItem.serialize for categoryItem in categoryItems])

@app.route('/catalog/<int:catalog_id>/items/<int:item_id>/JSON')
def showCategoryItemJSON(catalog_id, item_id):
	categoryItem = session.query(Item).filter_by(id = item_id).first()
	return jsonify(categoryItem = [categoryItem.serialize])

if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'super_secret_key'
    app.run(host = '0.0.0.0', port = 8000)
