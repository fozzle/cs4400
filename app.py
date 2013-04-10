from flask import (Flask, session, redirect, url_for, 
	request, render_template, flash)
import pymysql
import os
app = Flask(__name__)

conn = pymysql.connect(host='localhost', 
						user='cs4400_Group_29',
						db='cs4400_Group_29',
						passwd=os.environ['DBPASS'])

c = conn.cursor()

@app.route("/")
def home():
	if session.get('username'):
		return render_template('home.html')
	return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
    	sql = ("SELECT username FROM user WHERE username = '{u}' AND password = '{p}';".format(u=request.form['username'],
    																						p=request.form['password']))
    	result = c.execute(sql)

        if result:
            row = c.fetchone()
            flash('You were logged in', 'alert-success')
            session['username'] = row[0]
            session['role'] = get_role(row[0])
            return redirect(url_for('home'))
        else:
            flash('Incorrect login', 'alert-error')

    return render_template('login.html', error=error)

def get_role(username):
    admin = "SELECT username FROM Administrator WHERE username= '{u}'".format(u=username)
    employee = "SELECT username FROM GTCREmployee WHERE username= '{u}'".format(u=username)
    member = "SELECT username FROM member WHERE username= '{u}'".format(u=username)

    result = c.execute(member)
    if result:
        return 'member'
    result = c.execute(employee)
    if result:
        return 'emp'
    result = c.execute(admin)
    if result:
        return 'admin'

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('username', None)
    session.pop('role', None)
    flash('Logout Success', 'alert-success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if session.get('username'):
        return redirect(url_for('home'))
    if request.method == 'POST':
        if request.form['password'] != request.form['passwordconf']:
            flash('Passwords do not match!', 'alert-error')
            return render_template('register.html', error=error)

        sql = ("INSERT INTO user VALUES "
                "('{username}', '{password}')".format(username=request.form['username'],
                                                password=request.form['password']))

        if request.form['type'] == 'member':
            role = ("INSERT INTO member VALUES "
                        "('{username}', 'firstname', 'lastname', 'm', '123 sesame', NULL, NULL, NULL, NULL)"
                        .format(username=request.form['username']))

        elif request.form['type'] == 'emp':
            role = "INSERT INTO GTCREmployee VALUES ('{username}')".format(username=request.form['username'])
        

        try:
            result = c.execute(sql)
            result = c.execute(role)
            conn.commit()
        except pymysql.err.IntegrityError:
            flash('Username exists!', 'alert-error')
            return render_template('register.html', error=error)
        except:
            flash('Something happened!', 'alert-error')
            return render_template('register.html', error=error)


        flash('Registered', 'alert-success')
        return redirect(url_for('login'))
    return render_template('register.html', error=error)

if __name__ == "__main__":
	app.secret_key = 'sekret'
	app.run(debug=True)
