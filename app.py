from flask import Flask , render_template , request , session , redirect , url_for
from werkzeug.security import generate_password_hash , check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "no-body-knows"

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:9566@localhost/user'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#initailzing database 
db = SQLAlchemy(app)

#creating a database model here for example a row 
class User(db.Model):
  __tablename__ = 'user'
  id = db.Column(db.Integer , primary_key = True , autoincrement = True)
  username = db.Column(db.String(120), unique = True, nullable = False)
  name = db.Column(db.String(50) , nullable = False)
  email = db.Column(db.String(120), unique = True , nullable = False)
  password = db.Column(db.String(255) , nullable = False)
  tasks = db.relationship("Task", back_populates="user", lazy=True)

  def __repr__(self):
    return f"<user {self.name}"
  
  def set_password(self , password):
    self.password = generate_password_hash(password)

  def check_password(self, password):
    return check_password_hash(self.password , password)

#creating the task model now
from datetime import datetime

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    desc = db.Column(db.String(500))
    status = db.Column(db.String(20), default="pending")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # New column to store the timestamp

    user = db.relationship("User", back_populates="tasks")


@app.route("/")
def welcome():
  return render_template("welcome.html")

#register
@app.route("/register" , methods = ["GET","POST"])
def register():
  if request.method == "POST":
    username = request.form['username']
    name = request.form['name']
    email = request.form['mail']
    password = request.form['pswd']
    re_password = request.form['r-pswd']

    if password != re_password:
      return redirect(url_for('register' , error = "Entered Passwords does not match"))
    else:
      user = User.query.filter_by(username = username).first()
      if user:
        return redirect(url_for("login" , error = "User already exists..!!!"))
      new_user = User(username=username , name=name, email=email)
      new_user.set_password(password)
      db.session.add(new_user)
      db.session.commit()
      print("User created successfully")
      return redirect(url_for("login"))
    
  return render_template("register.html" , username = session.get('username'))

#login
#login
@app.route("/login", methods=["GET", "POST"])
def login():
    #collect the info from the login form
    if request.method == "POST":
        username = request.form['username']
        password = request.form['pswd']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['username'] = username
            session["user_id"] = user.id  # Corrected this line to set user_id in the session
            return redirect(url_for("dashboard"))
        else:
            return render_template("register.html")

    return render_template("login.html")


#dashboard
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))

    user = User.query.filter_by(username=session["username"]).first()
    tasks = Task.query.filter_by(user_id=user.id).all()
    return render_template("dashboard.html", username=user.name, tasks=tasks)

@app.route("/tasks")
def tasks():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    tasks = Task.query.filter_by(user_id=user.id).all()
    return render_template("tasks.html", tasks=tasks)

@app.route("/add_task", methods=["GET", "POST"])
def add_task():
    if "username" not in session:  # Check for username in session
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        status = request.form.get("status", "Pending")

        # Retrieve the user object from the database using username
        user = User.query.filter_by(username=session["username"]).first() 
        if user: 
            new_task = Task(name=name, desc=description, status=status, user_id=user.id)
            db.session.add(new_task)
            db.session.commit()
            return redirect(url_for("tasks"))
        else:
            # Handle the case where the user is not found (unlikely but possible)
            return "User not found in session.", 404

    return render_template("add_tasks.html")


@app.route("/update_task/<int:task_id>", methods=["GET", "POST"])
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    if request.method == "POST":
        task.status = request.form["status"]
        db.session.commit()
        return redirect(url_for("tasks"))
    
    return render_template("update_tasks.html", task=task)

@app.route("/delete_task/<int:task_id>")
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("tasks"))

if __name__ == '__main__':
  with app.app_context():
    db.create_all()
  app.run(debug=True)