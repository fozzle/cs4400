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
        #Getting args
        
        pickdate = request.args.get('pickdate','')
        pickhour = request.args.get('pickhour','')
        pickmin = request.args.get('','')
        
        returndate = request.args.get('returndate','')
        returnhour = request.args.get('returnhour','')
        returnmin = request.args.get('returnmin','')

        #finding timedelta for est cost calcs
        delta_date = int(returndate[8:10])-int(pickdate[8:10])
        delta_hour = int(returnhour)-int(pickhour)
        
        location = request.args.get('location','')
        model = request.args.get('model','')
        types = request.args.get('types','')
        
        #Setting the sql for the table
        if types:
            sql = "SELECT VehicleSno,CarModel,Type,CarLocation,Color,HourlyRate,HourlyRate,HourlyRate,DailyRate,Seating_Capacity,Transmission_Type,BluetoothConnectivity,Auxiliary_Cable FROM car WHERE  CarLocation='{l}' and Type='{t}'".format(l = location, t = types)
            
            c.execute(sql)
            things = c.fetchall()
            sub ="SELECT VehicleSno,CarModel,Type,CarLocation,Color,HourlyRate,HourlyRate,HourlyRate,DailyRate,Seating_Capacity,Transmission_Type,BluetoothConnectivity,Auxiliary_Cable FROM car WHERE  Type='{t}' GROUP BY CarLocation".format(t = types)
            print sub
            
        else:
            sql = "SELECT VehicleSno,CarModel,Type,CarLocation,Color,HourlyRate,HourlyRate,HourlyRate,DailyRate,Seating_Capacity,Transmission_Type,BluetoothConnectivity,Auxiliary_Cable FROM car WHERE  CarLocation='{l}' and CarModel='{m}'".format(l = location, m = model)
            c.execute(sql)
            things = c.fetchall()
            sub = "SELECT VehicleSno,CarModel,Type,CarLocation,Color,HourlyRate,HourlyRate,HourlyRate,DailyRate,Seating_Capacity,Transmission_Type,BluetoothConnectivity,Auxiliary_Cable FROM car WHERE  CarModel='{m}' GROUP BY CarLocation".format(m = model)

        c.execute(sub)
        extra = c.fetchall()
        #sorting the tuples into a list so i can mess around with their innards
        final = []
        a = []
        b = []
        for item in things:
            a.append(list(item))        
        for item in extra:
            b.append(list(item))

        #Checking for duplicate entries in the sql based off their VehicleSno
        for x in range(len(a)):
            for y in range(len(b)):
                try:
                    if a[x][0] == b[y][0]:
                        b.pop(y)
                except:
                    pass

        #Getting the user's plan info so I can make an estimate of the cost
        user= session.get('username')
        sql = "SELECT DrivingPlan FROM member WHERE Username='{u}'".format(u = user)
        c.execute(sql)
        plan = c.fetchall()[0][0]
        print plan
        
        #Concatination and editing the final lists of vehicles                 
        final = a+b           
        for item in final:
            vsno = item[0] #i'm keeping the vsno around so that maybe we can use it as the value of the select button so it will make the insertion into the rental sql easier? maybe?
            item.pop(0)
            item.append('available') #adding two extra fields for the est cost and when it's available until
            item.append('estcost')
            item[5] = .9*item[5] #Frequent
            item[6] = .85*item[6] #Daily
            if plan == "Frequent Driving":
                item[13] = item[7]*delta_date+item[5]*delta_hour
            elif plan == "Daily Driving":
                item[13] = item[7]*delta_date+item[6]*delta_hour
            else:
                item[13] = item[7]*delta_date+item[4]*delta_hour
                                         
            for x in range(len(item)): #changing the boolean values to 'yes' and 'no'
                if item[x] == '\x01':
                    item[x] = 'Yes'
                elif item[x] == '\x00':
                    item[x] = 'No'
            item.append(vsno)
        
        # Get arguments like date and stuff to build your query from request.args.get('nameofarg', '')
        # The names of the arg are the same as in the rent form. 

        return render_template('availability.html', data = final)

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

