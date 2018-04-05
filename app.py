
from flask import Flask ,render_template,request,redirect,url_for,session,flash
from pymongo import MongoClient
from datetime import datetime
import flask_login


MONGODB_URI = 'mongodb://<dbusername>:<dbpassword>@ds251807.mlab.com:51807/wordflow'
client = MongoClient(MONGODB_URI)
db = client.get_database("wordflow")
appdata = db.word_data

app = Flask(__name__)
app.secret_key = 'XXXX'

# login manager
login_manager = flask_login.LoginManager()

login_manager.init_app(app)


class User(flask_login.UserMixin):
    id=appdata['email']
    user=appdata['name']

@login_manager.user_loader
def user_loader(email):
    if  not appdata.find_one({'email':email}):
        return

    user=User()
    user.id=email
    dbdoc=appdata.find_one({'email':email})
    user.is_authenticate=(request.form.get('password'))==dbdoc['password']

    return user

@app.route('/')
def welcome():
    return render_template('html.html')


@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='GET':
        if session.get('user_id'):
            return redirect(url_for('protected'))
        else:
            return render_template('login.html')


    else:
        email=request.form.get('email')
        if appdata.find_one({'email':email}):
            dbdoc=appdata.find_one({'email':email})
            if dbdoc['password']==request.form.get('password'):
                user=User()
                user.id=email

                flask_login.login_user(user)
                session['user']=flask_login.current_user.id
                return redirect(url_for('protected'))

        return 'email not registered. Please signup first'


@app.route('/protected')
@flask_login.login_required
def protected():
    name=appdata.find_one({'email':flask_login.current_user.id})
    username=name['name']
    return render_template('home.html',data=username)

@app.route('/delete_account',methods=['GET'])
@flask_login.login_required
def delete_account():
    if request.method=='GET':
        appdata.delete_one({'email':flask_login.current_user.id})
        session.clear()
        return redirect(url_for("welcome"))

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect(url_for('welcome'))

@app.route('/write_article',methods=['GET','POST'])
@flask_login.login_required
def write_article():
    if request.method=='GET':
        return render_template('home.html')
    elif request.method=='POST':
        now=datetime.now()
        day=now.strftime("%d-%m-%Y")
        title=request.form.get('head')
        art=request.form.get('body')
        article=[title,art,day]
        appdata.update_one({'email':flask_login.current_user.id},{ '$push' :{ 'article':article}})
        return render_template('home.html')


@app.route('/viewmy',methods=['GET'])
@flask_login.login_required
def viewmy():
    if request.method=='GET':
        name=appdata.find_one({'email':flask_login.current_user.id})
        username=name['name']

        myarc=list(name['article'])

    return render_template('articles.html',name=username,data=myarc)


@app.route('/allarticles',methods=['GET'])
@flask_login.login_required
def allarticles():
    if request.method=='GET':
        name=appdata.find_one({'email':flask_login.current_user.id})
        username=name['name']
        d=name['article']
        allarcs=appdata.distinct('article')
        for i in d:
            if i in allarcs:
                allarcs.remove(i)
            else:
                pass

    return render_template('articles.html',data=allarcs,name=username)


@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized.Please log in first'


@app.route('/signup',methods=['GET','POST'])
def signup():
    if request.method=='GET':
        return render_template('signup.html')

    elif request.method=='POST':
        if appdata.find_one({"email":request.form.get('email')}):
            flash("email already exist")
            return render_template('signup.html')

        else:
            userdata={}
            userdata["name"]=request.form.get("username")
            userdata["email"]=request.form.get("email")
            userdata["password"]=request.form.get("password")
            userdata["article"]=[]
            appdata.insert_one(userdata)
            user=User()
            user.id=request.form.get("email")

            flask_login.login_user(user)
            session['user']=flask_login.current_user.id
            return redirect(url_for('protected'))




if __name__ == "__main__":
    app.run(debug=True)
