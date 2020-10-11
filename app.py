from flask import Flask #flask
from flask import render_template, request, redirect, make_response, Response, flash ##flask functions
import sqlite3 as sql ##for database
import smtplib ##for sending verification mail
from cryptohash import sha1  ##for hashing the password


app = Flask(__name__)

@app.route("/")
def root_dir():
    return render_template("register.html")


@app.route("/register")
def register():
    return render_template('register.html')

@app.route("/register", methods=['GET', 'POST'])
def register_db():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password_unhashed = request.form['password']
        password = sha1(password_unhashed) ##password to sha1 
        con = sql.connect("database.db")
        cur = con.cursor()
        try:
            cur.execute("INSERT INTO users (username,password,name,verified) VALUES (?,?,?,?)", (username,password,name,0))
            con.commit()
            con.close()
        except sql.IntegrityError:
            return render_template("/registered.html")
        vlink = "http://127.0.0.1:5000/verify/mail=" + username + "&_hash=" + sha1(username)
        sendmail(username, vlink)
        return render_template("reg_success.html")
        

@app.route("/login", methods=['GET', 'POST'])
def login_check():
    if request.method == 'POST':
        username = request.form['username']
        password_real = request.form['password']
        password_hashed = sha1(password_real)
        conn = sql.connect("database.db")
        creds = conn.execute("SELECT * FROM users WHERE username = '" + username + "'").fetchall()
        conn.close()
        try:
            if creds[0][3] == 0:
                return render_template("notverified.html")
            else:
                pass
            if password_hashed == creds[0][1]:
                resp = make_response(render_template("welcome.html"))
                resp.set_cookie('dont_try', str(sha1(username)))
                resp.set_cookie('email', username)
                return resp
            else:
                return render_template("loginfailed.html")
        except IndexError:
            return "you are not registered"


@app.route("/verify/mail=<mail>&_hash=<_hash>")
def verify_mai(mail, _hash):
    print(mail)
    conn = sql.connect("database.db")
    creds = conn.execute("SELECT * FROM users WHERE username = '" + mail + "'").fetchall()
    db_mail = creds[0][0]
    name = creds[0][2]
    verified_status = creds[0][3]
    if verified_status == 0:
        if (sha1(mail) == _hash and mail == db_mail):
            conn = sql.connect("database.db")
            conn.execute("UPDATE users SET verified=1 WHERE username='" + mail + "'")
            conn.commit()
            conn.close()
            resp = make_response(render_template("welcome.html", name=name))
            resp.set_cookie('dont_try', str(sha1(mail)))
            resp.set_cookie('email', mail)
            return resp
        else:
            return "Verification link broken"
    else:
        return render_template("/registered.html")


    
@app.route("/welcome")
def welcome_user():
    _hash = request.cookies.get("dont_try")
    username = request.cookies.get("email")
    cookie_check(username, _hash)
    conn = sql.connect("database.db")
    creds = conn.execute("SELECT name FROM users WHERE username = '" + username + "'").fetchall()
    name = creds[0][0]
    conn.close()
    return render_template("welcome.html", name=name) ##will contain two options -- findpool; postpool




@app.route("/postpool")
def postpool():
    _hash = request.cookies.get("dont_try")
    username = request.cookies.get("email")
    cookie_check(username, _hash)
    return render_template("postpool.html")


@app.route("/postpool", methods=['GET','POST'])
def postpoolreq():
    if request.method == 'POST':
        _hash = request.cookies.get("dont_try")
        username = request.cookies.get("email")
        cookie_check(username, _hash)

        ##fetch the name of the current user
        conn = sql.connect("database.db")
        fetch_name = conn.execute("SELECT name from users where username='" + username + "'").fetchall()
        name = fetch_name[0][0]
        #######################################

        start_location = request.form['start-location'] ##start location
        dest_location = request.form['dest-location'] ##destination location
        contact = request.form['contact'] ##phone number
        vehicle = request.form['vehicle-type'] ##vehicle type
        conn = sql.connect("database.db")
        cur = conn.cursor()
        cur.execute("INSERT INTO posts (name,start_location,dest_location,contact,vehicle) VALUES (?,?,?,?,?)", (name,start_location,dest_location,contact,vehicle))
        conn.commit()
        conn.close()
        return render_template("/postsuccess.html")


@app.route("/findpools")
def findpools():
    _hash = request.cookies.get("dont_try")
    username = request.cookies.get("email")
    cookie_check(username, _hash)
    conn = sql.connect("database.db")
    all_data = conn.execute("SELECT * FROM posts").fetchall()
    html_code = ""
    for i in range(0, len(all_data)):
        html_code += "<tr>"
        for x in range(0, 5):
            html_code += "<td>" + str(all_data[i][x]) + "</td>"
        html_code += "</tr>"
    print(html_code)
    return render_template("/viewpools.html", html_code=html_code)

@app.route("/findpool")
def findpool():
    _hash = request.cookies.get("dont_try")
    username = request.cookies.get("email")
    cookie_check(username, _hash)
    conn = sql.connect("database.db")
    all_data = conn.execute("SELECT * FROM posts").fetchall()
    html_code = ""
    for i in range(0, len(all_data)):
        html_code += "<tr>"
        for x in range(0, 5):
            html_code += "<td>" + str(all_data[i][x]) + "</td>"
        html_code += "</tr>"
    print(html_code)
    return render_template("/viewpools.html", html_code=html_code)

@app.route("/teamvortex")
def team():
    return render_template("/teamvortex.html")
    


def cookie_check(username, hash):
    conn = sql.connect("database.db")
    creds = conn.execute("SELECT * FROM users WHERE username = '" + username + "'").fetchall()
    conn.close()
    if creds == []:
        return render_template("/notregistered.html") 
    else:
        pass 
    if hash != sha1(creds[0][1]): ##uername/mail to sha1
        logout()
    else:
        pass
        
@app.route("/logout")
def logout():
    resp = make_response(render_template("/register.html"))
    resp.set_cookie('dont_try', expires=0)
    resp.set_cookie('email', expires=0)
    return resp



def sendmail(username, vlink):
    server = smtplib.SMTP('smtp.gmail.com', 587) #change it according to your smtp details
    server.ehlo()
    server.starttls()
    uid = "XXXXXXX@gmail.com" #your smtp email
    passwd = "PASSSOWRD" #your smtp password
    server.login(uid, passwd)
    msg = ("Verify your mail \n" + str(vlink))
    message = 'Subject: {}\n\n{}'.format("Pool-in registration", msg)
    server.sendmail('randomxes05@gmail.com', username, message) # smtpmail, your real email
    server.close()

if __name__ == "__main__":
    app.run()