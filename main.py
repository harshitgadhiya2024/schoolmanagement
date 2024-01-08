"""
    In this file handling all flask api route and maintain all of operation and sessions
"""

from flask import (flash, Flask, redirect, render_template, request,
                   session, url_for, send_file)
import os
from flask_cors import CORS
import json
from constant import constant_data
from operations.mongo_connection import mongo_connect, data_added, find_all_data, find_spec_data, update_mongo_data, delete_data
from operations.common_func import export_panel_data, delete_panel_data, get_unique_admin_id, get_admin_data, validate_phone_number, password_validation, logger_con, get_timestamp, get_error_msg, get_response_msg, get_unique_student_id, get_unique_teacher_id, search_panel_data
import random
from flask_mail import Mail
from werkzeug.utils import secure_filename

# create a flask app instance
app = Flask(__name__)

# Apply cors policy in our app instance
CORS(app)

# setup all config variable
app.config["enviroment"] = constant_data.get("enviroment", "qa")
app.config["SECRET_KEY"] = constant_data.get("app_secreat_key", "sdfsf65416534sdfsdf4653")
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'codescatter8980@gmail.com'
app.config['MAIL_PASSWORD'] = 'zuvgjolhsfgeyfjj'
app.config['MAIL_USE_SSL'] = True
app.config["PROFILE_UPLOAD_FOLDER"] = 'static/uploads/profiles/'
app.config["EXPORT_UPLOAD_FOLDER"] = 'static/uploads/export_file/'

# handling our application secure type like http or https
secure_type = constant_data["secure_type"]

# create mail instance for our application
mail = Mail(app)

# logger & MongoDB connection
# logger_con(app=app)
client = mongo_connect(app=app)

# allow only that image file extension
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif' 'svg'])

