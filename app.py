from flask import (Flask, session, redirect, url_for, 
	request, render_template, flash, Response)
import pymysql
import os
import json
from datetime import date, timedelta, datetime
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

        for k, v in request.form.iteritems():
            if not v:
                flash('Please fill out everything completely!')
                return redirect(url_for('personal_info'))


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

    if card[2]:     
        year = card[2].year
        month = card[2].month
    else:
        year = ''
        month = ''

    return render_template('personal_info.html', user=user_row, plans=plans, card=card, year=year, month=month)

@app.route('/rent', methods=['GET','POST'])
def rent():
        if session['role'] != 'member':
            return redirect(url_for('home'))
            
        locations = "SELECT LocationName FROM location"
        m = "SELECT Distinct CarModel FROM car GROUP BY CarModel"
        t = "SELECT Distinct Type FROM car GROUP BY Type"

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

        #Selecting what you want           
        if request.method == 'POST':

            vsn = request.form['car']
            pickdatetime = request.form['pickdatetime']
            returndatetime = request.form['returndatetime']
            sql = """INSERT INTO reservation(Username, PickUpDateTime, ReturnDateTime, ReturnStatus, EstimatedCost, ReservationLocation, VehicleSno)
                    VALUES ('{user}', '{pickup}', '{returnd}', 'out', {cost}, '{location}', {vsn})""".format(user=session.get('username'), pickup=pickdatetime, returnd=returndatetime, 
                                cost=request.form[vsn+'cost'], location=request.form[vsn+'location'], vsn=vsn)
            
            c.execute(sql)
            conn.commit()

            flash("You have rented a car!")

            return redirect(url_for('home'))

        
                    
        #Getting args
        
        pickdate = request.args.get('pickdate','')
        pickhour = request.args.get('pickhour','')
        pickmin = request.args.get('pickmin','')
        pickdatetime = datetime(int(pickdate[0:4]), int(pickdate[5:7]), int(pickdate[8:10]), int(pickhour), int(pickmin))
        
        returndate = request.args.get('returndate','')
        returnhour = request.args.get('returnhour','')
        returnmin = request.args.get('returnmin','')
        returndatetime = datetime(int(returndate[0:4]), int(returndate[5:7]), int(returndate[8:10]), int(returnhour), int(returnmin))

        location = request.args.get('location','')
        model = request.args.get('model','')
        car_type = request.args.get('types','')

        delta = returndatetime - pickdatetime
        
        #making sure the date is less than two
        if delta.days > 2:
            flash("You cannot rent a car for more than two days")
            return redirect(url_for('rent'))
        
        #Setting the sql for the table
        if car_type:
            sql = "SELECT VehicleSno,CarModel,Type,CarLocation,Color,HourlyRate,DailyRate,Seating_Capacity,Transmission_Type,BluetoothConnectivity,Auxiliary_Cable FROM car WHERE  CarLocation='{l}' AND Type='{t}'".format(l = location, t = car_type)
            sql += " UNION ALL SELECT * FROM (SELECT VehicleSno,CarModel,Type,CarLocation,Color,HourlyRate,DailyRate,Seating_Capacity,Transmission_Type,BluetoothConnectivity,Auxiliary_Cable FROM car WHERE  Type='{t}' AND CarLocation != '{l}' ORDER BY CarLocation) extra".format(l=location, t = car_type)
            
            
        elif model:
            sql = "SELECT * FROM (SELECT VehicleSno,CarModel,Type,CarLocation,Color,HourlyRate,DailyRate,Seating_Capacity,Transmission_Type,BluetoothConnectivity,Auxiliary_Cable FROM car WHERE  CarLocation='{l}' and CarModel='{m}') desired_location".format(l = location, m = model)
            sql += " UNION ALL SELECT * FROM (SELECT VehicleSno,CarModel,Type,CarLocation,Color,HourlyRate,DailyRate,Seating_Capacity,Transmission_Type,BluetoothConnectivity,Auxiliary_Cable FROM car WHERE  CarModel='{m}' AND CarLocation != '{l}' ORDER BY CarLocation) extra".format(l=location, m = model)
            
        else:
            sql = "SELECT * FROM (SELECT VehicleSno,CarModel,Type,CarLocation,Color,HourlyRate,DailyRate,Seating_Capacity,Transmission_Type,BluetoothConnectivity,Auxiliary_Cable FROM car WHERE  CarLocation='{l}') desired_location ".format(l=location)
            sql += " UNION ALL SELECT * FROM (SELECT VehicleSno,CarModel,Type,CarLocation,Color,HourlyRate,DailyRate,Seating_Capacity,Transmission_Type,BluetoothConnectivity,Auxiliary_Cable FROM car WHERE  CarLocation != '{l}' ORDER BY CarLocation) extra".format(l=location)

        c.execute(sql)
        cars = c.fetchall()
        dic = {}
        vsnos = []
        for item in cars:
            vsnos.append(item[0])
            dic[item[0]] = "N/A"

        
        sql = "SELECT Distinct VehicleSno,PickUpDateTime FROM reservation where PickUpDateTime > now()"
        c.execute(sql)
        avail = c.fetchall()

        for x in vsnos:
            for y in avail:
                if str(x) == str(y[0]):
                    dic[x] = y[1]
                else:
                    if x in dic == False:
                        dic[x] = 'N/A'


        discount = None
        #Getting the user's plan info so I can make an estimate of the cost
        user= session.get('username')
        role = session.get('role')
        sql = "SELECT Discount FROM drivingplan JOIN member ON member.DrivingPlan = drivingplan.Type WHERE Username='{u}'".format(u = user)

        c.execute(sql)
        try:
            discount = c.fetchone()[0]
        except:
            if role != 'emp':
                flash("You need to set up a plan!")
                return(redirect(url_for('home')))
            else:
                flash("Searching for available reservations")

        if discount:
            discount = (100.0 - discount)/100.0
        else:
            discount = 1
        print vsnos
        print dic
        
        return render_template('availability.html', location=location,
                                pickdatetime=pickdatetime.strftime('%Y-%m-%d %H:%M:%S'), 
                                returndatetime=returndatetime.strftime('%Y-%m-%d %H:%M:%S'), 
                                cars = cars, discount=discount, hours=delta.seconds/3600, days=delta.days,
                               dic = dic)

