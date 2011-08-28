import sys
import os

import framework
from models import QueueItem, User

import cherrypy

try:
    import json
except:
    import simplejson as json 

def get_user(email_address):
    user = cherrypy.request.db.query(User).filter(User.email_address == email_address).first()
    # TODO: For now, just create the user if it doesn't exist
    if user is None:
        user = User(email_address)
        cherrypy.request.db.add(user)
    return user

def get_queue(user, movie_id=None):
    qry = cherrypy.request.db.query(QueueItem).filter(QueueItem.user == user)
    if movie_id:
        qry = qry.filter(QueueItem.movie_id == movie_id)
    return qry
 
class QueueView(object):
    @cherrypy.expose
    def index(self, email_address):
        #TODO: Check content type before returning list
        user = get_user(email_address)
        queue = get_queue(user)
        # TODO: Fix things so we're not deserializing then serializing again
        # TODO: Add the URL of each queued item to the list
        return json.dumps([json.loads(item.to_json()) for item in queue.all()])

class QueueItemView(object):
    @cherrypy.expose
    def add(self, email_address, movie_id, title=None):
        try:
            # Get the user
            user = get_user(email_address)
            # Make sure this movie isn't already in the queue
            if get_queue(user, movie_id).all():
                return json.dumps({"result":"ok"})
            item = QueueItem(movie_id, title, user)
            cherrypy.request.db.add(item)
            return json.dumps({"result":"ok"})
        except Exception, e:
            return json.dumps({"result":"error", "error_msg":str(e)})

    @cherrypy.expose
    def delete(self, email_address, movie_id):
        try:
            # Get the user
            user = get_user(email_address)
            queued_items = get_queue(user, movie_id).all()
            if queued_items:
                for queued_item in queued_items:
                    cherrypy.request.db.delete(queued_item)
            return json.dumps({"result":"ok"})
        except Exception, e:
            return json.dumps({"result":"error", "error_msg":str(e)})
    
    @cherrypy.expose
    def get(self, email_address, movie_id):
        print cherrypy.request.headers
        try:
            user = get_user(email_address)
            queued_items = get_queue(user, movie_id).all()
            if queued_items:
                return queued_items[0].to_json()
            else:
                return json.dumps({"queued":False})
        except Exception, e:
            return json.dumps({"queued":False, "error_msg":str(e)})

class Users(object):
    @cherrypy.expose    
    def index(self):
        # TODO: Do something more useful here?
        return "Users"

class Root(object):
    users = Users()
    
    @cherrypy.expose
    def index(self):
        # TODO: Return API info?
        return "Netflix Queue Service"

def setup_routes():
    #Setup routes
    d = cherrypy.dispatch.RoutesDispatcher()

    # For Routes 1.12+ only...
    d.mapper.explicit = False
    d.connect('users', '/users', Users())
    d.connect('queue', '/users/:email_address/queue', QueueView(), action="index")
    d.connect('queueitem', '/users/:email_address/queue/:movie_id', QueueItemView(), conditions={'method':['POST']}, action="add")
    d.connect('queueitem', '/users/:email_address/queue/:movie_id', QueueItemView(), conditions={'method':['DELETE']}, action="delete")
    d.connect('queueitem', '/users/:email_address/queue/:movie_id', QueueItemView(), conditions={'method':['GET']}, action="get")
    d.connect('main', '/', Root())
    return d
    
def main(argv):
    # Start the web server
    db_path = os.path.abspath(os.path.join(os.curdir, 'queues.db'))
    url = 'sqlite:///%s' % db_path
    
    framework.SAEnginePlugin(cherrypy.engine, url).subscribe()
    cherrypy.tools.db = framework.SATool()
    cherrypy.tree.mount(None, config={'/': {'tools.db.on': True, 'request.dispatch':setup_routes()}})
    cherrypy.engine.start()
    cherrypy.engine.block()

if __name__=="__main__":
    sys.exit(main(sys.argv))