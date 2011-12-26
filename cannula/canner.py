from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash

from werkzeug.contrib.cache import SimpleCache

cache = SimpleCache()

app = Flask(__name__)
app.config.from_object(__name__)

from flask.views import MethodView

from cannula.conf import api

class CannulaView(MethodView):
    
    def default_context(self, extra_ctx=None):
        ctx = {'user': None}
        if session.get('logged_in'):
            user = api.users.get(session['user'])
            ctx['user'] = user
        # TODO: other stuff here too?
        if extra_ctx is not None:
            ctx = ctx.update(extra_ctx)
        return ctx

class Index(CannulaView):

    def get(self):
        ctx = self.default_context()
        return render_template('flask/index.html', **ctx)

class Login(CannulaView):
    
    def get(self):
        ctx = self.default_context()
        return render_template('flask/login.html', **ctx)
    
    def post(self):
        _next = request.args.get('next', '/')
        user = request.form.get('username')
        password = request.form.get('password')
        if not (user or password):
            abort(400)
        
        user = api.users.get(user)
        if user.check_password(password):
            session['logged_in'] = True
            session['user'] = user.name
            flash('You were logged in')
            return redirect(_next)
        
        ctx = self.default_context({'error': "Invalid user or password"})
        return render_template('flask/login.html', **ctx)

class Logout(CannulaView):
    
    def get(self):
        session['logged_in'] = False
        session['user'] = ''
        return redirect('/')
        
app.add_url_rule('/', view_func=Index.as_view('index'))
app.add_url_rule('/login/', view_func=Login.as_view('login'))
app.add_url_rule('/logout/', view_func=Logout.as_view('logout'))

if __name__ == '__main__':
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
    app.run(debug=True)