@app.route('/rental_info', methods=['GET','POST'])
def rental_info():
    if not session.get('role') == 'member':
        return redirect(url_for('home'))

    dates = [x.strftime("%Y-%m-%d") for x in daterange(date.today(), date.today() + timedelta(365))]
    if request.method == 'POST':

        if not request.form.get('extend'):
            flash('You must select a reservation to modify')
            return redirect(url_for('rental_info'))

        extenddate = request.form['extenddate']
        extendhour = request.form['extendhour']
        extendmin = request.form['extendmin']
        resid = request.form['extend']

        extenddatetime = datetime(int(extenddate[0:4]), int(extenddate[5:7]), int(extenddate[8:10]), int(extendhour), int(extendmin))
        
        sql = """SELECT ReturnDateTime, VehicleSno FROM reservation WHERE ResID={resid}""".format(resid=resid)

        c.execute(sql)
        curr_res = c.fetchone()
        if curr_res[0] > extenddatetime:
            flash('To extend you must choose a time past your current return time', 'alert-error')
            return redirect(url_for('rental_info'))

        vsn = curr_res[1]

        sql = """SELECT PickUpDateTime FROM reservation 
                WHERE VehicleSno={vsn} AND PickUpDateTime < '{extend}' 
                AND PickUpDateTime > '{orig_return}'""".format(vsn=vsn, 
                                                                extend=extenddatetime.strftime('%Y-%m-%d %H:%M:%S'),
                                                                orig_return=curr_res[0].strftime('%Y-%m-%d %H:%M:%S'))

        c.execute(sql)
        collision = c.fetchall()
        if collision:
            flash('Someone else has already reserved that car at {date}'.format(date=collision[0][0]), 'alert-error')
            return redirect(url_for('rental_info'))


        sql = """INSERT INTO reservation_extended_time 
                VALUES ({resid}, '{extend}')""".format(resid=resid, extend=extenddatetime.strftime('%Y-%m-%d %H:%M:%S'))
        c.execute(sql)
        conn.commit()

        flash('Reservation successfully extended!', 'alert-success')
        return redirect(url_for('rental_info'))



    user= session.get('username')
    sql = """SELECT PickUpDateTime,ReturnDateTime,CarModel,ReservationLocation,EstimatedCost, ReturnStatus, Extended_Time 
            FROM reservation r1 NATURAL JOIN car LEFT JOIN reservation_extended_time r2 ON r2.ResID = r1.ResID 
            WHERE Username='{u}'""".format(u = user)

    c.execute(sql)
    all_res = c.fetchall()
    
    sql = """SELECT r1.ResID, PickUpDateTime, ReturnDateTime, CarModel, ReservationLocation, EstimatedCost, ReturnStatus, Extended_Time 
            FROM reservation r1 NATURAL JOIN car LEFT JOIN reservation_extended_time r2 ON r2.ResID = r1.ResID 
            WHERE Username='{u}' AND PickUpDateTime < NOW() AND ReturnDateTime > NOW()""".format(u = user)

    print sql
    c.execute(sql)
    current = c.fetchall()

    return render_template('rental_info.html', current=current, all_res=all_res, dates=dates)