def allowed_photos(filename):
    """
    checking file extension is correct or not

    :param filename: file name
    :return: True, False
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def checking_upload_folder(filename):
    """
    checking file is duplicate or not

    :param filename: file name
    :return: status of file
    """
    try:
        entries = os.listdir(app.config["PROFILE_UPLOAD_FOLDER"])
        if filename in entries:
            return "duplicate"
        else:
            return "not duplicate"

    except Exception as e:
        print(e)

############################ Login operations ##################################
@app.route("/", methods=["GET", "POST"])
def login():
    """
    In this route we can handling student, teacher and admin login process
    :return: login template
    """
    try:
        login_dict = session.get("login_dict", "nothing")
        if login_dict != "nothing":
            type = login_dict["type"]
            if type == "Student":
                return redirect(url_for('student_dashboard', _external=True, _scheme=secure_type))
            elif type=="Teacher":
                return redirect(url_for('teacher_dashboard', _external=True, _scheme=secure_type))
            else:
                return redirect(url_for('admin_dashboard', _external=True, _scheme=secure_type))

        db = client["college_management"]
        all_types = ["Teacher", "Student", "Admin"]
        if request.method == "POST":
            id = request.form["id"]
            password = request.form["password"]
            type = request.form["type"]

            if type=="Teacher":
                di = {"type": "teacher", "teacher_id": int(id), "password": password}
                teacher_data = find_spec_data(app, db, "login_mapping", di)
                teacher_data = list(teacher_data)
                if len(teacher_data)==0:
                    flash("Please use correct credential..")
                    return render_template("login.html", all_types=all_types)
                else:
                    session["login_dict"] = {"id": id, "type": "Teacher"}
                    return redirect(url_for('teacher_dashboard', _external=True, _scheme=secure_type))
            elif type=="Student":
                di = {"type": "student", "student_id": int(id), "password": password}
                student_data = find_spec_data(app, db, "login_mapping", di)
                student_data = list(student_data)
                if len(student_data) == 0:
                    flash("Please use correct credential..")
                    return render_template("login.html", all_types=all_types)
                else:
                    session["login_dict"] = {"id": id, "type": "Student"}
                    return redirect(url_for('student_dashboard', _external=True, _scheme=secure_type))
            else:
                di = {"type": "admin", "admin_id": int(id), "password": password}
                admin_data = find_spec_data(app, db, "login_mapping", di)
                admin_data = list(admin_data)
                if len(admin_data) == 0:
                    flash("Please use correct credential..")
                    return render_template("login.html", all_types=all_types)
                else:
                    photo_link = admin_data[0].get("photo_link", "")
                    session["login_dict"] = {"id": id, "type": "Admin", "photo_link": photo_link}
                    return redirect(url_for('admin_dashboard', _external=True, _scheme=secure_type))

        else:
            return render_template("login.html", all_types=all_types)

    except Exception as e:
        app.logger.debug(f"Error in login route: {e}")
        flash("Please try again...")
        return redirect(url_for('login', _external=True, _scheme=secure_type))

@app.route("/otp_sending", methods=["GET", "POST"])
def otp_sending():
    """
    That funcation was sending a otp for user
    """

    try:
        otp = random.randint(100000, 999999)
        session["otp"] = otp
        email = session["register_dict"]["email"]
        mail.send_message("OTP Received",
                          sender="harshitgadhiya8980@gmail.com",
                          recipients=[email],
                          body=f'Hello There,\n We hope this message finds you well. As part of our ongoing commitment to ensure the security of your account, we have initiated a verification process.\nYour One-Time Password (OTP) for account verification is: [{otp}]\nPlease enter this OTP on the verification page to complete the process. Note that the OTP is valid for a limited time, so we recommend entering it promptly.\nIf you did not initiate this verification or have any concerns regarding your account security, please contact our support team immediately at help@codescatter.com\n\nThank you for your cooperation.\nBest regards,\nCodescatter',
                          html=f"<p>Hello There,</p><p>We hope this message finds you well. As part of our ongoing commitment to ensure the security of your account, we have initiated a verification process.</p><p>Your One-Time Password (OTP) for account verification is: <h2><b>{otp}</h2></b></p><p>Please enter this OTP on the verification page to complete the process. Note that the OTP is valid for a limited time, so we recommend entering it promptly.</p><p>If you did not initiate this verification or have any concerns regarding your account security, please contact our support team immediately at help@codescatter.com</p><p>Thank you for your cooperation.</p><p>Best regards,<br>Codescatter</p>")
        flash("OTP sending successfully...........")
        return redirect(url_for('otp_verification', _external=True, _scheme=secure_type))

    except Exception as e:
        app.logger.debug(f"Error in otp sending route: {e}")
        flash("Please try again...")
        return redirect(url_for('otp_verification', _external=True, _scheme=secure_type))

@app.route("/otp_verification", methods=["GET", "POST"])
def otp_verification():
    """
    That funcation can use otp_verification and new_password set link generate
    """

    try:
        db = client["college_management"]
        email = session["register_dict"]["email"]
        if request.method == "POST":
            get_otp = request.form["otp"]
            get_otp = int(get_otp)
            send_otp = session.get("otp", "")
            if get_otp == int(send_otp):
                register_dict = session["register_dict"]
                if register_dict["type"] == "student":
                    student_mapping_dict = {}
                    student_mapping_dict["student_id"] = register_dict["student_id"]
                    student_mapping_dict["username"] = register_dict["username"]
                    student_mapping_dict["email"] = register_dict["email"]
                    student_mapping_dict["password"] = register_dict["password"]
                    student_mapping_dict["type"] = register_dict["type"]
                    data_added(app, db, "students_data", register_dict)
                    data_added(app, db, "login_mapping", student_mapping_dict)
                    student_id = register_dict["student_id"]
                    username = register_dict["username"]
                    mail.send_message("[Rylee] Account Credentials",
                                      sender="harshitgadhiya8980@gmail.com",
                                      recipients=[email],
                                      body=f"Hello There,\nWe hope this message finds you well. As part of our ongoing commitment to ensure the security of your account. Your request for opening an 'Account' has been processed successfully and your account has been opened.\n Please check with the below credential.\nStudentID: {student_id}\nUsername: {username}\nif you have any concerns regarding your account security, be sure to get in touch with our support team immediately at help@codescatter.com\nThank you for your cooperation.\nBest regards,\nCodescatter",
                                      html=f'<p>Hello There,</p><p>We hope this message finds you well. As part of our ongoing commitment to ensure the security of your account. Your request for opening an "Account" has been processed successfully and your account has been opened.</p><p>Please check with the below credential.</p><p><h2><b>Student_id - {student_id}</b></h2></p><p><h2><b>Username - {username}</b></h2></p><p>if you have any concerns regarding your account security, be sure to get in touch with our support team immediately at help@codescatter.com</p><p>Thank you for your cooperation.</p><p>Best regards,<br>Codescatter</p>')

                    return redirect(url_for('student_register', _external=True, _scheme=secure_type))
                else:
                    teacher_mapping_dict = {}
                    teacher_mapping_dict["teacher_id"] = register_dict["teacher_id"]
                    teacher_mapping_dict["username"] = register_dict["username"]
                    teacher_mapping_dict["email"] = register_dict["email"]
                    teacher_mapping_dict["password"] = register_dict["password"]
                    teacher_mapping_dict["type"] = register_dict["type"]
                    data_added(app, db, "teacher_data", register_dict)
                    data_added(app, db, "login_mapping", teacher_mapping_dict)
                    teacher_id = register_dict["teacher_id"]
                    username = register_dict["username"]
                    mail.send_message("[Rylee] Account Credentials",
                                      sender="harshitgadhiya8980@gmail.com",
                                      recipients=[email],
                                      body=f"Hello There,\nWe hope this message finds you well. As part of our ongoing commitment to ensure the security of your account. Your request for opening an 'Account' has been processed successfully and your account has been opened.\n Please check with the below credential.\nTeacherID: {teacher_id}\nUsername: {username}\nif you have any concerns regarding your account security, be sure to get in touch with our support team immediately at help@codescatter.com\nThank you for your cooperation.\nBest regards,\nCodescatter",
                                      html=f'<p>Hello There,</p><p>We hope this message finds you well. As part of our ongoing commitment to ensure the security of your account. Your request for opening an "Account" has been processed successfully and your account has been opened.</p><p>Please check with the below credential.</p><p><h2><b>TeacherID - {teacher_id}</b></h2></p><p><h2><b>Username - {username}</b></h2></p><p>if you have any concerns regarding your account security, be sure to get in touch with our support team immediately at help@codescatter.com</p><p>Thank you for your cooperation.</p><p>Best regards,<br>Codescatter</p>')

                    return redirect(url_for('teacher_register', _external=True, _scheme=secure_type))
            else:
                flash("OTP is wrong. Please enter correct otp")
                return redirect(url_for('otp_verification', _external=True, _scheme=secure_type))
        else:
            otp = random.randint(100000, 999999)
            session["otp"] = otp
            mail.send_message("OTP Received",
                              sender="harshitgadhiya8980@gmail.com",
                              recipients=[email],
                              body=f"Hello There,\n We hope this message finds you well. As part of our ongoing commitment to ensure the security of your account, we have initiated a verification process.\nYour One-Time Password (OTP) for account verification is: [{otp}]\nPlease enter this OTP on the verification page to complete the process. Note that the OTP is valid for a limited time, so we recommend entering it promptly.\nIf you did not initiate this verification or have any concerns regarding your account security, please contact our support team immediately at help@codescatter.com\n\nThank you for your cooperation.\nBest regards,\nCodescatter",
                              html=f'<p>Hello There,</p><p>We hope this message finds you well. As part of our ongoing commitment to ensure the security of your account, we have initiated a verification process.</p><p>Your One-Time Password (OTP) for account verification is: <h2><b>{otp}</h2></b></p><p>Please enter this OTP on the verification page to complete the process. Note that the OTP is valid for a limited time, so we recommend entering it promptly.</p><p>If you did not initiate this verification or have any concerns regarding your account security, please contact our support team immediately at help@codescatter.com</p><p>Thank you for your cooperation.</p><p>Best regards,<br>Codescatter</p>')
            flash("OTP sent successfully......Please check your mail")
            return render_template("otp_verification.html")

    except Exception as e:
        app.logger.debug(f"Error in otp verification route: {e}")
        flash("Please try again...")
        return redirect(url_for('otp_verification', _external=True, _scheme=secure_type))

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    """
    That funcation was logout session and clear user session
    """

    try:
        session.clear()
        return redirect(url_for('login', _external=True, _scheme=secure_type))

    except Exception as e:
        flash("Please try again.......................................")
        return redirect(url_for('login', _external=True, _scheme=secure_type))


########################## Operation Route ####################################

@app.route("/admin/delete_data/<object>", methods=["GET", "POST"])
def delete_data(object):
    """
    That funcation can use delete from student, teacher and admin from admin panel
    """

    try:
        spliting_object = object.split("-")
        panel = spliting_object[0]
        id = spliting_object[1]
        delete_dict = {}
        if panel == "admin":
            coll_name = "admin_data"
            delete_dict["admin_id"] = int(id)
            delete_dict["type"] = "admin"
            delete_panel_data(app, client, "college_management", coll_name, delete_dict)
            return redirect(url_for('admin_data_list', _external=True, _scheme=secure_type))
        elif panel == "student":
            delete_dict["student_id"] = int(id)
            delete_dict["type"] = "student"
            coll_name = "students_data"
            delete_panel_data(app, client, "college_management", coll_name, delete_dict)
            return redirect(url_for('student_data_list', _external=True, _scheme=secure_type))
        else:
            delete_dict["teacher_id"] = int(id)
            delete_dict["type"] = "teacher"
            coll_name = "teacher_data"
            delete_panel_data(app, client, "college_management", coll_name, delete_dict)
            return redirect(url_for('teacher_data_list', _external=True, _scheme=secure_type))


    except Exception as e:
        app.logger.debug(f"Error in delete data from database: {e}")
        flash("Please try again...")
        return redirect(url_for('delete_data', _external=True, _scheme=secure_type))

@app.route("/admin/export/<object>", methods=["GET", "POST"])
def export_data(object):
    """
    That funcation can use delete from student, teacher and admin from admin panel
    """

    try:
        db = client["college_management"]
        spliting_object = object.split("-")
        panel = spliting_object[0]
        type = spliting_object[1]
        if panel == "admin":
            res = find_all_data(app, db, "admin_data")
            all_data = []
            for each_res in res:
                del each_res["_id"]
                all_data.append(each_res)
            output_path = export_panel_data(app, all_data, panel, type)
            return send_file(output_path, as_attachment=True)
        elif panel == "student":
            res = find_all_data(app, db, "students_data")
            all_data = []
            for each_res in res:
                del each_res["_id"]
                all_data.append(each_res)
            output_path = export_panel_data(app, all_data, panel, type)
            return send_file(output_path, as_attachment=True)
        else:
            res = find_all_data(app, db, "teacher_data")
            all_data = []
            for each_res in res:
                del each_res["_id"]
                all_data.append(each_res)
            output_path = export_panel_data(app, all_data, panel, type)
            return send_file(output_path, as_attachment=True)


    except Exception as e:
        app.logger.debug(f"Error in export data from database: {e}")
        flash("Please try again...")
        return redirect(url_for('export_data', _external=True, _scheme=secure_type))

@app.route("/admin/edit_data/<object>", methods=["GET", "POST"])
def edit_data(object):
    """
    That funcation can use delete from student, teacher and admin from admin panel
    """

    try:
        spliting_object = object.split("-")
        panel = spliting_object[0]
        print(f"Panel : {panel}")
        id = spliting_object[1]
        delete_dict = {}
        if panel == "admin":
            coll_name = "admin_data"
            delete_dict["admin_id"] = id
            delete_dict["type"] = "admin"
        elif panel == "student":
            delete_dict["student_id"] = id
            delete_dict["type"] = "student"
            coll_name = "students_data"
        else:
            delete_dict["teacher_id"] = id
            delete_dict["type"] = "teacher"
            coll_name = "teacher_data"
        return render_template(f'add-{panel}.html')

    except Exception as e:
        app.logger.debug(f"Error in edit data from database: {e}")
        flash("Please try again...")
        spliting_object = object.split("-")
        panel = spliting_object[0]
        return render_template(f'{panel}s.html')

@app.route("/search_data/<object>", methods=["GET", "POST"])
def search_data(object):
    """
    That funcation can use search data from student, teacher and admin from admin panel
    """

    try:
        panel = object
        print(f"Panel : {panel}")
        search_dict = {}
        id = request.form.get('id', '')
        username = request.form.get('username', '')
        contact_no = request.form.get('contact_no', '')
        email = request.form.get('email', '')
        panel_mapping = {
            "admin": "admin_data",
            "student": "students_data",
            "teacher": "teacher_data"
        }
        if panel in panel_mapping:
            if id:
                search_value = f'{panel}_id|{id}'
            elif username:
                search_value = f'username|{username}'
            elif contact_no:
                search_value = f'contact_no|{contact_no}'
            else:
                search_value = f'email|{email}'
            coll_name = panel_mapping[panel]
            search_dict = search_panel_data(app, client, "college_management", search_value, coll_name)
        else:
            app.logger.debug(f"Error in searching data from database")
        return render_template('search_result.html', search_dict=search_dict)

    except Exception as e:
        app.logger.debug(f"Error in searching data from database: {e}")
        print(e)
        flash("Please try again...")
        panel = object
        return render_template(f'{panel}s.html')


########################### Admin Operations ##################################

# Admin dashboard Route
@app.route("/admin_dashboard", methods=["GET", "POST"])
def admin_dashboard():
    """
    That funcation can use show admin dashboard to admin user
    """

    try:
        login_dict = session.get("login_dict", "nothing")
        if login_dict != "nothing":
            type = login_dict["type"]
            id = login_dict["id"]
            photo_link = "/"+login_dict["photo_link"]
        else:
            type = "Anonymous"
            id = "anonymous"
            photo_link = "/static/assets/img/profiles/avatar-01.jpg"
        return render_template("index.html", admin_id=id, type=type, photo_link=photo_link)

    except Exception as e:
        app.logger.debug(f"Error in admin dashboard route: {e}")
        flash("Please try again...")
        return redirect(url_for('admin_dashboard', _external=True, _scheme=secure_type))

@app.route("/admin/admin_data", methods=["GET", "POST"])
def admin_data_list():
    """
    That funcation can use show all admins data from admin panel
    """

    try:
        login_dict = session.get("login_dict", "nothing")
        type = login_dict["type"]
        id = login_dict["id"]
        photo_link = "/" + login_dict["photo_link"]
        all_keys, all_values = get_admin_data(app, client, "college_management", "admin_data")
        return render_template("admins.html", all_keys=all_keys, all_values=all_values, type=type, admin_id=id, photo_link=photo_link)

    except Exception as e:
        app.logger.debug(f"Error in show admins data from admin panel: {e}")
        flash("Please try again..")
        return redirect(url_for('admin_data_list', _external=True, _scheme=secure_type))

@app.route("/admin/add_admin", methods=["GET", "POST"])
def add_admin():
    """
    In this route we can handling admin register process
    :return: register template
    """
    try:
        login_dict = session.get("login_dict", "nothing")
        type = login_dict["type"]
        admin_id = login_dict["id"]
        photo_main_link = "/" + login_dict["photo_link"]
        db = client["college_management"]
        # set all dynamic variable value
        allcity = ["ahmedabad", "surat", "jamnagar", "junagadh", "navsari", "bhavnagar"]
        allstate = ["gujarat", "karnataka", "keral", "delhi", "rajasthan"]
        allcountry = ["USA", "UK", "IN", "CA"]
        allcountrycode = ["+91", "+221"]

        if request.method == "POST":
            photo_link = request.files["photo_link"]
            first_name = request.form["first_name"]
            last_name = request.form["last_name"]
            username = request.form["username"]
            password = request.form["password"]
            gender = request.form["gender"]
            countrycode = request.form["countrycode"]
            contact_no = request.form["contact_no"]
            emergency_contact_no = request.form["emer_contact_no"]
            email = request.form["email"]
            address = request.form["address"]
            city = request.form["city"]
            state = request.form["state"]
            country = request.form["country"]
            contact_no = countrycode + " " + contact_no
            emergency_contact_no = countrycode + " " + emergency_contact_no

            if 'photo_link' not in request.files:
                flash('No file part')
                return render_template("add-admin.html", allcountrycode=allcountrycode, allcity=allcity,
                                       allstate=allstate, allcountry=allcountry,
                                       first_name=first_name, last_name=last_name,username=username, password=password,
                                       gender=gender, contact_no=contact_no, emergency_contact_no=emergency_contact_no,
                                       email=email, address=address, type=type, photo_link=photo_main_link, admin_id=admin_id)

            if photo_link.filename == '':
                flash('No image selected for uploading')
                return render_template("add-admin.html", allcountrycode=allcountrycode, allcity=allcity,
                                       allstate=allstate, allcountry=allcountry,
                                       first_name=first_name, last_name=last_name, username=username, password=password,
                                       gender=gender, contact_no=contact_no, emergency_contact_no=emergency_contact_no,
                                       email=email, address=address, type=type, photo_link=photo_main_link, admin_id=admin_id)

            if photo_link and allowed_photos(photo_link.filename):
                filename = secure_filename(username+".jpg")
                ans = checking_upload_folder(filename=filename)
                if ans != "duplicate":
                    photo_link.save(os.path.join(app.config["PROFILE_UPLOAD_FOLDER"], filename))
                    photo_path = os.path.join(app.config["PROFILE_UPLOAD_FOLDER"], filename)
                else:
                    flash('This filename already exits')
                    return render_template("add-admin.html", allcountrycode=allcountrycode, allcity=allcity,
                                           allstate=allstate, allcountry=allcountry,
                                           first_name=first_name, last_name=last_name, username=username,
                                           password=password,
                                           gender=gender, contact_no=contact_no,
                                           emergency_contact_no=emergency_contact_no,
                                           email=email, address=address, type=type, photo_link=photo_main_link, admin_id=admin_id)
            else:
                flash('This file format is not supported.....')
                return render_template("add-admin.html", allcountrycode=allcountrycode, allcity=allcity,
                                       allstate=allstate, allcountry=allcountry,
                                       first_name=first_name, last_name=last_name, username=username, password=password,
                                       gender=gender, contact_no=contact_no, emergency_contact_no=emergency_contact_no,
                                       email=email, address=address, type=type, photo_link=photo_main_link, admin_id=admin_id)

            #username validation
            all_admin_data = find_all_data(app, db, "admin_data")
            get_all_username = [ad_data["username"] for ad_data in all_admin_data]
            if username in get_all_username:
                flash("Admin Username already exits. Please try with different Username")
                return render_template("add-admin.html", allcountrycode=allcountrycode, allcity=allcity, allstate=allstate, allcountry=allcountry,
                                first_name=first_name, last_name=last_name, password=password,
                               gender=gender, contact_no=contact_no, emergency_contact_no=emergency_contact_no, email=email,
                                address=address, type=type, photo_link=photo_main_link, admin_id=admin_id)

            #password validation
            if not password_validation(app=app, password=password):
                flash("Please choose strong password. Add at least 1 special character, number, capitalize latter..")
                return render_template("add-admin.html",allcountrycode=allcountrycode, allcity=allcity, allstate=allstate,
                                       allcountry=allcountry, username=username, first_name=first_name, last_name=last_name,
                                       gender=gender, contact_no=contact_no,
                                       emergency_contact_no=emergency_contact_no, email=email,
                                       address=address, type=type, photo_link=photo_main_link, admin_id=admin_id)

            # contact number and emergency contact number validation
            get_phone_val = validate_phone_number(app=app, phone_number=contact_no)
            get_emergency_phone_val = validate_phone_number(app, emergency_contact_no)
            if get_phone_val == "invalid number":
                flash("Please enter correct contact no.")
                return render_template("add-admin.html",allcountrycode=allcountrycode, allcity=allcity, allstate=allstate,
                                       allcountry=allcountry, password=password, username=username, first_name=first_name,
                                       last_name=last_name, gender=gender,
                                       emergency_contact_no=emergency_contact_no, email=email,
                                       address=address, type=type, photo_link=photo_main_link, admin_id=admin_id)

            if get_emergency_phone_val == "invalid number":
                flash("Please enter correct emergency contact no.")
                return render_template("add-admin.html",allcountrycode=allcountrycode, allcity=allcity, allstate=allstate,
                                       allcountry=allcountry, password=password, username=username, first_name=first_name,
                                       last_name=last_name, gender=gender, contact_no=contact_no, email=email,
                                       address=address, type=type, photo_link=photo_main_link, admin_id=admin_id)

            #admin-id validation
            all_admin_data = find_spec_data(app, db, "login_mapping", {"type": "admin"})
            get_all_admin_id = [ad_data["admin_id"] for ad_data in all_admin_data]
            unique_admin_id = get_unique_admin_id(app, get_all_admin_id)
            register_dict = {
                "photo_link": photo_path,
                "admin_id": unique_admin_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "password": password,
                "gender": gender,
                "contact_no": contact_no,
                "emergency_contact_no": emergency_contact_no,
                "email": email,
                "address": address,
                "city": city,
                "state": state,
                "country": country,
                "type": "admin",
                "inserted_on": get_timestamp(app),
                "updated_on": get_timestamp(app)
            }

            admin_mapping_dict = {}
            admin_mapping_dict["photo_link"] = photo_path
            admin_mapping_dict["admin_id"] = unique_admin_id
            admin_mapping_dict["username"] = username
            admin_mapping_dict["email"] = email
            admin_mapping_dict["password"] = password
            admin_mapping_dict["type"] = "admin"
            data_added(app, db, "admin_data", register_dict)
            data_added(app, db, "login_mapping", admin_mapping_dict)
            mail.send_message("[Rylee] Account Credentials",
                              sender="harshitgadhiya8980@gmail.com",
                              recipients=[email],
                              body=f"Hello There,\nWe hope this message finds you well. As part of our ongoing commitment to ensure the security of your account. Your request for opening an 'Account' has been processed successfully and your account has been opened.\n Please check with the below credential.\nAdminID: {unique_admin_id}\nUsername: {username}\nif you have any concerns regarding your account security, be sure to get in touch with our support team immediately at help@codescatter.com\nThank you for your cooperation.\nBest regards,\nCodescatter",
                              html=f'<p>Hello There,</p><p>We hope this message finds you well. As part of our ongoing commitment to ensure the security of your account. Your request for opening an "Account" has been processed successfully and your account has been opened.</p><p>Please check with the below credential.</p><p><h2><b>AdminID - {unique_admin_id}</b></h2></p><p><h2><b>Username - {username}</b></h2></p><p>if you have any concerns regarding your account security, be sure to get in touch with our support team immediately at help@codescatter.com</p><p>Thank you for your cooperation.</p><p>Best regards,<br>Codescatter</p>')
            flash("Data Added Successfully")
            return redirect(url_for('admin_data_list', _external=True, _scheme=secure_type))
        else:
            return render_template("add-admin.html", type=type, photo_link=photo_main_link, admin_id=admin_id, allcountrycode=allcountrycode, allcity=allcity, allstate=allstate, allcountry=allcountry)

    except Exception as e:
        app.logger.debug(f"Error in add admin data route: {e}")
        flash("Please try again...")
        return redirect(url_for('add_admin', _external=True, _scheme=secure_type))

@app.route("/admin/student_data", methods=["GET", "POST"])
def student_data_list():
    """
    That funcation can use show all students data from admin panel
    """

    try:
        login_dict = session.get("login_dict", "nothing")
        type = login_dict["type"]
        id = login_dict["id"]
        photo_link = "/" + login_dict["photo_link"]
        all_keys, all_values = get_admin_data(app, client, "college_management", "students_data")
        return render_template("students.html", type=type, admin_id=id, photo_link=photo_link, all_keys=all_keys, all_values=all_values)

    except Exception as e:
        app.logger.debug(f"Error in student data list route: {e}")
        flash("Please try again...")
        return redirect(url_for('student_data_list', _external=True, _scheme=secure_type))

@app.route("/admin/add_student", methods=["GET", "POST"])
def add_student():
    """
    In this route we can handling student register process
    :return: register template
    """
    try:
        login_dict = session.get("login_dict", "nothing")
        type = login_dict["type"]
        admin_id = login_dict["id"]
        photo_student_link = "/" + login_dict["photo_link"]
        db = client["college_management"]
        # set all dynamic variable value
        allcity = ["ahmedabad", "surat", "jamnagar", "junagadh", "navsari", "bhavnagar"]
        allstate = ["gujarat", "karnataka", "keral", "delhi", "rajasthan"]
        allcountry = ["USA", "UK", "IN", "CA"]
        allbatchyear = [2018, 2019, 2020, 2021, 2022, 2023, 2024]
        allcountrycode = ["+91", "+221"]

        if request.method == "POST":
            photo_link = request.files["photo_link"]
            first_name = request.form["first_name"]
            last_name = request.form["last_name"]
            username = request.form["username"]
            password = request.form["password"]
            dob = request.form["dob"]
            gender = request.form["gender"]
            countrycode = request.form["countrycode"]
            contact_no = request.form["contact_no"]
            emergency_contact_no = request.form["emer_contact_no"]
            email = request.form["email"]
            address = request.form["address"]
            city = request.form["city"]
            state = request.form["state"]
            country = request.form["country"]
            admission_date = request.form["admission_date"]
            enrolled_cource = request.form["enrolled_cource"]
            batch_year = request.form["batch_year"]
            contact_no = countrycode + " " + contact_no
            emergency_contact_no = countrycode + " " + emergency_contact_no

            if 'photo_link' not in request.files:
                flash('No file part')
                return render_template("add-student.html", allcountrycode=allcountrycode, username=username, allcity=allcity,
                                       allstate=allstate, allcountry=allcountry, type=type, admin_id=admin_id, photo_link=photo_student_link,
                                       allbatchyear=allbatchyear, first_name=first_name, last_name=last_name,
                                       password=password,
                                       dob=dob, gender=gender, contact_no=contact_no,
                                       emergency_contact_no=emergency_contact_no, email=email,
                                       address=address, admission_date=admission_date, enrolled_cource=enrolled_cource)


            if photo_link.filename == '':
                flash('No image selected for uploading')
                return render_template("add-student.html", allcountrycode=allcountrycode, username=username,
                                       allcity=allcity, allstate=allstate, allcountry=allcountry, type=type, admin_id=admin_id,
                                       photo_link=photo_student_link, allbatchyear=allbatchyear, first_name=first_name, last_name=last_name,
                                       password=password, dob=dob, gender=gender, contact_no=contact_no,
                                       emergency_contact_no=emergency_contact_no, email=email,
                                       address=address, admission_date=admission_date, enrolled_cource=enrolled_cource)

            if photo_link and allowed_photos(photo_link.filename):
                filename = secure_filename("student_"+username+".jpg")
                ans = checking_upload_folder(filename=filename)
                if ans != "duplicate":
                    photo_link.save(os.path.join(app.config["PROFILE_UPLOAD_FOLDER"], filename))
                    photo_path = os.path.join(app.config["PROFILE_UPLOAD_FOLDER"], filename)
                else:
                    flash('This filename already exits')
                    return render_template("add-student.html", allcountrycode=allcountrycode, username=username,
                                           allcity=allcity, allstate=allstate, allcountry=allcountry, type=type,
                                           admin_id=admin_id,
                                           photo_link=photo_student_link, allbatchyear=allbatchyear,
                                           first_name=first_name, last_name=last_name,
                                           password=password, dob=dob, gender=gender, contact_no=contact_no,
                                           emergency_contact_no=emergency_contact_no, email=email,
                                           address=address, admission_date=admission_date,
                                           enrolled_cource=enrolled_cource)
            else:
                flash('This file format is not supported.....')
                return render_template("add-student.html", allcountrycode=allcountrycode, username=username,
                                       allcity=allcity, allstate=allstate, allcountry=allcountry, type=type,
                                       admin_id=admin_id,
                                       photo_link=photo_student_link, allbatchyear=allbatchyear, first_name=first_name,
                                       last_name=last_name,
                                       password=password, dob=dob, gender=gender, contact_no=contact_no,
                                       emergency_contact_no=emergency_contact_no, email=email,
                                       address=address, admission_date=admission_date, enrolled_cource=enrolled_cource)


            #username validation
            all_student_data = find_all_data(app, db, "students_data")
            get_all_username = [st_data["username"] for st_data in all_student_data]
            if username in get_all_username:
                flash("Username already exits. Please try with different Username")
                return render_template("add-student.html", type=type, admin_id=admin_id, photo_link=photo_student_link, allcountrycode=allcountrycode, allcity=allcity, allstate=allstate, allcountry=allcountry,
                                allbatchyear=allbatchyear, first_name=first_name, last_name=last_name, password=password,
                                dob=dob, gender=gender, contact_no=contact_no, emergency_contact_no=emergency_contact_no, email=email,
                                address=address, admission_date=admission_date, enrolled_cource=enrolled_cource)

            #password validation
            if not password_validation(app=app, password=password):
                flash("Please choose strong password. Add at least 1 special character, number, capitalize latter..")
                return render_template("add-student.html",allcountrycode=allcountrycode, allcity=allcity, allstate=allstate,
                                       allcountry=allcountry, type=type, admin_id=admin_id, photo_link=photo_student_link,
                                       allbatchyear=allbatchyear, username=username, first_name=first_name, last_name=last_name,
                                       dob=dob, gender=gender, contact_no=contact_no,
                                       emergency_contact_no=emergency_contact_no, email=email,
                                       address=address, admission_date=admission_date, enrolled_cource=enrolled_cource)

            # contact number and emergency contact number validation
            get_phone_val = validate_phone_number(app=app, phone_number=contact_no)
            get_emergency_phone_val = validate_phone_number(app, emergency_contact_no)
            if get_phone_val == "invalid number":
                flash("Please enter correct contact no.")
                return render_template("add-student.html",allcountrycode=allcountrycode, allcity=allcity, allstate=allstate,
                                       allcountry=allcountry, password=password,
                                       allbatchyear=allbatchyear, username=username, first_name=first_name,
                                       last_name=last_name, type=type, admin_id=admin_id, photo_link=photo_student_link,
                                       dob=dob, gender=gender,
                                       emergency_contact_no=emergency_contact_no, email=email,
                                       address=address, admission_date=admission_date, enrolled_cource=enrolled_cource)

            if get_emergency_phone_val == "invalid number":
                flash("Please enter correct emergency contact no.")
                return render_template("add-student.html",allcountrycode=allcountrycode, allcity=allcity, allstate=allstate,
                                       allcountry=allcountry, password=password,
                                       allbatchyear=allbatchyear, username=username, first_name=first_name,
                                       last_name=last_name, type=type, admin_id=admin_id, photo_link=photo_student_link,
                                       dob=dob, gender=gender, contact_no=contact_no, email=email,
                                       address=address, admission_date=admission_date, enrolled_cource=enrolled_cource)

            #student-id validation
            all_student_data = find_spec_data(app, db, "login_mapping", {"type": "student"})
            get_all_student_id = [st_data["student_id"] for st_data in all_student_data]
            unique_student_id = get_unique_student_id(app, get_all_student_id)
            register_dict = {
                "photo_link": photo_path,
                "student_id": unique_student_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "password": password,
                "dob": dob,
                "gender": gender,
                "contact_no": contact_no,
                "emergency_contact_no": emergency_contact_no,
                "email": email,
                "address": address,
                "city": city,
                "state": state,
                "country": country,
                "admission_date": admission_date,
                "enrolled_cource": enrolled_cource,
                "batch_year": batch_year,
                "type": "student",
                "inserted_on": get_timestamp(app),
                "updated_on": get_timestamp(app)
            }

            student_mapping_dict = {}
            student_mapping_dict["photo_link"] = photo_path
            student_mapping_dict["student_id"] = unique_student_id
            student_mapping_dict["username"] = username
            student_mapping_dict["email"] = email
            student_mapping_dict["password"] = password
            student_mapping_dict["type"] = "student"
            data_added(app, db, "students_data", register_dict)
            data_added(app, db, "login_mapping", student_mapping_dict)
            mail.send_message("[Rylee] Account Credentials",
                              sender="harshitgadhiya8980@gmail.com",
                              recipients=[email],
                              body=f"Hello There,\nWe hope this message finds you well. As part of our ongoing commitment to ensure the security of your account. Your request for opening an 'Account' has been processed successfully and your account has been opened.\n Please check with the below credential.\nStudentID: {unique_student_id}\nUsername: {username}\nif you have any concerns regarding your account security, be sure to get in touch with our support team immediately at help@codescatter.com\nThank you for your cooperation.\nBest regards,\nCodescatter",
                              html=f'<p>Hello There,</p><p>We hope this message finds you well. As part of our ongoing commitment to ensure the security of your account. Your request for opening an "Account" has been processed successfully and your account has been opened.</p><p>Please check with the below credential.</p><p><h2><b>Student_id - {unique_student_id}</b></h2></p><p><h2><b>Username - {username}</b></h2></p><p>if you have any concerns regarding your account security, be sure to get in touch with our support team immediately at help@codescatter.com</p><p>Thank you for your cooperation.</p><p>Best regards,<br>Codescatter</p>')
            flash("Data Added Successfully")
            return redirect(url_for('student_data_list', _external=True, _scheme=secure_type))
        else:
            return render_template("add-student.html",type=type, admin_id=admin_id, photo_link=photo_student_link, allcountrycode=allcountrycode, allcity=allcity, allstate=allstate, allcountry=allcountry, allbatchyear=allbatchyear)

    except Exception as e:
        return redirect(url_for('student_register', _external=True, _scheme=secure_type))













@app.route("/teacher_register", methods=["GET", "POST"])
def teacher_register():
    """
    Handling teacher register process
    :return: teacher register template
    """
    try:
        db = client["college_management"]
        allcity = ["ahmedabad", "surat", "jamnagar", "junagadh", "navsari", "bhavnagar"]
        allstate = ["gujarat", "karnataka", "keral", "delhi", "rajasthan"]
        allcountry = ["USA", "UK", "IN", "CA"]
        allqualification = ["MBA", "ME", "BCA", "MCA", "BBA"]
        alldepartment = ["Computer", "Information & Technology", "Mechenical", "Civil"]
        allsubjects = ["PDA", "ES", "OOPS"]
        allcountrycode = ["+91", "+221"]
        if request.method == "POST":
            first_name = request.form["first_name"]
            last_name = request.form["last_name"]
            username = request.form["username"]
            password = request.form["password"]
            dob = request.form["dob"]
            gender = request.form["gender"]
            countrycode = request.form["countrycode"]
            contact_no = request.form["contact_no"]
            emergency_contact_no = request.form["emer_contact_no"]
            email = request.form["email"]
            address = request.form["address"]
            city = request.form["city"]
            state = request.form["state"]
            country = request.form["country"]
            qualification = request.form["qualification"]
            department = request.form["department"]
            subject = request.form["subject"]
            joining_date = request.form["joining_date"]
            contact_no = countrycode + " " + contact_no
            emergency_contact_no = countrycode + " " + emergency_contact_no

            all_teacher_data = find_all_data(app, db, "teacher_data")
            get_all_username = [te_data["username"] for te_data in all_teacher_data]
            if username in get_all_username:
                flash("Username already exits. Please try with different Username")
                return render_template("teacher_register.html", allcountrycode=allcountrycode, allcity=allcity, allstate=allstate,
                                       allcountry=allcountry, allqualification=allqualification, allsubjects=allsubjects, alldepartment=alldepartment,
                                       first_name=first_name, last_name=last_name, password=password, dob=dob, gender=gender, contact_no=contact_no,
                                       emergency_contact_no=emergency_contact_no, email=email,
                                       address=address, joining_date=joining_date)

            # password validation
            if not password_validation(app=app, password=password):
                flash("Please choose strong password. Add at least 1 special character, number, capitalize latter..")
                return render_template("teacher_register.html", allcountrycode=allcountrycode, allcity=allcity, allstate=allstate,
                                       allcountry=allcountry, allqualification=allqualification, allsubjects=allsubjects, alldepartment=alldepartment,
                                       first_name=first_name, last_name=last_name, username=username, dob=dob, gender=gender, contact_no=contact_no,
                                       emergency_contact_no=emergency_contact_no, email=email,
                                       address=address, joining_date=joining_date)

            # contact number and emergency contact number validation
            get_phone_val = validate_phone_number(app=app, phone_number=contact_no)
            get_emergency_phone_val = validate_phone_number(app, emergency_contact_no)
            if get_phone_val == "invalid number":
                flash("Please enter correct contact no.")
                return render_template("teacher_register.html", allcountrycode=allcountrycode, allcity=allcity,
                                       allstate=allstate,
                                       allcountry=allcountry, allqualification=allqualification,
                                       allsubjects=allsubjects, alldepartment=alldepartment,
                                       first_name=first_name, last_name=last_name, username=username, dob=dob,
                                       gender=gender, password=password,
                                       emergency_contact_no=emergency_contact_no, email=email,
                                       address=address, joining_date=joining_date)

            if get_emergency_phone_val == "invalid number":
                flash("Please enter correct emergency contact no.")
                return render_template("teacher_register.html", allcountrycode=allcountrycode, allcity=allcity,
                                       allstate=allstate,
                                       allcountry=allcountry, allqualification=allqualification,
                                       allsubjects=allsubjects, alldepartment=alldepartment,
                                       first_name=first_name, last_name=last_name, username=username, dob=dob,
                                       gender=gender, password=password,
                                       contact_no=contact_no, email=email,
                                       address=address, joining_date=joining_date)

            # teacher id validation
            all_teacher_data = find_spec_data(app, db, "login_mapping", {"type": "teacher"})
            get_all_teacher_id = [ta_data["teacher_id"] for ta_data in all_teacher_data]
            unique_teacher_id = get_unique_teacher_id(app, get_all_teacher_id)
            session["register_dict"] = {
                "teacher_id": unique_teacher_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "password": password,
                "dob": dob,
                "gender": gender,
                "contact_no": contact_no,
                "emergency_contact_no": emergency_contact_no,
                "email": email,
                "address": address,
                "city": city,
                "state": state,
                "country": country,
                "qualification": qualification,
                "department": department,
                "subject": subject,
                "joining_date": joining_date,
                "type": "teacher",
                "inserted_on": get_timestamp(app),
                "updated_on": get_timestamp(app)
            }

            return redirect(url_for('otp_verification', _external=True, _scheme=secure_type))
        else:
            return render_template("teacher_register.html", allcountrycode=allcountrycode, allcity=allcity, allstate=allstate, allcountry=allcountry, allqualification=allqualification, allsubjects=allsubjects, alldepartment=alldepartment)

    except Exception as e:
        return redirect(url_for('teacher_register', _external=True, _scheme=secure_type))

@app.route("/student_dashboard", methods=["GET", "POST"])
def student_dashboard():
    """
    That funcation can use otp_verification and new_password set link generate
    """

    try:
        login_dict = session.get("login_dict", "nothing")
        if login_dict != "nothing":
            type = login_dict["type"]
            id = login_dict["id"]
        else:
            type="Anonymous"
            id="anonymous"
        return render_template("student-dashboard.html", student_id=id, type=type)

    except Exception as e:
        flash("Please try again.......................................")
        return redirect(url_for('verification', _external=True, _scheme=secure_type))

@app.route("/teacher_dashboard", methods=["GET", "POST"])
def teacher_dashboard():
    """
    That funcation can use otp_verification and new_password set link generate
    """

    try:
        login_dict = session.get("login_dict", "nothing")
        if login_dict != "nothing":
            type = login_dict["type"]
            id = login_dict["id"]
        else:
            type = "Anonymous"
            id = "anonymous"
        return render_template("teacher-dashboard.html", teacher_id=id, type=type)

    except Exception as e:
        flash("Please try again.......................................")
        return redirect(url_for('verification', _external=True, _scheme=secure_type))

@app.route("/admin/teacher_data", methods=["GET", "POST"])
def teacher_data_list():
    """
    That funcation can use show all students data from admin panel
    """

    try:
        all_keys, all_values = get_admin_data(app, client, "college_management", "teacher_data")
        return render_template("teachers.html", all_keys=all_keys, all_values=all_values)

    except Exception as e:
        flash("Please try again.......................................")
        return redirect(url_for('teacher_data_list', _external=True, _scheme=secure_type))


if __name__ == "__main__":
    app.run(debug=True) ## Need to remove this line before commit
    app.run(host="0.0.0.0", port=constant_data.get("app_port_number", 7910))