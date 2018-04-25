from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

import cgi

## import for CRUD Operations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Item, Category

# Create Session and connect to db
engine = create_engine('sqlite:///bargainMart.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

class WebServerHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path.endswith("/restaurants"):
            restaurants = session.query(Restaurant).all()
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            message = ""
            message += "<html><body>"
            message += "<a href='/restaurants/new'>Make a new Restaurant</a>"
            message += "</br>"
            message += "List of Restaurants"
            for restaurant in restaurants:
                message += "</br>"
                message += "%s" % restaurant.name
                message += "</br>"
                message += "<a href='/restaurants/%d/edit'>Edit</a>" % restaurant.id
                message += "</br>"
                message += "<a href='/restaurants/%d/delete'>Delete</a>" % restaurant.id            
            message += "</body></html>"
            self.wfile.write(message)
            print message
            return

        if self.path.endswith("/restaurants/new"):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            message = ""
            message += "<html><body>"
            message += '''<form method='POST' enctype='multipart/form-data' action='/restaurants'>
            <h2>Make a New Restaurant</h2><input name="restaurantName" type="text" placeholder="New Restaurant Name">
            <input type="submit" value="Create"> </form>'''
            message += "</body></html>"
            self.wfile.write(message)
            print message
            return

        if self.path.endswith("/edit"):
            restaurantId = self.path.split("/")[2]
            restaurants = session.query(Restaurant).filter_by(id = restaurantId).one()
            if restaurants != []:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                message = ""
                message += "<html><body>"
                message += "<h2>%s</h2>" % restaurants.name
                message += """<form method='POST' enctype='multipart/form-data' 
                action='/restaurants/%s/edit'>""" %restaurantId
                message += "<input name='restaurantRename' type='text' placeholder='%s'>" % restaurants.name
                message += "<input type='submit' value='Rename'> </form>"
                message += "</body></html>"
                self.wfile.write(message)
                print message
            else:
                pass
            
            return

        if self.path.endswith("/delete"):
            restaurantId = self.path.split("/")[2]
            restaurants = session.query(Restaurant).filter_by(id = restaurantId).one()
            if restaurants != []:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                message = ""
                message += "<html><body>"
                message += "<h2>Are you sure you want to Delete %s?</h2>" % restaurants.name
                message += """<form method='POST' enctype='multipart/form-data' 
                            action='/restaurants/%s/delete'>""" %restaurantId
                message += "<input type='submit' value='Delete'> </form>"
                message += "</body></html>"
                self.wfile.write(message)
                print message
            else:
                pass
            
            return

        if self.path.endswith("/hello"):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            message = ""
            message += "<html><body>Hello!</body></html>"
            message += '''<form method='POST' enctype='multipart/form-data' action='/hello'>
            <h2>What would you like me to say?</h2><input name="message" type="text" >
            <input type="submit" value="Submit"> </form>'''
            message += "</body></html>"
            self.wfile.write(message)
            print message
            return

        if self.path.endswith("/hola"):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            message = ""
            message += "<html><body>&#161Hola <a href='/hello'>Back to Hello</a></body> </html>"
            message += '''<form method='POST' enctype='multipart/form-data' action='/hello'>
            <h2>What would you like me to say?</h2><input name="message" type="text" >
            <input type="submit" value="Submit"> </form>'''
            message += "</body></html>"
            self.wfile.write(message)
            print message
            return

        else:
            self.send_error(404, 'File Not Found: %s' % self.path)


    def do_POST(self):
        try:
            if(self.path.endswith("/restaurants/new")):
                ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    restaurantName = fields.get('restaurantName')
            
                # Add to Database
                restaurant = Restaurant(name = restaurantName[0])
                session.add(restaurant)
                session.commit()

                self.send_response(301)
                self.send_header('Content-type', 'text/html')
                self.send_header('Location', '/restaurants')
                self.end_headers()
            
                output = "Added to Database"

            if(self.path.endswith("/edit")):
                ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                
                restaurantName = fields.get('restaurantRename')
                restaurantId = self.path.split("/")[2]            
                restaurant = session.query(Restaurant).filter_by(id = restaurantId).one()
                if restaurant != []:
                    restaurant.name = restaurantName[0]
                    session.add(restaurant)
                    session.commit()

                    self.send_response(301)
                    self.send_header('Content-type', 'text/html')
                    self.send_header('Location', '/restaurants')
                    self.end_headers()
            
                    output = "Updated to Database"

            if(self.path.endswith("/delete")):
                ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
                
                restaurantId = self.path.split("/")[2]            
                
                restaurant = session.query(Restaurant).filter_by(id = restaurantId).one()
                if restaurant != []:
                    session.delete(restaurant)
                    session.commit()

                    self.send_response(301)
                    self.send_header('Content-type', 'text/html')
                    self.send_header('Location', '/restaurants')
                    self.end_headers()
            
                    output = "Deleted from Database"




            #output += "<html><body>"
            #self.send_response(301)
            #self.send_header('Content-type', 'text/html')
            #self.end_headers()
            #ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            #if ctype == 'multipart/form-data':
            #    fields = cgi.parse_multipart(self.rfile, pdict)
            #    messagecontent = fields.get('message')
            #output += " <h2> Okay, how about this: </h2>"
            #output += "<h1>%s</h1>" % messagecontent[0]
            #output += '''<form method='POST' enctype='multipart/form-data' action='/hello'>
            #<h2>What would you like me to say?</h2><input name="message" type="text" >
            #<input type="submit" value="Submit"> </form>'''
            #output += "</body></html>"
            #self.wfile.write(output)
            print output
        except Exception as e:
            pass


def main():
    try:
        port = 8080
        server = HTTPServer(('', port), WebServerHandler)
        print "Web Server running on port %s" % port
        server.serve_forever()
    except KeyboardInterrupt:
        print " ^C entered, stopping web server...."
        server.socket.close()

if __name__ == '__main__':
    main()