#===========================================
# ADMIN FUNCTIONS
#===========================================

@app.route('/admin/reports', methods=['GET'])
def admin_reports():
    if not session.get('role') == 'admin':
        return redirect(url_for('home'))

    sql = """SELECT reservation.VehicleSno, Type, CarModel, SUM(EstimatedCost) , SUM(LateFees) FROM  `reservation` JOIN `car` ON reservation.VehicleSno = car.VehicleSno
            WHERE PickUpDateTime > DATE_SUB(NOW() ,INTERVAL 3 MONTH) AND PickUpDateTime < NOW() 
            GROUP BY reservation.VehicleSno ORDER BY Type"""
    c.execute(sql)
    data = c.fetchall()

    return render_template('admin_report.html', data=data)


#===========================================
# EMPLOYEE FUNCTIONS
#===========================================

@app.route('/car_data', methods=['GET'])
def car_data():
    if not session.get('role') == 'emp':
        abort(401)

    if request.args.get('location', ''):
        # location request, serve up cars in this location
        sql = """SELECT *, 
                CAST(Transmission_Type AS unsigned integer) as trans, 
                CAST(Auxiliary_Cable AS unsigned integer) as aux, 
                CAST(BluetoothConnectivity AS unsigned integer) as blue,
                CAST(UnderMaintenanceFlag AS unsigned integer) as maint 
                FROM car WHERE CarLocation = '{location}'""".format(location=request.args.get('location', ''))

    elif request.args.get('vsn', ''):
        # Specific request, serve up a car based on this request.
        sql = """SELECT *,
                CAST(Transmission_Type AS unsigned integer) as trans, 
                CAST(Auxiliary_Cable AS unsigned integer) as aux, 
                CAST(BluetoothConnectivity AS unsigned integer) as blue,
                CAST(UnderMaintenanceFlag AS unsigned integer) as maint 
                FROM car WHERE VehicleSno = {vsn}""".format(vsn=request.args.get('vsn',''))

    c.execute(sql)
    cars = c.fetchall()
    js = []
    for (vsn, aux_bit, trans_bit, cap, blue_bit, daily, hourly, color, cartype, model, maint_bit, loc, trans, aux, blue, maint) in cars:
        js.append({"vsn": vsn,
                    "aux": aux,
                    "trans": trans,
                    "cap": cap,
                    "blue": blue,
                    "daily": daily,
                    "hourly": hourly,
                    "color": color,
                    "type": cartype,
                    "model": model,
                    "maint": maint,
                    "location": loc})

    return Response(json.dumps(js),  mimetype='application/json')

