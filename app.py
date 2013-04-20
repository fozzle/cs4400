from flask import (Flask, session, redirect, url_for, 
	request, render_template, flash)
import pymysql
import os
from datetime import date, timedelta
app = Flask(__name__)

conn = pymysql.connect(host='localhost', 
						user='cs4400_Group_29',
						db='cs4400_Group_29',
						passwd=os.environ['DBPASS'])

c = conn.cursor()

#===============================================
# UTILITY
#===============================================

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

#===============================================
# GENERAL USER MGMT AND HOME
#===============================================

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

#===========================================
# MEMBER FUNCTIONS
#===========================================
@app.route('/plans', methods=['GET'])
def plans():
    if not session.get('username'):
        return redirect(url_for('login'))

    sql = "SELECT * FROM drivingplan"
    c.execute(sql)
    rows = c.fetchall()
    return render_template('plans.html', rows=rows)

@app.route('/personal_info', methods=['GET', 'POST'])
def personal_info():

    if request.method == 'POST':

        card_sql = ("INSERT INTO credit_card(CardNo, Name, CVV, ExpiryDate, BillingAdd) "
                    "VALUES ({cardno}, '{name}', {cvv}, '{exp_year}-{exp_mo}-01', '{billing}') ON DUPLICATE KEY UPDATE "
                    "Name='{name}', CVV={cvv}, ExpiryDate='{exp_year}-{exp_mo}-01', BillingAdd='{billing}'"
                    .format(cardno=request.form['cardno'],
                            name=request.form['name'],
                            cvv=request.form['cvv'],
                            exp_year=request.form['exp_year'],
                            exp_mo=request.form['exp_mo'],
                            billing=request.form['billingadd']))
        print card_sql

        user_sql = ("UPDATE member SET FirstName='{firstname}', LastName='{lastname}', MiddleInit='{middle}', " 
                    "Address='{addr}', PhoneNo={phone}, EmailAddress='{email}', CardNo={cardno}, DrivingPlan='{drivingplan}' " 
                    "WHERE username='{username}'".format(username=session['username'],
                                                        firstname=request.form['firstname'],
                                                        lastname=request.form['lastname'],
                                                        middle=request.form['middleinit'],
                                                        addr=request.form['address'],
                                                        phone=request.form['phone'],
                                                        email=request.form['email'],
                                                        cardno=request.form['cardno'],
                                                        drivingplan=request.form['plan']))

        try:
            c.execute(card_sql)
            c.execute(user_sql)
            conn.commit()
        except pymysql.err.IntegrityError:
            flash("IntegrityError!", 'alert-error')
        
        flash('Updated!', 'alert-success')

    user_sql = "SELECT * FROM member WHERE username='{username}'".format(username=session['username'])

    r = c.execute(user_sql)
    if not r:
        flash('You are not a member', 'alert-error')
        return redirect(url_for('home'))

    user_row = c.fetchone()

    # Get driving plans available.
    plans_sql = "SELECT Type FROM drivingplan"
    c.execute(plans_sql)
    plans = c.fetchall()

    # Get card info, if exists
    card = ('', '', '', '')
    if user_row[7]:
        card_sql = "SELECT Name, CVV, ExpiryDate, BillingAdd FROM credit_card WHERE CardNo={cardno}".format(cardno=user_row[7])
        r = c.execute(card_sql)
        card = c.fetchone()

    year = card[2].year
    month = card[2].month    
    return render_template('personal_info.html', user=user_row, plans=plans, card=card, year=year, month=month)

@app.route('/rent', methods=['GET','POST'])
def rent():
        if session['role'] != 'member':
            return redirect(url_for('home'))
            
        locations = "SELECT LocationName FROM location"
        m = "SELECT CarModel FROM car GROUP BY CarModel"
        t = "SELECT Type FROM car GROUP BY CarModel"

        c.execute(locations)
        locations = c.fetchall()

        c.execute(m)
        models = c.fetchall()

        c.execute(t)
        types = c.fetchall()

        dates = [x.strftime("%Y-%m-%d") for x in daterange(date.today(), date.today() + timedelta(365))]
                        
        return render_template('rent.html', locations = locations, models = models, types = types, dates=dates)

@app.route('/availability', methods=['GET','POST'])
def availability():

        if session['role'] != 'member':
            return redirect(url_for('home'))

        # If this came from the rent form... (it should have)
        if request.args.get('pickdate', '') and request.args.get('returndate', ''):
                    pickdate = request.args.get('pickdate', '')
                    returndate = request.args.get('returndate', '')

                    delta = date(int(returndate[0:4]), int(returndate[5:7]), int(returndate[8:10])) - date(int(pickdate[0:4]), int(pickdate[5:7]), int(pickdate[8:10]))

                    #making sure the date is less than two
                    if delta.days > 2:
                        flash("You cannot rent a car for more than two days")
                        return redirect(url_for('rent'))

        # Get arguments like date and stuff to build your query from request.args.get('nameofarg', '')
        # The names of the arg are the same as in the rent form. 

        return render_template('availability.html')

def rental_info():
        pass


#===========================================
# ADMIN FUNCTIONS
#===========================================

@app.route('/admin/reports', methods=['GET'])
def admin_reports():
    if not session.get('role') == 'admin':
        return redirect(url_for('home'))

    sql = ("SELECT car.VehicleSno, Type, CarModel, SUM(EstimatedCost) , SUM(LateFees) FROM  `reservation` JOIN `car` "
            "WHERE PickUpDateTime > DATE_SUB(NOW() ,INTERVAL 3 MONTH) AND PickUpDateTime < NOW() "
            "GROUP BY VehicleSno ORDER BY Type")
    c.execute(sql)
    data = c.fetchall()

    return render_template('admin_report.html', data=data)

#===========================================
# EMPLOYEE FUNCTIONS
#===========================================



if __name__ == "__main__":
	app.secret_key = 'sekret'
	app.run(debug=True)

