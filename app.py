from functools import wraps
from flask import Flask, render_template, jsonify
from flask import request, session, redirect, url_for, flash
from utils.crm_api import login_action, is_session_active, fill_crm_info
from utils.forms import LoginForm, UploadFileForm
from flask_pymongo import PyMongo
import pandas as pd
import time
import threading

app = Flask(__name__)

app.config['SECRET_KEY'] = 'W.pPiKp47Z0WPd#'
app.config["MONGO_URI"] = "mongodb://localhost:27017/SRMtest"
mongo = PyMongo(app)
mongo.db.test1.create_index([("serie", 1)], unique=True)


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "login_res" in session:
            login_res = session["login_res"]
            if is_session_active(login_res[1]["JESSIONID"], login_res[1]["u-token"], login_res[1]["sna_cookie"]):
                return f(*args, **kwargs)
            else:
                flash("Session expired. Please log in again.")
                return redirect(url_for("login"))
        else:
            flash("Please log in.")
            return redirect(url_for("login"))

    return wrap


@app.route("/")
def index():
    if "login_res" in session:
        login_res = session["login_res"]
        if is_session_active(login_res[1]["JESSIONID"], login_res[1]["u-token"], login_res[1]["sna_cookie"]):
            return redirect(url_for("home"))
        else:
            flash("Session expired. Please log in again.")
            return redirect(url_for("login"))
    else:
        flash("Please log in.")
        return redirect(url_for("login"))



@app.route("/home")
@login_required
def home():
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        login_res = login_action(form.username.data, form.password.data)
        if login_res[0] == -1:
            flash("Error: " + str(login_res[1]))
            return redirect(url_for("login"))
        elif login_res[0]:
            session["login_res"] = login_res
            return redirect(url_for("home"))
        else:
            flash(login_res[1])
            return redirect(url_for("login"))
    return render_template("login.html", form=form)


@app.route("/upload")
@login_required
def upload():
    form = UploadFileForm()
    return render_template("fileupload.html", form=form)


@app.route('/validate', methods=['POST'])
@login_required
def validate():
    file = request.files['file']
    if not file:
        return '<p class="text-tertiary-500">Error: Archivo no fue proporcionado<p/>', 200
    if file.filename.endswith('.csv'):
        df = pd.read_csv(file)
        entries = len(df)
        duplicates = len(df[df[df.columns[1]].duplicated()])
        base_mislen = df.loc[~(df[df.columns[0]].astype(str).str.len() == 10), df.columns[0]].tolist()
        serial_mislen = df.loc[~(df[df.columns[1]].astype(str).str.len() == 8), df.columns[1]].tolist()
        html_table = df.head(10).to_html()
        return render_template("uptable_check.html",
                               table=html_table, entries=entries, duplicates=duplicates,
                               base_mislen=base_mislen, serial_mislen=serial_mislen)
    else:
        return '<p class="text-tertiary-500">Error: Tipo de archivo incorrecto<p/>', 200


@app.route("/upload_file", methods=["POST"])
@login_required
def upload_file():
    file = request.files['file']
    if not file:
        return '<p>Error: Archivo no fue proporcionado<p/>', 400
    if file.filename.endswith('.csv'):
        df = pd.read_csv(file)
        df.columns[0] = 'base'
        df.columns[1] = 'serie'
        entries = len(df)
        duplicates = len(df[df[df.columns[1]].duplicated()])
        df = df.drop_duplicates(subset=df.columns[1], keep='first')
        base_mislen = bool(len(df.loc[~(df[df.columns[0]].astype(str).str.len() == 10), df.columns[0]]))
        serial_mislen = bool(len(df.loc[~(df[df.columns[1]].astype(str).str.len() == 8), df.columns[1]]))
        if duplicates or base_mislen or serial_mislen:
            return jsonify({"status": "error", "message": "Error: Archivo contiene errores"})
        else:
            fill_crm_info(df, session["login_res"][1])
            mongo.db.test1.insert_many(df.to_dict('records'))
            return f'<p>{entries} valores fueron subidas exitosamente<p/>', 200
    else:
        return jsonify({'status': 'error', 'message': 'Tipo de archivo incorrecto'}), 400


def tracking_function():
    while True:
        # Your tracking logic here
        print("Tracking...")
        if "login_res" in session:
            print(f"{session['login_res']}")
        time.sleep(10)  # Run every 60 seconds


if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    # tracking_thread = threading.Thread(target=tracking_function)
    # tracking_thread.daemon = True
    # tracking_thread.start()

    app.run(debug=True)