@app.route('/manage_cars', methods=['GET', 'POST'])
def manage_cars():
    if not session.get('role') == 'emp':
        return redirect(url_for('home'))

    locations = "SELECT LocationName FROM location"
    c.execute(locations)
    locations = c.fetchall()

    t = "SELECT Distinct Type FROM car GROUP BY Type"
    c.execute(t)
    types = c.fetchall()

    models = "SELECT Distinct CarModel FROM car GROUP BY CarModel"
    c.execute(models)
    models = c.fetchall()
    
    if request.method == "POST":
        car_sql = ("INSERT INTO car(VehicleSno,Auxiliary_Cable,Transmission_Type,Seating_Capacity,BluetoothConnectivity,DailyRate,HourlyRate,Color,Type,CarModel,CarLocation) VALUES ({VehicleSno},{Auxiliary_Cable},{Transmission_Type},{Seating_Capacity},{BluetoothConnectivity},{DailyRate},{HourlyRate},'{Color}','{Type}','{CarModel}', '{CarLocation}')"
                   .format(VehicleSno=request.form['vsno'],
                            Auxiliary_Cable=request.form['aux'],
                            Transmission_Type=request.form['trans'],
                            Seating_Capacity=request.form['seat'],
                            BluetoothConnectivity=request.form['blue'],
                            DailyRate=request.form['daily'],
                            HourlyRate=request.form['hr'],
                            Color=request.form['color'],
                            Type=request.form['type'],
                            CarModel=request.form['model'],
                            CarLocation=request.form['location'],))
        
        try:
            c.execute(car_sql)
            conn.commit()
            flash('Car Inserted!')
        except pymysql.err.IntegrityError:
            flash("IntegrityError!", 'alert-error')
	   	
        
        return render_template('manage_cars.html',locations = locations, types = types)
    
    
    return render_template('manage_cars.html', models = models, locations = locations, types = types)

@app.route('/update_car', methods=['GET', 'POST'])
def update_car():
    if not session.get('role') == 'emp':
        return redirect(url_for('home'))

    if request.method == 'POST':
        if request.form['transType'] == 'Manual':
            trans = 1
        else:
            trans = 0

        car_sql = """UPDATE car SET CarLocation = '{l}', Type = '{t}', Color = '{c}', Seating_Capacity = {capacity}, 
                    Transmission_Type = ({trans}) WHERE VehicleSno = {vsn}""".format(t=request.form['carType'],
                                                                                c=request.form['color'],
                                                                                capacity=request.form['seatCap'],
                                                                                trans=trans,
                                                                                l=request.form['newLocation'],
                                                                                vsn=request.form['vsn'])
        c.execute(car_sql)
        conn.commit()
        flash('Car updated!')
    
    return redirect(url_for('manage_cars'))




@app.route('/maint_request', methods=['GET', 'POST'])
def maint_request():
    if not session.get('role') == 'emp':
        return redirect(url_for('home'))
        
    locations = "SELECT LocationName FROM location"
    c.execute(locations)
    locations = c.fetchall()

    if request.method == 'POST':
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        maint_req = """INSERT INTO maintenance_request 
                        VALUES ({vsn}, '{now}', '{user}')""".format(vsn=request.form['vsn'], now=now, user=session.get('username'))

        c.execute(maint_req)

        maint_prob = """INSERT INTO maintenance_request_problems
                        VALUES ({vsn}, '{now}', '{prob}')""".format(vsn=request.form['vsn'], now=now, user=session.get('username'), prob=request.form['problems'])
        c.execute(maint_prob)

        update_flag = """UPDATE car SET UnderMaintenanceFlag=(1) WHERE VehicleSno={vsn}""".format(vsn=request.form['vsn'])
        c.execute(update_flag)

        conn.commit()
        flash('Your report has been submitted', 'alert-success')

    return render_template('maint_request.html', locations = locations)


