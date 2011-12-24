from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash

from werkzeug.contrib.cache import SimpleCache

cache = SimpleCache()

app = Flask(__name__)
app.config.from_object(__name__)

from flask.views import MethodView

from cannula.conf import api

class UserAPI(MethodView):

    def get(self):
        if session.get('logged_in'):
            user = cache.get('user:%s' % session['user'])
            if user is None:
                user = api.users.get(session['user'])
                cache.set('user:%s' % session['user'], user)
        ctx = {'user': user}
        return render_template('flask/index.html', **ctx)
        

    def post(self):
        group = api.groups.create('test')

class Login(MethodView):
    
    def get(self):
        return render_template('flask/login.html')
    
    def post(self):
        _next = request.args.get('next', '/')
        session['logged_in'] = True
        session['user'] = 'rmyers'
        flash('You were logged in')
        return redirect(_next)
        #return render_template('login.html', error=error)
        
app.add_url_rule('/users/', view_func=UserAPI.as_view('users'))
app.add_url_rule('/login/', view_func=Login.as_view('login'))

if __name__ == '__main__':
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
    app.run(debug=True)