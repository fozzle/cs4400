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
        	flash('You were logged in')
        	session['username'] = c.fetchone()[0]
        	return redirect(url_for('home'))
        else:
        	flash('Incorrect login')

    return render_template('login.html', error=error)

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('username', None)
    flash('Login Success')
    return redirect(url_for('login'))

if __name__ == "__main__":
	app.secret_key = 'sekret'
	app.run(debug=True)