@app.route('/rental_change', methods=['GET', 'POST'])
def rental_change():
    if not session.get('role') == 'emp':
        return redirect(url_for('home'))
        
    dates = [x.strftime("%Y-%m-%d") for x in daterange(date.today(), date.today() + timedelta(365))]

    if request.method == 'POST':
        pickdate = request.form['pickdate']
        pickhour = request.form['pickhour']
        pickmin = request.form['pickmin']

        currdate = request.form['currdate']
        currhour = request.form['currhour']
        currmin = request.form['currmin']

        resid = request.form['resid']
    
        pickdatetime = datetime(int(pickdate[0:4]), int(pickdate[5:7]), int(pickdate[8:10]), int(pickhour), int(pickmin))
        currdatetime = datetime(int(currdate[0:4]), int(currdate[5:7]), int(currdate[8:10]), int(currhour), int(currmin))
        late_by = pickdatetime - currdatetime
        late_by = late_by.seconds/3600

        if pickdatetime < currdatetime:
            flash('You must pick a time after the current one', 'alert-error')
            return redirect(url_for('rental_change'))

        sql = """INSERT INTO reservation_extended_time 
                VALUES ({resid}, '{extended}')""".format(resid=resid, extended=pickdatetime.strftime('%Y-%m-%d %H:%M:%S'))

        c.execute(sql)
        conn.commit()

        sql = """SELECT Username, PickUpDateTime, ReturnDateTime, EmailAddress, PhoneNo, ResID, ReservationLocation FROM reservation 
                NATURAL JOIN member 
                WHERE PickUpDateTime < '{overlap}' 
                AND PickUpDateTime > '{curr}'""".format(overlap=pickdatetime.strftime('%Y-%m-%d %H:%M:%S'),
                                                        curr=currdatetime.strftime('%Y-%m-%d %H:%M:%S'))
    
        overlap = None
        c.execute(sql)
        overlap = c.fetchone()
        if overlap:
            sql = """UPDATE reservation SET LateFees={latefee} WHERE ResID={resid}""".format(latefee=50*late_by,resid=resid)
            c.execute(sql)
            conn.commit()

            flash('The new time has overlapped with an existing reservation, please amend')

        flash('The user reservation has been extended', 'alert-success')
        return render_template('rental_change.html', dates=dates, overlap=overlap)

    if request.args.get('username',''):
        rental_info = """SELECT car.CarModel , car.CarLocation, reservation.ReturnDateTime, reservation.resID FROM car 
                        INNER JOIN reservation ON reservation.VehicleSno = car.VehicleSno 
                        WHERE reservation.Username = '{user}' AND reservation.PickUpDateTime<now() 
                        AND reservation.ReturnDateTime>now()""".format(user=request.args.get('username', ''))
        #rental_info selects the data needed to auto populate the text boxes
        c.execute(rental_info)
        current = c.fetchone()

        if current:
            model, location, retdate, resid = current
            curr_date = retdate.strftime("%Y-%m-%d")
            curr_hour = retdate.hour
            curr_min = retdate.minute
        else:
            flash('No current reservation for user: {user}'.format(user=request.args.get('username', '')))
            curr_date = ''
            curr_hour = ''
            curr_min = ''

        return render_template('rental_change.html', resid=resid, dates=dates, model=model, curr_date=curr_date, curr_hour=curr_hour, curr_min=curr_min, username=request.args.get('username', ''))


    return render_template('rental_change.html', dates=dates)

