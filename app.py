from flask import Flask, render_template, redirect, url_for, request, session, flash
from Player import Player
from Team import Team
from flask_sqlalchemy import SQLAlchemy
import json
from flask_migrate import Migrate

app = Flask(__name__)
app.secret_key = "secret_user"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

migrate = Migrate(app, db)

class users(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))
    team = db.Column(db.String(5000))
    editedPlayer = db.Column(db.String(5000))

    def __init__(self, username, password, team, editedPlayer):
        self.username = username
        self.password = password
        self.team = json.dumps(team)
        self.editedPlayer = json.dumps(editedPlayer)

@app.route("/team", methods=["POST", "GET"])
def team(team=None, editedPlayer=None):
    if "user" in session:
        usr = users.query.filter_by(username=session["user"]).first()
        if request.method == "POST":
            if "newPlayerNumber" in request.form:
                usr.editedPlayer = json.dumps(None)

                number = request.form["newPlayerNumber"]
                fname = request.form["newPlayerFirstName"]
                lname = request.form["newPlayerLastName"]
                
                newPlayer = Player(int(number), fname, lname)

                players = json.loads(usr.team)

                team = Team()
                if players == None:
                    team.Players = dict()
                else:
                    team.Players = players

                team.AddPlayer(newPlayer)

                # Sort team by number
                team.Players = dict(sorted(team.Players.items(), key=lambda x: int(x[0])))

                usr.team = json.dumps(team.Players)
                db.session.commit()

                return redirect(url_for("team", team=team.Players, editedPlayer=None))

            elif "editPlayerForm" in request.form:
                number = request.form["editPlayerForm"]
                players = json.loads(usr.team)

                team = Team()
                team.Players = players

                editedPlayer = team.RemovePlayer(number)
                usr.editedPlayer = json.dumps(editedPlayer)

                usr.team = json.dumps(team.Players)
                db.session.commit()

                return redirect(url_for("team", team=team.Players, editedPlayer=json.loads(usr.editedPlayer)))

            elif "deletePlayerForm" in request.form:
                number = request.form["deletePlayerForm"]

                players = json.loads(usr.team)

                team = Team()
                team.Players = players

                team.RemovePlayer(number)

                usr.team = json.dumps(team.Players)
                db.session.commit()

                return redirect(url_for("team", team=players))
        else:
            return render_template('team.html', team=json.loads(usr.team), editedPlayer=json.loads(usr.editedPlayer))
    else:
        return redirect(url_for("login"))

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "GET":
        return render_template('login.html')
    else:
        if "username" in request.form and "password" in request.form:
            username = request.form["username"]
            password = request.form["password"]
            #To-Do: validate user
            found_user = users.query.filter_by(username=username).first()
            if found_user:
                if (found_user.password == password):
                    session["user"] = username
                    return redirect(url_for("team", team=found_user.team))
            # If we make it here, username or password was incorrect
            flash("Username or password incorrect")
            return render_template('login.html')
        else:
            return redirect(url_for("createAccount"))
        

@app.route("/create-account", methods=["POST", "GET"])
def createAccount(username=None):
    if request.method == "GET":
        return render_template('createAccount.html')
    else:
        username = request.form["username"]
        password = request.form["password"]
        cfmPassword = request.form["confirmPassword"]
        if password != cfmPassword:
            flash("Passwords did not match", "error")
            return redirect(url_for("createAccount", username=username))
        #To-Do: check if user is already in database
        found_user = users.query.filter_by(username=username).first()
        if found_user:
            flash("Username is taken")
            return redirect(url_for("createAccount", username=username))
        else:
            session["user"] = username
            usr = users(username, password, None, None)
            db.session.add(usr)
            db.session.commit()

            return redirect(url_for("team"))

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/stat-track")
def statTrack():
    if "user" in session:
        return render_template('stat-track.html')
    else:
        return redirect(url_for("login"))

@app.route("/logout")
def logout():
    # users.query.delete()
    # db.session.commit()
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    with app.app_context():
        # users.query.delete()
        # db.session.commit()
        db.create_all()
    app.run(host='0.0.0.0', debug=True)