@app.route('/delete_rental', methods=['POST'])
def del_rental():
    if not session.get('role') == 'emp':
        return redirect(url_for('home'))

    resid = request.form['overlapid']

    sql = """DELETE FROM reservation WHERE ResID = {resid}""".format(resid=resid)
    print sql
    c.execute(sql)
    conn.commit()

    flash('The users conflicting reservation has been deleted', 'alert-success')

    return redirect(url_for('rental_change'))

@app.route('/loc_prefs', methods=['GET'])
def loc_prefs():
    if not session.get('role') == 'emp':
        return redirect(url_for('home'))

    sql = """SELECT mon_name, ReservationLocation, ResCount, total_hours
            FROM (
                SELECT COUNT( ResID ) AS ResCount, SUM( TIMESTAMPDIFF( HOUR , PickUpDateTime, ReturnDateTime ) ) AS total_hours, MONTHNAME( PickUpDateTime ) AS mon_name, ReservationLocation
                    FROM reservation
                    WHERE PickUpDateTime > DATE_SUB( NOW( ) , INTERVAL 3 
                    MONTH ) 
                    AND PickUpDateTime < NOW( ) 
                    GROUP BY YEAR( PickUpDateTime ) , MONTH( PickUpDateTime ) , ReservationLocation
                ) AS thing1
            WHERE (
                thing1.mon_name, thing1.ResCount
            )
            IN (
                SELECT mon_name, MAX( ResCount ) 
                FROM (

                SELECT COUNT( ResID ) AS ResCount, SUM( TIMESTAMPDIFF( HOUR , PickUpDateTime, ReturnDateTime ) ) AS total_hours, MONTHNAME( PickUpDateTime ) AS mon_name, ReservationLocation
                    FROM reservation
                    WHERE PickUpDateTime > DATE_SUB( NOW( ) , INTERVAL 3 
                    MONTH ) 
                    AND PickUpDateTime < NOW( ) 
                    GROUP BY YEAR( PickUpDateTime ) , MONTH( PickUpDateTime ) , ReservationLocation
                    ) AS thing
                GROUP BY mon_name
            )"""
                
    c.execute(sql)

    return render_template('loc_prefs.html', data=c.fetchall())

@app.route('/freq_users', methods=['GET'])
def freq_users():
    if not session.get('role') == 'emp':
        return redirect(url_for('home'))

    #SQL to grab all the stuff
    sql = ("SELECT username, COUNT(*) FROM (user NATURAL JOIN reservation) GROUP BY username ORDER BY COUNT(*) DESC")
    c.execute(sql)
    tupe = c.fetchall()
    data = list(tupe)
    
    #If the list of data is more than five, it shortens it down to only the top five
    # You can use the databse LIMIT param
    try:
        data = data[0:4]
    except:
        pass
    #This part adds in the member's plan 
    for x in range(len(data)):
        data[x] = list(data[x])
        sql = "SELECT DrivingPlan FROM member where username ='{u}'".format(u = data[x][0])
        c.execute(sql)
        tupe = c.fetchall()
        plan = tupe[0][0]
        data[x].insert(1,plan)
    
    return render_template('freq_users.html', data=data)

@app.route('/maint_history', methods=['GET'])
def maint_history():
    if not session.get('role') == 'emp':
        return redirect(url_for('home'))

    sql = "Select CarModel,RequestDateTime,Username,Problem From (Select VehicleSno, CarModel, RequestDateTime, Username,Problem from car NATURAL JOIN maintenance_request NATURAL JOIN maintenance_request_problems) as T Natural Join (SELECT VehicleSno, count(*) AS total FROM maintenance_request GROUP BY VehicleSno ORDER BY total ASC) as J ORDER BY total Desc"
    c.execute(sql)
    data = list(c.fetchall())
    print data

    return render_template('maint_history.html', data = data)

if __name__ == "__main__":
	app.secret_key = 'sekret'
	app.run(debug=True)

