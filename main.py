"""
    In this file handling all flask api route and maintain all of operation and sessions
"""

from flask import (flash, Flask, redirect, render_template, request,
                   session, url_for, send_file)
import os
from flask_cors import CORS
import json
from constant import constant_data
from operations.mongo_connection import (mongo_connect, data_added, find_all_data, find_spec_data, update_mongo_data,
                                         delete_data)
from operations.common_func import (file_check,export_student_panel_data, get_student_data, import_data_into_database, search_panel_data, delete_all_panel_data,
                                    get_unique_subject_id, export_teacher_panel_data, export_panel_data, delete_panel_data,
                                    get_unique_department_id,get_profile_data,
                                    get_unique_admin_id, get_admin_data, validate_phone_number, password_validation,
                                    logger_con, get_timestamp, get_unique_student_id,
                                    get_unique_teacher_id, get_all_country_state_names, check_dirs, create_query_list,
                                    update_rejected_data_file, delete_teacher_panel_data)
import random
from flask_mail import Mail
import pandas as pd
from flask_ngrok import run_with_ngrok
from werkzeug.utils import secure_filename

# create a flask app instance
app = Flask(__name__)

# Apply cors policy in our app instance
CORS(app)
# run_with_ngrok(app)

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
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["IMPORT_UPLOAD_FOLDER"] = 'static/uploads/import_file/'
app.config['REJECTED_DATA_UPLOAD_FOLDER'] = 'static/uploads/rejected_data/'

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
            if type == "student":
                return redirect(url_for('student_dashboard', _external=True, _scheme=secure_type))
            elif type == "teacher":
                return redirect(url_for('teacher_dashboard', _external=True, _scheme=secure_type))
            else:
                return redirect(url_for('admin_dashboard', _external=True, _scheme=secure_type))

        db = client["college_management"]
        all_types = ["Teacher", "Student", "Admin"]
        if request.method == "POST":
            email = request.form["email"]
            password = request.form["password"]

            di = {"username": email, "password": password}
            di_email = {"email": email, "password": password}
            teacher_data = find_spec_data(app, db, "login_mapping", di)
            teacher_data_email = find_spec_data(app, db, "login_mapping", di_email)
            teacher_data = list(teacher_data)
            teacher_data_email = list(teacher_data_email)
            if len(teacher_data) == 0 and len(teacher_data_email) == 0:
                flash("Please use correct credential..")
                return render_template("login.html", all_types=all_types)
            elif len(teacher_data)>0:
                teacher_data = teacher_data[0]
                id = teacher_data["username"]
                type = teacher_data["type"]
                photo_link = teacher_data["photo_link"]
                session["login_dict"] = {"id": id, "type": type, "photo_link":photo_link}
                return redirect(url_for(f'{type}_dashboard', _external=True, _scheme=secure_type))
            else:
                teacher_data_email = teacher_data_email[0]
                id = teacher_data_email["username"]
                type = teacher_data_email["type"]
                photo_link = teacher_data_email["photo_link"]
                session["login_dict"] = {"id": id, "type": type, "photo_link": photo_link}
                return redirect(url_for(f'{type}_dashboard', _external=True, _scheme=secure_type))

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


########################## Admin Operation Route ####################################

@app.route('/get_province')
def get_province():
    city_province_mapping = constant_data.get("city_province_mapping", {})
    city = request.args.get('city')
    province = city_province_mapping.get(city, 'Unknown')
    print(province)
    return province

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
            delete_dict["admin_id"] = id
            delete_dict["type"] = "admin"
            delete_panel_data(app, client, "college_management", coll_name, delete_dict)
            return redirect(url_for('admin_data_list', _external=True, _scheme=secure_type))
        elif panel == "student":
            delete_dict["student_id"] = id
            delete_dict["type"] = "student"
            coll_name = "students_data"
            delete_panel_data(app, client, "college_management", coll_name, delete_dict)
            return redirect(url_for('student_data_list', _external=True, _scheme=secure_type))
        elif panel == "department":
            delete_dict["department_id"] = id
            coll_name = "department_data"
            delete_panel_data(app, client, "college_management", coll_name, delete_dict)
            return redirect(url_for('department_data_list', _external=True, _scheme=secure_type))
        elif panel == "subject":
            delete_dict["subject_id"] = id
            coll_name = "subject_data"
            delete_panel_data(app, client, "college_management", coll_name, delete_dict)
            return redirect(url_for('subject_data_list', _external=True, _scheme=secure_type))
        else:
            delete_dict["teacher_id"] = id
            delete_dict["type"] = "teacher"
            coll_name = "teacher_data"
            delete_panel_data(app, client, "college_management", coll_name, delete_dict)
            return redirect(url_for('teacher_data_list', _external=True, _scheme=secure_type))


    except Exception as e:
        app.logger.debug(f"Error in delete data from database: {e}")
        flash("Please try again...")
        return redirect(url_for('delete_data', _external=True, _scheme=secure_type))


@app.route("/admin/deleteall/<object>", methods=["GET", "POST"])
def delete_all_data(object):
    """
    That funcation can use delete from student, teacher and admin from admin panel
    """

    try:
        panel = object
        panel_mapping = {
            "admin": ("admin_data", "admin_data_list"),
            "student": ("students_data", "student_data_list"),
            "department": ("department_data", "department_data_list"),
            "subject": ("subject_data", "subject_data_list"),
        }

        coll_name, data_list = panel_mapping.get(panel, ("teacher_data", "teacher_data_list"))
        delete_result = delete_all_panel_data(app, client, "college_management", coll_name, panel)
        if delete_result:
            flash("All data deleted successfully")
            return redirect(url_for(data_list, _external=True, _scheme=secure_type))
        else:
            flash("All records deleted...")
            return redirect(url_for(data_list, _external=True, _scheme=secure_type))
    except Exception as e:
        app.logger.debug(f"Error in delete data from database: {e}")
        flash("Please try again...")
        return redirect(url_for('delete_all_data', _external=True, _scheme=secure_type))


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
        elif panel == "department":
            res = find_all_data(app, db, "department_data")
            all_data = []
            for each_res in res:
                del each_res["_id"]
                all_data.append(each_res)
            output_path = export_panel_data(app, all_data, panel, type)
            return send_file(output_path, as_attachment=True)
        elif panel == "subject":
            res = find_all_data(app, db, "subject_data")
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


@app.route("/admin/import_data/<panel_obj>", methods=["GET", "POST"])
def import_data(panel_obj):
    """
    That funcation can use delete from student, teacher and admin from admin panel
    """

    try:
        db = client["college_management"]
        ## Check if panel object is in the mapping and request method is POST
        ## If yes, then it will store the id type in a variable with which it will be checking for present record
        if request.method == "POST":
            ## Getting file from request
            file = request.files["file"]
            ## Checking if file is selected, if yes, secure the filename
            if file.filename != "":
                ## Securing file and getting file extension
                file_name = secure_filename(file.filename)
                if not os.path.isdir(app.config['IMPORT_UPLOAD_FOLDER']):
                    os.makedirs(app.config['IMPORT_UPLOAD_FOLDER'], exist_ok=True)
                if not os.path.exists(app.config['REJECTED_DATA_UPLOAD_FOLDER']):
                    os.makedirs(app.config['REJECTED_DATA_UPLOAD_FOLDER'], exist_ok=True)
                file_path = os.path.join(app.config['IMPORT_UPLOAD_FOLDER'], file_name)
                file.save(file_path)
                file_extension = os.path.splitext(file_name)[1]

                if file_extension == ".xlsx":
                    dataload_excel = pd.read_excel(file_path)
                    json_record_data = dataload_excel.to_json(orient='records')
                    json_data = json.loads(json_record_data)
                elif file_extension == ".csv":
                    dataload = pd.read_csv(file_path)
                    json_record_data = dataload.to_json(orient='records')
                    json_data = json.loads(json_record_data)
                else:
                    with open(file_path, encoding='utf-8') as json_file:
                        json_data = json.load(json_file)


                flag = False
                if panel_obj == "admin":
                    get_admin_data = find_all_data(app, db, "admin_data")
                    get_login_data = find_all_data(app, db, "login_mapping")
                    all_login_data = []
                    for login_data in get_login_data:
                        del login_data["_id"]
                        all_login_data.append(login_data)
                    all_admin_data = []
                    for admin_data in get_admin_data:
                        del admin_data["_id"]
                        all_admin_data.append(admin_data)
                    for record in json_data:
                        record["admin_id"] = str(record["admin_id"])
                        make_dict = {}
                        make_dict["photo_link"] = record["photo_link"]
                        make_dict["admin_id"] = str(record["admin_id"])
                        make_dict["username"] = record["username"]
                        make_dict["email"] = record["email"]
                        make_dict["password"] = record["password"]
                        make_dict["type"] = "admin"
                        if make_dict not in all_login_data:
                            make_dict["photo_link"] = "static/assets/img/profiles/avatar-01.jpg"
                            data_added(app, db, "login_mapping", make_dict)
                            coll = db["admin_data"]
                            if record not in all_admin_data:
                                record["photo_link"] = "static/assets/img/profiles/avatar-01.jpg"
                                coll.insert_one(record)
                        else:
                            flag = True
                    if flag:
                        flash("Your some data is not valid so that data is not imported..")
                    return redirect(f'/admin/{panel_obj}_data')
                elif panel_obj == "student":
                    get_student_data = find_all_data(app, db, "students_data")
                    get_login_data = find_all_data(app, db, "login_mapping")
                    all_login_data = []
                    for login_data in get_login_data:
                        del login_data["_id"]
                        all_login_data.append(login_data)
                    all_student_data = []
                    for student_data in get_student_data:
                        del student_data["_id"]
                        all_student_data.append(student_data)
                    print(all_student_data)
                    for record in json_data:
                        record["photo_link"] = "static/assets/img/profiles/avatar-01.jpg"
                        record["student_id"] = str(record["student_id"])
                        make_dict = {}
                        make_dict["photo_link"] = "static/assets/img/profiles/avatar-01.jpg"
                        make_dict["student_id"] = str(record["student_id"])
                        make_dict["username"] = record["username"]
                        make_dict["email"] = record["email"]
                        make_dict["password"] = record["password"]
                        make_dict["type"] = "student"
                        print(make_dict)
                        if make_dict not in all_login_data:
                            data_added(app, db, "login_mapping", make_dict)
                            print(record)
                            class_mapping = {}
                            class_mapping["student_id"] = str(record["student_id"])
                            class_mapping["department"] = record["department"]
                            class_mapping["class_name"] = record["classes"]
                            class_mapping["type"] = "student"
                            coll = db["class_data"]
                            coll.insert_one(class_mapping)
                            coll = db["students_data"]
                            if record not in all_student_data:
                                coll.insert_one(record)
                        else:
                            flag = True
                    if flag:
                        flash("Your some data is not valid so that data is not imported..")
                    return redirect(f'/admin/{panel_obj}_data')
                elif panel_obj == "teacher":
                    get_teacher_data = find_all_data(app, db, "teacher_data")
                    get_login_data = find_all_data(app, db, "login_mapping")
                    all_login_data = []
                    for login_data in get_login_data:
                        del login_data["_id"]
                        all_login_data.append(login_data)
                    all_teacher_data = []
                    for teacher_data in get_teacher_data:
                        del teacher_data["_id"]
                        all_teacher_data.append(teacher_data)
                    print(all_teacher_data)
                    for record in json_data:
                        record["photo_link"] = "static/assets/img/profiles/avatar-01.jpg"
                        record["teacher_id"] = str(record["teacher_id"])
                        make_dict = {}
                        make_dict["photo_link"] = "static/assets/img/profiles/avatar-01.jpg"
                        make_dict["teacher_id"] = str(record["teacher_id"])
                        make_dict["username"] = record["username"]
                        make_dict["email"] = record["email"]
                        make_dict["password"] = record["password"]
                        make_dict["type"] = "teacher"
                        print(make_dict)
                        if make_dict not in all_login_data:
                            data_added(app, db, "login_mapping", make_dict)
                            print(record)
                            subject_mapping_dict = {}
                            subject_mapping_dict["teacher_id"] = str(record["teacher_id"])
                            subject_mapping_dict["department_name"] = record["department"]
                            subject_mapping_dict["subject"] = record["subject"]
                            subject_mapping_dict["type"] = "teacher"
                            coll = db["subject_mapping"]
                            coll.insert_one(subject_mapping_dict)
                            coll = db["teacher_data"]
                            if record not in all_teacher_data:
                                coll.insert_one(record)
                        else:
                            flag = True
                    if flag:
                        flash("Your some data is not valid so that data is not imported..")
                    return redirect(f'/admin/{panel_obj}_data')
                elif panel_obj == "department":
                    get_department_data = find_all_data(app, db, "department_data")
                    all_department_data = []
                    for department_data in get_department_data:
                        del department_data["_id"]
                        all_department_data.append(department_data)
                    for record in json_data:
                        record["department_id"] = str(record["department_id"])
                        coll = db["department_data"]
                        print(all_department_data)
                        if record not in all_department_data:
                            print(record)
                            coll.insert_one(record)
                        else:
                            flag=True
                    if flag:
                        flash("Your some data is not valid so that data is not imported..")
                    return redirect(f'/admin/{panel_obj}_data')
                elif panel_obj == "subject":
                    get_subject_data = find_all_data(app, db, "subject_data")
                    all_subject_data = []
                    for subject_data in get_subject_data:
                        del subject_data["_id"]
                        all_subject_data.append(subject_data)
                    for record in json_data:
                        record["subject_id"] = str(record["subject_id"])
                        coll = db["subject_data"]
                        if record not in all_subject_data:
                            coll.insert_one(record)
                        else:
                            flag=True
                    if flag:
                        flash("Your some data is not valid so that data is not imported..")
                    return redirect(f'/admin/{panel_obj}_data')

            else:
                flash("No file selected, please select a file")
            if panel_obj == "class":
                return render_template(f'{panel_obj}es.html')
            return render_template(f'{panel_obj}s.html')

    except Exception as e:
        app.logger.debug(f"Error in export data from database: {e}")
        print(f"Error in export data from database: {e}")
        flash("Please try again...")
        if panel_obj == "class":
            return render_template(f'{panel_obj}es.html')
        return render_template(f'{panel_obj}s.html')


@app.route("/admin/edit_data/<object>", methods=["GET", "POST"])
def edit_data(object):
    """
    That funcation can use delete from student, teacher and admin from admin panel
    """

    try:
        # We can directly assign values to panel and id variable
        panel, id = object.split("-")
        edit_dict = {}

        # Define a mapping of panel to collection and search dictionary
        panel_mapping = {
            "admin": ("admin_data", {"admin_id": id, "type": "admin"}),
            "student": ("students_data", {"student_id": id, "type": "student"}),
            "teacher": ("teacher_data", {"teacher_id": id, "type": "teacher"}),
        }

        # Check if panel is in the mapping
        # If it is, get the collection and search dictionary``
        if panel in panel_mapping:
            coll_name, edit_dict = panel_mapping[panel]
            search_value = panel + "_id|" + id
            edit_dict = search_panel_data(app, client, "college_management", search_value, coll_name)
            print(f"Search dictionary is : {edit_dict}")
            html_page_name = f"add-{panel}.html"
        # If it is not, set a flash message and return to the previous screen
        else:
            flash("Please try again...")
            html_page_name = f"{panel}s.html"
        print(f"Rendered html page is : {html_page_name}")
        country_code, contact = edit_dict["contact_no"].split(" ")
        return render_template(html_page_name,
                               first_name=edit_dict["first_name"],
                               last_name=edit_dict["last_name"],
                               username=edit_dict["username"],
                               password=edit_dict["password"],
                               dob=edit_dict["dob"],
                               gender=edit_dict["gender"],
                               countrycode=country_code,
                               contact_no=contact,
                               emergency_contact_no=edit_dict["emergency_contact_no"],
                               email=edit_dict["email"],
                               address=edit_dict["address"],
                               admission_date=edit_dict["admission_date"],
                               city=edit_dict["city"],
                               state=edit_dict["state"],
                               country=edit_dict["country"],
                               department=edit_dict["department"],
                               classes=edit_dict["classes"],
                               batch_year=edit_dict["batch_year"])

    except Exception as e:
        app.logger.debug(f"Error in edit data from database: {e}")
        flash("Please try again...")
        print(e)
        panel = object.split("-")[0]
        return render_template(f'{panel}s.html')


@app.route("/search_data/<object>", methods=["GET", "POST"])
def search_data(object):
    """
    That funcation can use search data from student, teacher and admin from admin panel
    """

    try:
        login_dict = session.get("login_dict", "nothing")
        type = login_dict["type"]
        admin_id = login_dict["id"]
        photo_link = "/" + login_dict["photo_link"]
        panel = object
        search_dict = {}
        id = request.form.get('id', '')
        username = request.form.get('username', '')
        contact_no = request.form.get('contact_no', '')
        email = request.form.get('email', '')
        panel_mapping = {
            "admin": "admin_data",
            "student": "students_data",
            "teacher": "teacher_data",
            "department": "department_data",
            "subject": "subject_data",
            "class": "class_data",
        }
        if panel in panel_mapping:
            print("Panel is in the mapping")
            if panel in ["admin", "student", "teacher"]:
                if id:
                    search_value = f'{panel}_id|{id}'
                elif username:
                    search_value = f'username|{username}'
                elif contact_no:
                    search_value = f'contact_no|{contact_no}'
                elif email:
                    search_value = f'email|{email}'
                else:
                    app.logger.debug(f"Search field is invalid, please try with some other field...")
                    if panel == "class":
                        return render_template(f'{panel}es.html')
                    return render_template(f'{panel}s.html')
            else:
                if id:
                    search_value = f'{panel}_id|{id}'
                elif username:
                    search_value = f'department_name|{username}'
                elif contact_no and panel in ["class"]:
                    search_value = f'class_name|{contact_no}'
                else:
                    app.logger.debug(f"Search field is invalid, please try with some other field...")
                    if panel == "class":
                        return render_template(f'{panel}es.html')
                    return render_template(f'{panel}s.html')
            coll_name = panel_mapping[panel]
            print(f"Search value is : {search_value}, coll_name is : {coll_name}")
            search_dict = search_panel_data(app, client, "college_management", search_value, coll_name)
        else:
            print("Panel is not in the mapping")
            app.logger.debug(f"Error in searching data from database")
        return render_template('search_result.html', panel=panel, search_dict=search_dict, type=type, admin_id=admin_id, photo_link=photo_link)

    except Exception as e:
        app.logger.debug(f"Error in searching data from database: {e}")
        print(e)
        flash("Please try again...")
        panel = object
        if panel == "class":
            return render_template(f'{panel}es.html')
        return render_template(f'{panel}s.html')


########################## Student Operation Route ####################################

@app.route("/student/delete_data/<object>", methods=["GET", "POST"])
def student_delete_data(object):
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
            delete_dict["admin_id"] = id
            delete_dict["type"] = "admin"
            delete_panel_data(app, client, "college_management", coll_name, delete_dict)
            return redirect(url_for('admin_data_list', _external=True, _scheme=secure_type))
        elif panel == "student":
            delete_dict["student_id"] = id
            delete_dict["type"] = "student"
            coll_name = "students_data"
            delete_panel_data(app, client, "college_management", coll_name, delete_dict)
            return redirect(url_for('student_data_list', _external=True, _scheme=secure_type))
        elif panel == "department":
            delete_dict["department_id"] = id
            coll_name = "department_data"
            delete_panel_data(app, client, "college_management", coll_name, delete_dict)
            return redirect(url_for('department_data_list', _external=True, _scheme=secure_type))
        elif panel == "subject":
            delete_dict["subject_id"] = id
            coll_name = "subject_data"
            delete_panel_data(app, client, "college_management", coll_name, delete_dict)
            return redirect(url_for('subject_data_list', _external=True, _scheme=secure_type))
        else:
            delete_dict["teacher_id"] = id
            delete_dict["type"] = "teacher"
            coll_name = "teacher_data"
            delete_panel_data(app, client, "college_management", coll_name, delete_dict)
            return redirect(url_for('teacher_data_list', _external=True, _scheme=secure_type))


    except Exception as e:
        app.logger.debug(f"Error in delete data from database: {e}")
        flash("Please try again...")
        return redirect(url_for('delete_data', _external=True, _scheme=secure_type))


@app.route("/student/deleteall/<object>", methods=["GET", "POST"])
def student_delete_all_data(object):
    """
    That funcation can use delete from student, teacher and admin from admin panel
    """

    try:
        panel = object
        panel_mapping = {
            "admin": ("admin_data", "admin_data_list"),
            "student": ("students_data", "student_data_list"),
            "department": ("department_data", "department_data_list"),
            "subject": ("subject_data", "subject_data_list"),
        }

        coll_name, data_list = panel_mapping.get(panel, ("teacher_data", "teacher_data_list"))
        delete_result = delete_all_panel_data(app, client, "college_management", coll_name, panel)
        if delete_result:
            flash("All data deleted successfully")
            return redirect(url_for(data_list, _external=True, _scheme=secure_type))
        else:
            flash("All records deleted...")
            return redirect(url_for(data_list, _external=True, _scheme=secure_type))
    except Exception as e:
        app.logger.debug(f"Error in delete data from database: {e}")
        flash("Please try again...")
        return redirect(url_for('delete_all_data', _external=True, _scheme=secure_type))


@app.route("/student/export/<object>", methods=["GET", "POST"])
def student_export_data(object):
    """
    That funcation can use delete from student, teacher and admin from admin panel
    """

    try:
        db = client["college_management"]
        spliting_object = object.split("-")
        panel = spliting_object[0]
        username = spliting_object[1]
        type = spliting_object[2]
        if panel == "attendance":
            res = find_spec_data(app, db, "attendance_data", {"student": username})
            all_data = []
            for each_res in res:
                del each_res["_id"]
                all_data.append(each_res)
            output_path = export_student_panel_data(app, all_data, panel, type)
            return send_file(output_path, as_attachment=True)



    except Exception as e:
        app.logger.debug(f"Error in export data from database: {e}")
        flash("Please try again...")
        return redirect(url_for('student_export_data', _external=True, _scheme=secure_type))


@app.route("/student/import_data/<panel_obj>", methods=["GET", "POST"])
def student_import_data(panel_obj):
    """
    That funcation can use delete from student, teacher and admin from admin panel
    """

    try:
        db = client["college_management"]
        ## Check if panel object is in the mapping and request method is POST
        ## If yes, then it will store the id type in a variable with which it will be checking for present record
        if request.method == "POST":
            ## Getting file from request
            file = request.files["file"]
            ## Checking if file is selected, if yes, secure the filename
            if file.filename != "":
                ## Securing file and getting file extension
                file_name = secure_filename(file.filename)
                if not os.path.isdir(app.config['IMPORT_UPLOAD_FOLDER']):
                    os.makedirs(app.config['IMPORT_UPLOAD_FOLDER'], exist_ok=True)
                if not os.path.exists(app.config['REJECTED_DATA_UPLOAD_FOLDER']):
                    os.makedirs(app.config['REJECTED_DATA_UPLOAD_FOLDER'], exist_ok=True)
                file_path = os.path.join(app.config['IMPORT_UPLOAD_FOLDER'], file_name)
                file.save(file_path)
                file_extension = os.path.splitext(file_name)[1]

                if file_extension == ".xlsx":
                    dataload_excel = pd.read_excel(file_path)
                    json_record_data = dataload_excel.to_json(orient='records')
                    json_data = json.loads(json_record_data)
                elif file_extension == ".csv":
                    dataload = pd.read_csv(file_path)
                    json_record_data = dataload.to_json(orient='records')
                    json_data = json.loads(json_record_data)
                else:
                    with open(file_path, encoding='utf-8') as json_file:
                        json_data = json.load(json_file)


                flag = False
                if panel_obj == "admin":
                    get_admin_data = find_all_data(app, db, "admin_data")
                    get_login_data = find_all_data(app, db, "login_mapping")
                    all_login_data = []
                    for login_data in get_login_data:
                        del login_data["_id"]
                        all_login_data.append(login_data)
                    all_admin_data = []
                    for admin_data in get_admin_data:
                        del admin_data["_id"]
                        all_admin_data.append(admin_data)
                    for record in json_data:
                        record["admin_id"] = str(record["admin_id"])
                        make_dict = {}
                        make_dict["photo_link"] = record["photo_link"]
                        make_dict["admin_id"] = str(record["admin_id"])
                        make_dict["username"] = record["username"]
                        make_dict["email"] = record["email"]
                        make_dict["password"] = record["password"]
                        make_dict["type"] = "admin"
                        if make_dict not in all_login_data:
                            make_dict["photo_link"] = "static/assets/img/profiles/avatar-01.jpg"
                            data_added(app, db, "login_mapping", make_dict)
                            coll = db["admin_data"]
                            if record not in all_admin_data:
                                record["photo_link"] = "static/assets/img/profiles/avatar-01.jpg"
                                coll.insert_one(record)
                        else:
                            flag = True
                    if flag:
                        flash("Your some data is not valid so that data is not imported..")
                    return redirect(f'/admin/{panel_obj}_data')
                elif panel_obj == "student":
                    get_student_data = find_all_data(app, db, "students_data")
                    get_login_data = find_all_data(app, db, "login_mapping")
                    all_login_data = []
                    for login_data in get_login_data:
                        del login_data["_id"]
                        all_login_data.append(login_data)
                    all_student_data = []
                    for student_data in get_student_data:
                        del student_data["_id"]
                        all_student_data.append(student_data)
                    print(all_student_data)
                    for record in json_data:
                        record["photo_link"] = "static/assets/img/profiles/avatar-01.jpg"
                        record["student_id"] = str(record["student_id"])
                        make_dict = {}
                        make_dict["photo_link"] = "static/assets/img/profiles/avatar-01.jpg"
                        make_dict["student_id"] = str(record["student_id"])
                        make_dict["username"] = record["username"]
                        make_dict["email"] = record["email"]
                        make_dict["password"] = record["password"]
                        make_dict["type"] = "student"
                        print(make_dict)
                        if make_dict not in all_login_data:
                            data_added(app, db, "login_mapping", make_dict)
                            print(record)
                            class_mapping = {}
                            class_mapping["student_id"] = str(record["student_id"])
                            class_mapping["department"] = record["department"]
                            class_mapping["class_name"] = record["classes"]
                            class_mapping["type"] = "student"
                            coll = db["class_data"]
                            coll.insert_one(class_mapping)
                            coll = db["students_data"]
                            if record not in all_student_data:
                                coll.insert_one(record)
                        else:
                            flag = True
                    if flag:
                        flash("Your some data is not valid so that data is not imported..")
                    return redirect(f'/admin/{panel_obj}_data')
                elif panel_obj == "teacher":
                    get_teacher_data = find_all_data(app, db, "teacher_data")
                    get_login_data = find_all_data(app, db, "login_mapping")
                    all_login_data = []
                    for login_data in get_login_data:
                        del login_data["_id"]
                        all_login_data.append(login_data)
                    all_teacher_data = []
                    for teacher_data in get_teacher_data:
                        del teacher_data["_id"]
                        all_teacher_data.append(teacher_data)
                    print(all_teacher_data)
                    for record in json_data:
                        record["photo_link"] = "static/assets/img/profiles/avatar-01.jpg"
                        record["teacher_id"] = str(record["teacher_id"])
                        make_dict = {}
                        make_dict["photo_link"] = "static/assets/img/profiles/avatar-01.jpg"
                        make_dict["teacher_id"] = str(record["teacher_id"])
                        make_dict["username"] = record["username"]
                        make_dict["email"] = record["email"]
                        make_dict["password"] = record["password"]
                        make_dict["type"] = "teacher"
                        print(make_dict)
                        if make_dict not in all_login_data:
                            data_added(app, db, "login_mapping", make_dict)
                            print(record)
                            subject_mapping_dict = {}
                            subject_mapping_dict["teacher_id"] = str(record["teacher_id"])
                            subject_mapping_dict["department_name"] = record["department"]
                            subject_mapping_dict["subject"] = record["subject"]
                            subject_mapping_dict["type"] = "teacher"
                            coll = db["subject_mapping"]
                            coll.insert_one(subject_mapping_dict)
                            coll = db["teacher_data"]
                            if record not in all_teacher_data:
                                coll.insert_one(record)
                        else:
                            flag = True
                    if flag:
                        flash("Your some data is not valid so that data is not imported..")
                    return redirect(f'/admin/{panel_obj}_data')
                elif panel_obj == "department":
                    get_department_data = find_all_data(app, db, "department_data")
                    all_department_data = []
                    for department_data in get_department_data:
                        del department_data["_id"]
                        all_department_data.append(department_data)
                    for record in json_data:
                        record["department_id"] = str(record["department_id"])
                        coll = db["department_data"]
                        print(all_department_data)
                        if record not in all_department_data:
                            print(record)
                            coll.insert_one(record)
                        else:
                            flag=True
                    if flag:
                        flash("Your some data is not valid so that data is not imported..")
                    return redirect(f'/admin/{panel_obj}_data')
                elif panel_obj == "subject":
                    get_subject_data = find_all_data(app, db, "subject_data")
                    all_subject_data = []
                    for subject_data in get_subject_data:
                        del subject_data["_id"]
                        all_subject_data.append(subject_data)
                    for record in json_data:
                        record["subject_id"] = str(record["subject_id"])
                        coll = db["subject_data"]
                        if record not in all_subject_data:
                            coll.insert_one(record)
                        else:
                            flag=True
                    if flag:
                        flash("Your some data is not valid so that data is not imported..")
                    return redirect(f'/admin/{panel_obj}_data')

            else:
                flash("No file selected, please select a file")
            if panel_obj == "class":
                return render_template(f'{panel_obj}es.html')
            return render_template(f'{panel_obj}s.html')

    except Exception as e:
        app.logger.debug(f"Error in export data from database: {e}")
        print(f"Error in export data from database: {e}")
        flash("Please try again...")
        if panel_obj == "class":
            return render_template(f'{panel_obj}es.html')
        return render_template(f'{panel_obj}s.html')


@app.route("/student/edit_data/<object>", methods=["GET", "POST"])
def student_edit_data(object):
    """
    That funcation can use delete from student, teacher and admin from admin panel
    """

    try:
        # We can directly assign values to panel and id variable
        panel, id = object.split("-")
        edit_dict = {}

        # Define a mapping of panel to collection and search dictionary
        panel_mapping = {
            "admin": ("admin_data", {"admin_id": id, "type": "admin"}),
            "student": ("students_data", {"student_id": id, "type": "student"}),
            "teacher": ("teacher_data", {"teacher_id": id, "type": "teacher"}),
        }

        # Check if panel is in the mapping
        # If it is, get the collection and search dictionary``
        if panel in panel_mapping:
            coll_name, edit_dict = panel_mapping[panel]
            search_value = panel + "_id|" + id
            edit_dict = search_panel_data(app, client, "college_management", search_value, coll_name)
            print(f"Search dictionary is : {edit_dict}")
            html_page_name = f"add-{panel}.html"
        # If it is not, set a flash message and return to the previous screen
        else:
            flash("Please try again...")
            html_page_name = f"{panel}s.html"
        print(f"Rendered html page is : {html_page_name}")
        country_code, contact = edit_dict["contact_no"].split(" ")
        return render_template(html_page_name,
                               first_name=edit_dict["first_name"],
                               last_name=edit_dict["last_name"],
                               username=edit_dict["username"],
                               password=edit_dict["password"],
                               dob=edit_dict["dob"],
                               gender=edit_dict["gender"],
                               countrycode=country_code,
                               contact_no=contact,
                               emergency_contact_no=edit_dict["emergency_contact_no"],
                               email=edit_dict["email"],
                               address=edit_dict["address"],
                               admission_date=edit_dict["admission_date"],
                               city=edit_dict["city"],
                               state=edit_dict["state"],
                               country=edit_dict["country"],
                               department=edit_dict["department"],
                               classes=edit_dict["classes"],
                               batch_year=edit_dict["batch_year"])

    except Exception as e:
        app.logger.debug(f"Error in edit data from database: {e}")
        flash("Please try again...")
        print(e)
        panel = object.split("-")[0]
        return render_template(f'{panel}s.html')

########################## Operation Route ####################################

@app.route("/teacher/delete_data/<object>", methods=["GET", "POST"])
def teacher_delete_data(object):
    """
    That funcation can use delete from student, teacher and admin from admin panel
    """

    try:
        spliting_object = object.split("*")
        panel = spliting_object[0]
        student = spliting_object[1]
        attendance_date = spliting_object[2]
        delete_dict = {}
        login_dict = session.get("login_dict", "nothing")
        if panel == "attendance":
            coll_name = "attendance_data"
            delete_dict["teacher_name"] = login_dict["id"]
            delete_dict["student"] = student
            delete_dict["attendance_date"] = attendance_date
            delete_teacher_panel_data(app, client, "college_management", coll_name, delete_dict)
            return redirect(url_for('attendance_data_list', _external=True, _scheme=secure_type))

    except Exception as e:
        app.logger.debug(f"Error in delete data from database: {e}")
        flash("Please try again...")
        return redirect(url_for('teacher_delete_data', _external=True, _scheme=secure_type))


@app.route("/teacher/deleteall/<object>", methods=["GET", "POST"])
def teacher_delete_all_data(object):
    """
    That funcation can use delete from student, teacher and admin from admin panel
    """

    try:
        panel = object
        panel_mapping = {
            "admin": ("admin_data", "admin_data_list"),
            "student": ("students_data", "student_data_list"),
            "department": ("department_data", "department_data_list"),
            "subject": ("subject_data", "subject_data_list"),
        }

        coll_name, data_list = panel_mapping.get(panel, ("teacher_data", "teacher_data_list"))
        delete_result = delete_all_panel_data(app, client, "college_management", coll_name, panel)
        if delete_result:
            flash("All data deleted successfully")
            return redirect(url_for(data_list, _external=True, _scheme=secure_type))
        else:
            flash("All records deleted...")
            return redirect(url_for(data_list, _external=True, _scheme=secure_type))
    except Exception as e:
        app.logger.debug(f"Error in delete data from database: {e}")
        flash("Please try again...")
        return redirect(url_for('delete_all_data', _external=True, _scheme=secure_type))


@app.route("/teacher/export/<object>", methods=["GET", "POST"])
def teacher_export_data(object):
    """
    That funcation can use delete from student, teacher and admin from admin panel
    """

    try:
        db = client["college_management"]
        spliting_object = object.split("-")
        panel = spliting_object[0]
        type = spliting_object[1]
        if panel == "attendance":
            res = find_all_data(app, db, "attendance_data")
            all_data = []
            for each_res in res:
                del each_res["_id"]
                all_data.append(each_res)
            output_path = export_teacher_panel_data(app, all_data, panel, type)
            return send_file(output_path, as_attachment=True)

    except Exception as e:
        app.logger.debug(f"Error in export data from database: {e}")
        flash("Please try again...")
        return redirect(url_for('export_data', _external=True, _scheme=secure_type))


@app.route("/teacher/import_data/<panel_obj>", methods=["GET", "POST"])
def teacher_import_data(panel_obj):
    """
    That funcation can use delete from student, teacher and admin from admin panel
    """

    try:
        db = client["college_management"]
        ## Check if panel object is in the mapping and request method is POST
        ## If yes, then it will store the id type in a variable with which it will be checking for present record
        if request.method == "POST":
            ## Getting file from request
            file = request.files["file"]
            ## Checking if file is selected, if yes, secure the filename
            if file.filename != "":
                ## Securing file and getting file extension
                file_name = secure_filename(file.filename)
                if not os.path.isdir(app.config['IMPORT_UPLOAD_FOLDER']):
                    os.makedirs(app.config['IMPORT_UPLOAD_FOLDER'], exist_ok=True)
                if not os.path.exists(app.config['REJECTED_DATA_UPLOAD_FOLDER']):
                    os.makedirs(app.config['REJECTED_DATA_UPLOAD_FOLDER'], exist_ok=True)
                file_path = os.path.join(app.config['IMPORT_UPLOAD_FOLDER'], file_name)
                file.save(file_path)
                file_extension = os.path.splitext(file_name)[1]

                if file_extension == ".xlsx":
                    dataload_excel = pd.read_excel(file_path)
                    json_record_data = dataload_excel.to_json(orient='records')
                    json_data = json.loads(json_record_data)
                elif file_extension == ".csv":
                    dataload = pd.read_csv(file_path)
                    json_record_data = dataload.to_json(orient='records')
                    json_data = json.loads(json_record_data)
                else:
                    with open(file_path, encoding='utf-8') as json_file:
                        json_data = json.load(json_file)


                flag = False
                if panel_obj == "attendance":
                    get_attendance_data = find_all_data(app, db, "attendance_data")
                    all_attendance_data = []
                    for attendance_data in get_attendance_data:
                        del attendance_data["_id"]
                        all_attendance_data.append(attendance_data)
                    for record in json_data:
                        record["reason"] = ""
                        coll = db["attendance_data"]
                        if record not in all_attendance_data:
                            coll.insert_one(record)
                        else:
                            flag = True
                    if flag:
                        flash("Your some data is not valid so that data is not imported..")
                    return redirect(f'/teacher/{panel_obj}_data')

            else:
                flash("No file selected, please select a file")
            return render_template(f'{panel_obj}s.html')

    except Exception as e:
        app.logger.debug(f"Error in export data from database: {e}")
        return render_template(f'{panel_obj}s.html')


@app.route("/teacher/edit_data/<object>", methods=["GET", "POST"])
def teacher_edit_data(object):
    """
    That funcation can use delete from student, teacher and admin from admin panel
    """

    try:
        # We can directly assign values to panel and id variable
        panel, id = object.split("-")
        edit_dict = {}

        # Define a mapping of panel to collection and search dictionary
        panel_mapping = {
            "admin": ("admin_data", {"admin_id": id, "type": "admin"}),
            "student": ("students_data", {"student_id": id, "type": "student"}),
            "teacher": ("teacher_data", {"teacher_id": id, "type": "teacher"}),
        }

        # Check if panel is in the mapping
        # If it is, get the collection and search dictionary``
        if panel in panel_mapping:
            coll_name, edit_dict = panel_mapping[panel]
            search_value = panel + "_id|" + id
            edit_dict = search_panel_data(app, client, "college_management", search_value, coll_name)
            print(f"Search dictionary is : {edit_dict}")
            html_page_name = f"add-{panel}.html"
        # If it is not, set a flash message and return to the previous screen
        else:
            flash("Please try again...")
            html_page_name = f"{panel}s.html"
        print(f"Rendered html page is : {html_page_name}")
        country_code, contact = edit_dict["contact_no"].split(" ")
        return render_template(html_page_name,
                               first_name=edit_dict["first_name"],
                               last_name=edit_dict["last_name"],
                               username=edit_dict["username"],
                               password=edit_dict["password"],
                               dob=edit_dict["dob"],
                               gender=edit_dict["gender"],
                               countrycode=country_code,
                               contact_no=contact,
                               emergency_contact_no=edit_dict["emergency_contact_no"],
                               email=edit_dict["email"],
                               address=edit_dict["address"],
                               admission_date=edit_dict["admission_date"],
                               city=edit_dict["city"],
                               state=edit_dict["state"],
                               country=edit_dict["country"],
                               department=edit_dict["department"],
                               classes=edit_dict["classes"],
                               batch_year=edit_dict["batch_year"])

    except Exception as e:
        app.logger.debug(f"Error in edit data from database: {e}")
        flash("Please try again...")
        print(e)
        panel = object.split("-")[0]
        return render_template(f'{panel}s.html')


@app.route("/search_data/<object>", methods=["GET", "POST"])
def teacher_search_data(object):
    """
    That funcation can use search data from student, teacher and admin from admin panel
    """

    try:
        login_dict = session.get("login_dict", "nothing")
        type = login_dict["type"]
        admin_id = login_dict["id"]
        photo_link = "/" + login_dict["photo_link"]
        panel = object
        search_dict = {}
        id = request.form.get('id', '')
        username = request.form.get('username', '')
        contact_no = request.form.get('contact_no', '')
        email = request.form.get('email', '')
        panel_mapping = {
            "admin": "admin_data",
            "student": "students_data",
            "teacher": "teacher_data",
            "department": "department_data",
            "subject": "subject_data",
            "class": "class_data",
        }
        if panel in panel_mapping:
            print("Panel is in the mapping")
            if panel in ["admin", "student", "teacher"]:
                if id:
                    search_value = f'{panel}_id|{id}'
                elif username:
                    search_value = f'username|{username}'
                elif contact_no:
                    search_value = f'contact_no|{contact_no}'
                elif email:
                    search_value = f'email|{email}'
                else:
                    app.logger.debug(f"Search field is invalid, please try with some other field...")
                    if panel == "class":
                        return render_template(f'{panel}es.html')
                    return render_template(f'{panel}s.html')
            else:
                if id:
                    search_value = f'{panel}_id|{id}'
                elif username:
                    search_value = f'department_name|{username}'
                elif contact_no and panel in ["class"]:
                    search_value = f'class_name|{contact_no}'
                else:
                    app.logger.debug(f"Search field is invalid, please try with some other field...")
                    if panel == "class":
                        return render_template(f'{panel}es.html')
                    return render_template(f'{panel}s.html')
            coll_name = panel_mapping[panel]
            print(f"Search value is : {search_value}, coll_name is : {coll_name}")
            search_dict = search_panel_data(app, client, "college_management", search_value, coll_name)
        else:
            print("Panel is not in the mapping")
            app.logger.debug(f"Error in searching data from database")
        return render_template('search_result.html', panel=panel, search_dict=search_dict, type=type, admin_id=admin_id, photo_link=photo_link)

    except Exception as e:
        app.logger.debug(f"Error in searching data from database: {e}")
        print(e)
        flash("Please try again...")
        panel = object
        if panel == "class":
            return render_template(f'{panel}es.html')
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
            if login_dict["photo_link"]!="static/assets/img/profiles/avatar-01.jpg":
                photo_link = "/" + login_dict["photo_link"]
            else:
                photo_link = login_dict["photo_link"]
        else:
            type = "Anonymous"
            id = "anonymous"
            photo_link = "static/assets/img/profiles/avatar-01.jpg"
        db = client["college_management"]
        coll_admin = db["admin_data"]
        coll_student = db["students_data"]
        coll_teacher = db["teacher_data"]
        coll_department = db["department_data"]
        student_count = coll_student.count_documents({})
        admin_count = coll_admin.count_documents({})
        teacher_count = coll_teacher.count_documents({})
        department_count = coll_department.count_documents({})
        return render_template("index.html", admin_id=id, type=type, photo_link=photo_link,
                               student_count=student_count, admin_count=admin_count, teacher_count=teacher_count,
                               department_count=department_count)

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
        if all_keys and all_values:
            return render_template("admins.html", all_keys=all_keys[0], all_values=all_values, type=type, admin_id=id,
                                   photo_link=photo_link)
        else:
            return render_template("admins.html", all_keys=all_keys, all_values=all_values, type=type, admin_id=id,
                                   photo_link=photo_link)

    except Exception as e:
        app.logger.debug(f"Error in show admins data from admin panel: {e}")
        flash("Please try again..")
        return redirect(url_for('admin_data_list', _external=True, _scheme=secure_type))

@app.route("/student/student_profile", methods=["GET", "POST"])
def student_profile():
    """
    That funcation can use show all admins data from admin panel
    """

    try:
        login_dict = session.get("login_dict", "nothing")
        type = login_dict["type"]
        id = login_dict["id"]
        photo_link = "/" + login_dict["photo_link"]
        search_dict = get_profile_data(app, client, "college_management", type)
        return render_template("student_profile.html", search_dict=search_dict, type=type, student_id=id,
                                   photo_link=photo_link)

    except Exception as e:
        app.logger.debug(f"Error in show student data in profile section: {e}")
        flash("Please try again..")
        return redirect(url_for('student_profile', _external=True, _scheme=secure_type))

@app.route("/teacher/teacher_profile", methods=["GET", "POST"])
def teacher_profile():
    """
    That funcation can use show all admins data from admin panel
    """

    try:
        login_dict = session.get("login_dict", "nothing")
        type = login_dict["type"]
        id = login_dict["id"]
        photo_link = "/" + login_dict["photo_link"]
        search_dict = get_profile_data(app, client, "college_management", type)
        return render_template("teacher_profile.html", search_dict=search_dict, type=type, teacher_id=id,
                                   photo_link=photo_link)

    except Exception as e:
        app.logger.debug(f"Error in show student data in profile section: {e}")
        flash("Please try again..")
        return redirect(url_for('teacher_profile', _external=True, _scheme=secure_type))


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
        allcity = list(constant_data.get("city_province_mapping", {}).keys())
        allstate, allcountrycode = get_all_country_state_names(app)

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
            province = request.form["province"]
            new_contact_no = countrycode + " " + contact_no
            new_emergency_contact_no = countrycode + " " + emergency_contact_no

            # username validation
            all_admin_data = find_all_data(app, db, "login_mapping")
            get_all_username = [ad_data["username"] for ad_data in all_admin_data]
            if username in get_all_username:
                flash("Username already exits. Please try with different Username")
                return render_template("add-admin.html", allcountrycode=allcountrycode, allcity=allcity,
                                       allstate=allstate,
                                       first_name=first_name, last_name=last_name, username=username, password=password,
                                       gender=gender, contact_no=contact_no, emergency_contact_no=emergency_contact_no,
                                       email=email, address=address, countrycode=countrycode, city=city, province=province,
                                       type=type, photo_link=photo_main_link, admin_id=admin_id)

            all_admin_data = find_all_data(app, db, "login_mapping")
            get_all_email = [ad_data["email"] for ad_data in all_admin_data]
            if email in get_all_email:
                flash("Email already exits. Please try with different Email..")
                return render_template("add-admin.html", allcountrycode=allcountrycode, allcity=allcity,
                                       allstate=allstate,
                                       first_name=first_name, last_name=last_name, username=username, password=password,
                                       gender=gender, contact_no=contact_no, emergency_contact_no=emergency_contact_no,
                                       email=email, address=address, countrycode=countrycode, city=city, province=province,
                                       type=type, photo_link=photo_main_link, admin_id=admin_id)

            # password validation
            if not password_validation(app=app, password=password):
                flash("Please choose strong password. Add at least 1 special character, number, capitalize latter..")
                return render_template("add-admin.html", allcountrycode=allcountrycode, allcity=allcity,
                                       allstate=allstate,
                                       first_name=first_name, last_name=last_name, username=username, password=password,
                                       gender=gender, contact_no=contact_no, emergency_contact_no=emergency_contact_no,
                                       email=email, address=address, countrycode=countrycode, city=city, province=province,
                                       type=type, photo_link=photo_main_link, admin_id=admin_id)

            # contact number and emergency contact number validation
            get_phone_val = validate_phone_number(app=app, phone_number=contact_no)
            get_emergency_phone_val = validate_phone_number(app, emergency_contact_no)
            if get_phone_val == "invalid number":
                flash("Please enter correct contact no.")
                return render_template("add-admin.html", allcountrycode=allcountrycode, allcity=allcity,
                                       allstate=allstate,
                                       first_name=first_name, last_name=last_name, username=username, password=password,
                                       gender=gender, contact_no=contact_no, emergency_contact_no=emergency_contact_no,
                                       email=email, address=address, countrycode=countrycode, city=city, province=province,
                                       type=type, photo_link=photo_main_link, admin_id=admin_id)

            if get_emergency_phone_val == "invalid number":
                flash("Please enter correct emergency contact no.")
                return render_template("add-admin.html", allcountrycode=allcountrycode, allcity=allcity,
                                       allstate=allstate,
                                       first_name=first_name, last_name=last_name, username=username, password=password,
                                       gender=gender, contact_no=contact_no, emergency_contact_no=emergency_contact_no,
                                       email=email, address=address, countrycode=countrycode, city=city, province=province,
                                       type=type, photo_link=photo_main_link, admin_id=admin_id)

            if 'photo_link' not in request.files:
                flash('No file part')
                return render_template("add-admin.html", allcountrycode=allcountrycode, allcity=allcity,
                                       allstate=allstate,
                                       first_name=first_name, last_name=last_name, username=username, password=password,
                                       gender=gender, contact_no=contact_no, emergency_contact_no=emergency_contact_no,
                                       email=email, address=address, countrycode=countrycode, city=city, province=province,
                                       type=type, photo_link=photo_main_link, admin_id=admin_id)

            if photo_link.filename == '':
                flash('No image selected for uploading')
                return render_template("add-admin.html", allcountrycode=allcountrycode, allcity=allcity,
                                       allstate=allstate,
                                       first_name=first_name, last_name=last_name, username=username, password=password,
                                       gender=gender, contact_no=contact_no, emergency_contact_no=emergency_contact_no,
                                       email=email, address=address, countrycode=countrycode, city=city, province=province,
                                       type=type, photo_link=photo_main_link, admin_id=admin_id)

            if photo_link and allowed_photos(photo_link.filename):
                filename = secure_filename(username + ".jpg")
                ans = checking_upload_folder(filename=filename)
                if ans != "duplicate":
                    photo_link.save(os.path.join(app.config["PROFILE_UPLOAD_FOLDER"], filename))
                    photo_path = os.path.join(app.config["PROFILE_UPLOAD_FOLDER"], filename)
                else:
                    flash('This filename already exits')
                    return render_template("add-admin.html", allcountrycode=allcountrycode, allcity=allcity,
                                           allstate=allstate,
                                           first_name=first_name, last_name=last_name, username=username,
                                           password=password,
                                           gender=gender, contact_no=contact_no,
                                           emergency_contact_no=emergency_contact_no,
                                           email=email, address=address, countrycode=countrycode, city=city,
                                           province=province, type=type, photo_link=photo_main_link, admin_id=admin_id)
            else:
                flash('This file format is not supported.....')
                return render_template("add-admin.html", allcountrycode=allcountrycode, allcity=allcity,
                                       allstate=allstate,
                                       first_name=first_name, last_name=last_name, username=username, password=password,
                                       gender=gender, contact_no=contact_no, emergency_contact_no=emergency_contact_no,
                                       email=email, address=address, countrycode=countrycode, city=city, province=province,
                                       type=type, photo_link=photo_main_link, admin_id=admin_id)

            # admin-id validation
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
                "contact_no": new_contact_no,
                "emergency_contact_no": new_emergency_contact_no,
                "email": email,
                "address": address,
                "city": city,
                "province": province,
                "type": "admin",
                "inserted_on": get_timestamp(app),
                "updated_on": get_timestamp(app)
            }

            admin_mapping_dict = {}
            admin_mapping_dict["photo_link"] = photo_path
            admin_mapping_dict["admin_id"] = str(unique_admin_id)
            admin_mapping_dict["username"] = username
            admin_mapping_dict["email"] = email
            admin_mapping_dict["password"] = password
            admin_mapping_dict["type"] = "admin"
            data_added(app, db, "admin_data", register_dict)
            get_login_data = find_all_data(app, db, "login_mapping")
            all_login_data = []
            for login_data in get_login_data:
                del login_data["_id"]
                all_login_data.append({"email":login_data["email"], "username": login_data["username"]})
            if [admin_mapping_dict["email"], admin_mapping_dict["username"]] not in all_login_data:
                data_added(app, db, "login_mapping", admin_mapping_dict)
            mail.send_message("[Rylee] Account Credentials",
                              sender="harshitgadhiya8980@gmail.com",
                              recipients=[email],
                              body=f"Hello There,\nWe hope this message finds you well. As part of our ongoing commitment to ensure the security of your account. Your request for opening an 'Account' has been processed successfully and your account has been opened.\n Please check with the below credential.\nAdminID: {unique_admin_id}\nUsername: {username}\nif you have any concerns regarding your account security, be sure to get in touch with our support team immediately at help@codescatter.com\nThank you for your cooperation.\nBest regards,\nCodescatter",
                              html=f'<p>Hello There,</p><p>We hope this message finds you well. As part of our ongoing commitment to ensure the security of your account. Your request for opening an "Account" has been processed successfully and your account has been opened.</p><p>Please check with the below credential.</p><p><h2><b>AdminID - {unique_admin_id}</b></h2></p><p><h2><b>Username - {username}</b></h2></p><p>if you have any concerns regarding your account security, be sure to get in touch with our support team immediately at help@codescatter.com</p><p>Thank you for your cooperation.</p><p>Best regards,<br>Codescatter</p>')
            flash("Data Added Successfully")
            return redirect(url_for('admin_data_list', _external=True, _scheme=secure_type))
        else:
            return render_template("add-admin.html", type=type, photo_link=photo_main_link, admin_id=admin_id,
                                   allcountrycode=allcountrycode, allcity=allcity, allstate=allstate)

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
        if all_keys and all_values:
            return render_template("students.html", type=type, admin_id=id, photo_link=photo_link, all_keys=all_keys[0],
                                   all_values=all_values)
        else:
            return render_template("students.html", type=type, admin_id=id, photo_link=photo_link, all_keys=all_keys,
                                   all_values=all_values)

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
        allcity = list(constant_data.get("city_province_mapping", {}).keys())
        allstate, allcountrycode = get_all_country_state_names(app)
        allbatchyear = list(range(2000, 2025))
        allbatchyear = allbatchyear[::-1]
        department_data = find_all_data(app, db, "department_data")
        alldepartment = [department["department_name"] for department in department_data]

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
            province = request.form["province"]
            admission_date = request.form["admission_date"]
            department = request.form["department"]
            classes = request.form["classes"]
            batch_year = request.form["batch_year"]
            new_contact_no = countrycode + " " + contact_no
            new_emergency_contact_no = countrycode + " " + emergency_contact_no

            # username validation
            all_student_data = find_all_data(app, db, "students_data")
            get_all_username = [st_data["username"] for st_data in all_student_data]
            if username in get_all_username:
                flash("Username already exits. Please try with different Username")
                return render_template("add-student.html", allcountrycode=allcountrycode, username=username,
                                       allcity=allcity, alldepartment=alldepartment, department=department,
                                       allstate=allstate, type=type, admin_id=admin_id,
                                       photo_link=photo_student_link, classes=classes,
                                       allbatchyear=allbatchyear, first_name=first_name, last_name=last_name,
                                       password=password, countrycode=countrycode, city=city, province=province,
                                       dob=dob, gender=gender, contact_no=contact_no,
                                       emergency_contact_no=emergency_contact_no, email=email, batch_year=batch_year,
                                       address=address, admission_date=admission_date)

            # password validation
            if not password_validation(app=app, password=password):
                flash("Please choose strong password. Add at least 1 special character, number, capitalize latter..")
                return render_template("add-student.html", allcountrycode=allcountrycode, username=username,
                                       allcity=allcity, alldepartment=alldepartment,
                                       allstate=allstate, type=type, admin_id=admin_id,
                                       photo_link=photo_student_link, classes=classes, department=department,
                                       allbatchyear=allbatchyear, first_name=first_name, last_name=last_name,
                                       password=password, countrycode=countrycode, city=city, province=province,
                                       dob=dob, gender=gender, contact_no=contact_no,
                                       emergency_contact_no=emergency_contact_no, email=email, batch_year=batch_year,
                                       address=address, admission_date=admission_date)

            # contact number and emergency contact number validation
            get_phone_val = validate_phone_number(app=app, phone_number=contact_no)
            get_emergency_phone_val = validate_phone_number(app, emergency_contact_no)
            if get_phone_val == "invalid number":
                flash("Please enter correct contact no.")
                return render_template("add-student.html", allcountrycode=allcountrycode, username=username,
                                       allcity=allcity, alldepartment=alldepartment,
                                       allstate=allstate, type=type, admin_id=admin_id,
                                       photo_link=photo_student_link, classes=classes, department=department,
                                       allbatchyear=allbatchyear, first_name=first_name, last_name=last_name,
                                       password=password, countrycode=countrycode, city=city, province=province,
                                       dob=dob, gender=gender, contact_no=contact_no,
                                       emergency_contact_no=emergency_contact_no, email=email, batch_year=batch_year,
                                       address=address, admission_date=admission_date)

            if get_emergency_phone_val == "invalid number":
                flash("Please enter correct emergency contact no.")
                return render_template("add-student.html", allcountrycode=allcountrycode, username=username,
                                       allcity=allcity, alldepartment=alldepartment,
                                       allstate=allstate, type=type, admin_id=admin_id,
                                       photo_link=photo_student_link,
                                       allbatchyear=allbatchyear, first_name=first_name, last_name=last_name,
                                       password=password, countrycode=countrycode, city=city, province=province,
                                       classes=classes, department=department,
                                       dob=dob, gender=gender, contact_no=contact_no,
                                       emergency_contact_no=emergency_contact_no, email=email, batch_year=batch_year,
                                       address=address, admission_date=admission_date)

            if 'photo_link' not in request.files:
                flash('No file part')
                return render_template("add-student.html", allcountrycode=allcountrycode, username=username,
                                       allcity=allcity, alldepartment=alldepartment,
                                       allstate=allstate, type=type, admin_id=admin_id,
                                       photo_link=photo_student_link,
                                       allbatchyear=allbatchyear, first_name=first_name, last_name=last_name,
                                       password=password, countrycode=countrycode, city=city, province=province,
                                       classes=classes, department=department,
                                       dob=dob, gender=gender, contact_no=contact_no,
                                       emergency_contact_no=emergency_contact_no, email=email, batch_year=batch_year,
                                       address=address, admission_date=admission_date)

            if photo_link.filename == '':
                flash('No image selected for uploading')
                return render_template("add-student.html", allcountrycode=allcountrycode, username=username,
                                       allcity=allcity, alldepartment=alldepartment,
                                       allstate=allstate, type=type, admin_id=admin_id,
                                       photo_link=photo_student_link,
                                       allbatchyear=allbatchyear, first_name=first_name, last_name=last_name,
                                       password=password, countrycode=countrycode, city=city, province=province,
                                       classes=classes, department=department,
                                       dob=dob, gender=gender, contact_no=contact_no,
                                       emergency_contact_no=emergency_contact_no, email=email, batch_year=batch_year,
                                       address=address, admission_date=admission_date)

            if photo_link and allowed_photos(photo_link.filename):
                filename = secure_filename("student_" + username + ".jpg")
                ans = checking_upload_folder(filename=filename)
                if ans != "duplicate":
                    photo_link.save(os.path.join(app.config["PROFILE_UPLOAD_FOLDER"], filename))
                    photo_path = os.path.join(app.config["PROFILE_UPLOAD_FOLDER"], filename)
                else:
                    flash('This filename already exits')
                    return render_template("add-student.html", allcountrycode=allcountrycode, username=username,
                                           allcity=allcity, alldepartment=alldepartment,
                                           allstate=allstate, type=type, admin_id=admin_id,
                                           photo_link=photo_student_link,
                                           allbatchyear=allbatchyear, first_name=first_name, last_name=last_name,
                                           password=password, countrycode=countrycode, city=city, province=province,
                                           classes=classes, department=department,
                                           dob=dob, gender=gender, contact_no=contact_no,
                                           emergency_contact_no=emergency_contact_no, email=email,
                                           batch_year=batch_year,
                                           address=address, admission_date=admission_date)
            else:
                flash('This file format is not supported.....')
                return render_template("add-student.html", allcountrycode=allcountrycode, username=username,
                                       allcity=allcity, alldepartment=alldepartment,
                                       allstate=allstate, type=type, admin_id=admin_id,
                                       photo_link=photo_student_link,
                                       allbatchyear=allbatchyear, first_name=first_name, last_name=last_name,
                                       password=password, countrycode=countrycode, city=city, province=province,
                                       classes=classes, department=department,
                                       dob=dob, gender=gender, contact_no=contact_no,
                                       emergency_contact_no=emergency_contact_no, email=email, batch_year=batch_year,
                                       address=address, admission_date=admission_date)

            # student-id validation
            all_student_data = find_spec_data(app, db, "login_mapping", {"type": "student"})
            get_all_student_id = [st_data["student_id"] for st_data in all_student_data]
            unique_student_id = get_unique_student_id(app, get_all_student_id)
            register_dict = {
                "photo_link": photo_path,
                "student_id": str(unique_student_id),
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "password": password,
                "dob": dob,
                "gender": gender,
                "contact_no": new_contact_no,
                "emergency_contact_no": new_emergency_contact_no,
                "email": email,
                "address": address,
                "city": city,
                "province": province,
                "admission_date": admission_date,
                "classes": classes,
                "department": department,
                "batch_year": batch_year,
                "type": "student",
                "inserted_on": get_timestamp(app),
                "updated_on": get_timestamp(app)
            }

            student_mapping_dict = {}
            student_mapping_dict["photo_link"] = photo_path
            student_mapping_dict["student_id"] = str(unique_student_id)
            student_mapping_dict["username"] = username
            student_mapping_dict["email"] = email
            student_mapping_dict["password"] = password
            student_mapping_dict["type"] = "student"
            classes_mapping_dict = {}
            classes_mapping_dict["student_id"] = str(unique_student_id)
            classes_mapping_dict["department"] = department
            classes_mapping_dict["class_name"] = classes
            classes_mapping_dict["type"] = "student"
            data_added(app, db, "class_data", classes_mapping_dict)
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
            return render_template("add-student.html", type=type, alldepartment=alldepartment, admin_id=admin_id,
                                   photo_link=photo_student_link, allcountrycode=allcountrycode, allcity=allcity, allbatchyear=allbatchyear)

    except Exception as e:
        app.logger.debug(f"Error in add student data route: {e}")
        flash("Please try again...")
        return redirect(url_for('student_register', _external=True, _scheme=secure_type))


@app.route("/admin/teacher_data", methods=["GET", "POST"])
def teacher_data_list():
    """
    That funcation can use show all students data from admin panel
    """

    try:
        login_dict = session.get("login_dict", "nothing")
        type = login_dict["type"]
        id = login_dict["id"]
        photo_link = "/" + login_dict["photo_link"]
        all_keys, all_values = get_admin_data(app, client, "college_management", "teacher_data")
        if all_keys and all_values:
            return render_template("teachers.html", all_keys=all_keys[0], all_values=all_values, type=type,
                                   admin_id=id, photo_link=photo_link)
        else:
            return render_template("teachers.html", all_keys=all_keys, all_values=all_values, type=type, admin_id=id,
                                   photo_link=photo_link)


    except Exception as e:
        app.logger.debug(f"Error in add teacher data route: {e}")
        flash("Please try again...")
        return redirect(url_for('teacher_data_list', _external=True, _scheme=secure_type))


@app.route("/admin/add_teacher", methods=["GET", "POST"])
def add_teacher():
    """
    Handling teacher register process
    :return: teacher register template
    """
    try:
        login_dict = session.get("login_dict", "nothing")
        type = login_dict["type"]
        admin_id = login_dict["id"]
        photo_teacher_link = "/" + login_dict["photo_link"]
        db = client["college_management"]
        allcity = list(constant_data.get("city_province_mapping", {}).keys())
        allstate, allcountrycode = get_all_country_state_names(app)
        allqualification = ["MBA", "ME", "BCA", "MCA", "BBA"]
        department_data = find_all_data(app, db, "department_data")
        alldepartment = [department["department_name"] for department in department_data]
        subject_data = find_all_data(app, db, "subject_data")
        allsubjects = [subject["subject_name"] for subject in subject_data]
        allsubjects = list(set(allsubjects))
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
            province = request.form["province"]
            qualification = request.form["qualification"]
            department = request.form["department"]
            subject = request.form["subject"]
            joining_date = request.form["joining_date"]
            new_contact_no = countrycode + " " + contact_no
            new_emergency_contact_no = countrycode + " " + emergency_contact_no

            all_teacher_data = find_all_data(app, db, "teacher_data")
            get_all_username = [te_data["username"] for te_data in all_teacher_data]
            if username in get_all_username:
                flash("Username already exits. Please try with different Username")
                return render_template("add-teacher.html", username=username, allcountrycode=allcountrycode,
                                       allcity=allcity,
                                       allstate=allstate, type=type, admin_id=admin_id, photo_link=photo_teacher_link,
                                       allqualification=allqualification,
                                       allsubjects=allsubjects, alldepartment=alldepartment, countrycode=countrycode,
                                       first_name=first_name, last_name=last_name, password=password, dob=dob,
                                       gender=gender, contact_no=contact_no, city=city, province=province,
                                       emergency_contact_no=emergency_contact_no, email=email, subject=subject,
                                       address=address, joining_date=joining_date, qualification=qualification,
                                       department=department)

            # password validation
            if not password_validation(app=app, password=password):
                flash("Please choose strong password. Add at least 1 special character, number, capitalize latter..")
                return render_template("add-teacher.html", username=username, allcountrycode=allcountrycode,
                                       allcity=allcity,
                                       allstate=allstate, type=type, admin_id=admin_id, photo_link=photo_teacher_link,
                                        allqualification=allqualification,
                                       allsubjects=allsubjects, alldepartment=alldepartment, countrycode=countrycode,
                                       first_name=first_name, last_name=last_name, password=password, dob=dob,
                                       gender=gender, contact_no=contact_no, city=city, province=province,
                                       emergency_contact_no=emergency_contact_no, email=email, subject=subject,
                                       address=address, joining_date=joining_date, qualification=qualification,
                                       department=department)

            # contact number and emergency contact number validation
            get_phone_val = validate_phone_number(app=app, phone_number=contact_no)
            get_emergency_phone_val = validate_phone_number(app, emergency_contact_no)
            if get_phone_val == "invalid number":
                flash("Please enter correct contact no.")
                return render_template("add-teacher.html", username=username, allcountrycode=allcountrycode,
                                       allcity=allcity,
                                       allstate=allstate, type=type, admin_id=admin_id, photo_link=photo_teacher_link,
                                        allqualification=allqualification,
                                       allsubjects=allsubjects, alldepartment=alldepartment, countrycode=countrycode,
                                       first_name=first_name, last_name=last_name, password=password, dob=dob,
                                       gender=gender, contact_no=contact_no, city=city, province=province,
                                       emergency_contact_no=emergency_contact_no, email=email, subject=subject,
                                       address=address, joining_date=joining_date, qualification=qualification,
                                       department=department)

            if get_emergency_phone_val == "invalid number":
                flash("Please enter correct emergency contact no.")
                return render_template("add-teacher.html", username=username, allcountrycode=allcountrycode,
                                       allcity=allcity,
                                       allstate=allstate, type=type, admin_id=admin_id, photo_link=photo_teacher_link,
                                        allqualification=allqualification,
                                       allsubjects=allsubjects, alldepartment=alldepartment, countrycode=countrycode,
                                       first_name=first_name, last_name=last_name, password=password, dob=dob,
                                       gender=gender, contact_no=contact_no, city=city, province=province,
                                       emergency_contact_no=emergency_contact_no, email=email, subject=subject,
                                       address=address, joining_date=joining_date, qualification=qualification,
                                       department=department)

            if 'photo_link' not in request.files:
                flash('No file part')
                return render_template("add-teacher.html", username=username, allcountrycode=allcountrycode,
                                       allcity=allcity,
                                       allstate=allstate, type=type, admin_id=admin_id, photo_link=photo_teacher_link,
                                        allqualification=allqualification,
                                       allsubjects=allsubjects, alldepartment=alldepartment, countrycode=countrycode,
                                       first_name=first_name, last_name=last_name, password=password, dob=dob,
                                       gender=gender, contact_no=contact_no, city=city, province=province,
                                       emergency_contact_no=emergency_contact_no, email=email, subject=subject,
                                       address=address, joining_date=joining_date, qualification=qualification,
                                       department=department)

            if photo_link.filename == '':
                flash('No image selected for uploading')
                return render_template("add-teacher.html", username=username, allcountrycode=allcountrycode,
                                       allcity=allcity,
                                       allstate=allstate, type=type, admin_id=admin_id, photo_link=photo_teacher_link,
                                        allqualification=allqualification,
                                       allsubjects=allsubjects, alldepartment=alldepartment, countrycode=countrycode,
                                       first_name=first_name, last_name=last_name, password=password, dob=dob,
                                       gender=gender, contact_no=contact_no, city=city, province=province,
                                       emergency_contact_no=emergency_contact_no, email=email, subject=subject,
                                       address=address, joining_date=joining_date, qualification=qualification,
                                       department=department)

            if photo_link and allowed_photos(photo_link.filename):
                filename = secure_filename("teacher_" + username + ".jpg")
                ans = checking_upload_folder(filename=filename)
                if ans != "duplicate":
                    photo_link.save(os.path.join(app.config["PROFILE_UPLOAD_FOLDER"], filename))
                    photo_path = os.path.join(app.config["PROFILE_UPLOAD_FOLDER"], filename)
                else:
                    flash('This filename already exits')
                    return render_template("add-teacher.html", username=username, allcountrycode=allcountrycode,
                                           allcity=allcity,
                                           allstate=allstate, type=type, admin_id=admin_id,
                                           photo_link=photo_teacher_link,
                                            allqualification=allqualification,
                                           allsubjects=allsubjects, alldepartment=alldepartment,
                                           countrycode=countrycode,
                                           first_name=first_name, last_name=last_name, password=password, dob=dob,
                                           gender=gender, contact_no=contact_no, city=city, province=province,
                                           emergency_contact_no=emergency_contact_no, email=email, subject=subject,
                                           address=address, joining_date=joining_date, qualification=qualification,
                                           department=department)
            else:
                flash('This file format is not supported.....')
                return render_template("add-teacher.html", username=username, allcountrycode=allcountrycode,
                                       allcity=allcity,
                                       allstate=allstate, type=type, admin_id=admin_id, photo_link=photo_teacher_link,
                                        allqualification=allqualification,
                                       allsubjects=allsubjects, alldepartment=alldepartment, countrycode=countrycode,
                                       first_name=first_name, last_name=last_name, password=password, dob=dob,
                                       gender=gender, contact_no=contact_no, city=city, province=province,
                                       emergency_contact_no=emergency_contact_no, email=email, subject=subject,
                                       address=address, joining_date=joining_date, qualification=qualification,
                                       department=department)

            # teacher id validation
            all_teacher_data = find_spec_data(app, db, "login_mapping", {"type": "teacher"})
            get_all_teacher_id = [ta_data["teacher_id"] for ta_data in all_teacher_data]
            unique_teacher_id = get_unique_teacher_id(app, get_all_teacher_id)
            register_dict = {
                "photo_link": photo_path,
                "teacher_id": str(unique_teacher_id),
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "password": password,
                "dob": dob,
                "gender": gender,
                "contact_no": new_contact_no,
                "emergency_contact_no": new_emergency_contact_no,
                "email": email,
                "address": address,
                "city": city,
                "province": province,
                "qualification": qualification,
                "department": department,
                "subject": subject,
                "joining_date": joining_date,
                "type": "teacher",
                "inserted_on": get_timestamp(app),
                "updated_on": get_timestamp(app)
            }

            teacher_mapping_dict = {}
            teacher_mapping_dict["photo_link"] = photo_path
            teacher_mapping_dict["teacher_id"] = str(unique_teacher_id)
            teacher_mapping_dict["username"] = username
            teacher_mapping_dict["email"] = email
            teacher_mapping_dict["password"] = password
            teacher_mapping_dict["type"] = "teacher"
            subject_mapping_dict = {}
            subject_mapping_dict["teacher_id"] = str(unique_teacher_id)
            subject_mapping_dict["department_name"] = department
            subject_mapping_dict["subject"] = subject
            subject_mapping_dict["type"] = "teacher"
            data_added(app, db, "subject_mapping", subject_mapping_dict)
            data_added(app, db, "teacher_data", register_dict)
            data_added(app, db, "login_mapping", teacher_mapping_dict)
            mail.send_message("[Rylee] Account Credentials",
                              sender="harshitgadhiya8980@gmail.com",
                              recipients=[email],
                              body=f"Hello There,\nWe hope this message finds you well. As part of our ongoing commitment to ensure the security of your account. Your request for opening an 'Account' has been processed successfully and your account has been opened.\n Please check with the below credential.\nStudentID: {unique_teacher_id}\nUsername: {username}\nif you have any concerns regarding your account security, be sure to get in touch with our support team immediately at help@codescatter.com\nThank you for your cooperation.\nBest regards,\nCodescatter",
                              html=f'<p>Hello There,</p><p>We hope this message finds you well. As part of our ongoing commitment to ensure the security of your account. Your request for opening an "Account" has been processed successfully and your account has been opened.</p><p>Please check with the below credential.</p><p><h2><b>Student_id - {unique_teacher_id}</b></h2></p><p><h2><b>Username - {username}</b></h2></p><p>if you have any concerns regarding your account security, be sure to get in touch with our support team immediately at help@codescatter.com</p><p>Thank you for your cooperation.</p><p>Best regards,<br>Codescatter</p>')
            flash("Data Added Successfully")

            return redirect(url_for('teacher_data_list', _external=True, _scheme=secure_type))
        else:
            return render_template("add-teacher.html", allcountrycode=allcountrycode,
                                   allcity=allcity, allstate=allstate,
                                   allqualification=allqualification, allsubjects=allsubjects,
                                   alldepartment=alldepartment)

    except Exception as e:
        app.logger.debug(f"Error in add teacher data route: {e}")
        flash("Please try again...")
        return redirect(url_for('add_teacher', _external=True, _scheme=secure_type))


@app.route("/admin/department_data", methods=["GET", "POST"])
def department_data_list():
    """
    That funcation can use show all admins data from admin panel
    """

    try:
        login_dict = session.get("login_dict", "nothing")
        type = login_dict["type"]
        id = login_dict["id"]
        photo_link = "/" + login_dict["photo_link"]
        all_keys, all_values = get_admin_data(app, client, "college_management", "department_data")
        if all_keys and all_values:
            return render_template("departments.html", all_keys=all_keys[0], all_values=all_values, type=type,
                                   admin_id=id, photo_link=photo_link)
        else:
            return render_template("departments.html", all_keys=all_keys, all_values=all_values, type=type, admin_id=id,
                                   photo_link=photo_link)

    except Exception as e:
        app.logger.debug(f"Error in show departments data from department panel: {e}")
        flash("Please try again..")
        return redirect(url_for('department_data_list', _external=True, _scheme=secure_type))


@app.route("/admin/add_department", methods=["GET", "POST"])
def add_department():
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
        if request.method == "POST":
            hod_name = request.form["hod_name"]
            department_date = request.form["department_date"]
            department_name = request.form["department_name"]

            # department validation
            all_department_data = find_all_data(app, db, "department_data")
            get_all_department_name = [st_data["department_name"] for st_data in all_department_data]
            if department_name in get_all_department_name:
                flash("Department name already exits. Please try with different Department name")
                return render_template("add-department.html", hod_name=hod_name, department_name=department_name,
                                       department_date=department_date, type=type, admin_id=admin_id,
                                       photo_link=photo_student_link)

            # department-id validation
            all_department_data = find_all_data(app, db, "department_data")
            get_all_department_id = [dt_data["department_id"] for dt_data in all_department_data]
            unique_department_id = get_unique_department_id(app, get_all_department_id)
            register_dict = {
                "department_id": unique_department_id,
                "department_name": department_name,
                "department_date": department_date,
                "HOD_name": hod_name,
                "type": "department",
                "inserted_on": get_timestamp(app),
                "updated_on": get_timestamp(app)
            }

            data_added(app, db, "department_data", register_dict)
            flash("Data Added Successfully")
            return redirect(url_for('department_data_list', _external=True, _scheme=secure_type))
        else:
            return render_template("add-department.html", type=type, admin_id=admin_id, photo_link=photo_student_link)

    except Exception as e:
        app.logger.debug(f"Error in add departpent data route: {e}")
        flash("Please try again...")
        return redirect(url_for('add_department', _external=True, _scheme=secure_type))


@app.route("/admin/subject_data", methods=["GET", "POST"])
def subject_data_list():
    """
    That funcation can use show all admins data from admin panel
    """

    try:
        login_dict = session.get("login_dict", "nothing")
        type = login_dict["type"]
        id = login_dict["id"]
        photo_link = "/" + login_dict["photo_link"]
        all_keys, all_values = get_admin_data(app, client, "college_management", "subject_data")
        if all_keys and all_values:
            return render_template("subjects.html", all_keys=all_keys[0], all_values=all_values, type=type, admin_id=id,
                                   photo_link=photo_link)
        else:
            return render_template("subjects.html", all_keys=all_keys, all_values=all_values, type=type, admin_id=id,
                                   photo_link=photo_link)

    except Exception as e:
        app.logger.debug(f"Error in show departments data from department panel: {e}")
        flash("Please try again..")
        return redirect(url_for('department_data_list', _external=True, _scheme=secure_type))


@app.route("/admin/add_subject", methods=["GET", "POST"])
def add_subject():
    """
    In this route we can handling student register process
    :return: register template
    """
    try:
        login_dict = session.get("login_dict", "nothing")
        type = login_dict["type"]
        admin_id = login_dict["id"]
        photo_link = "/" + login_dict["photo_link"]
        db = client["college_management"]
        department_data = find_all_data(app, db, "department_data")
        alldepartment = [department["department_name"] for department in department_data]
        if request.method == "POST":
            subject_name = request.form["subject_name"]
            department = request.form["department"]
            subject_date = request.form["subject_date"]

            # department-id validation
            all_subject_data = find_all_data(app, db, "subject_data")
            get_all_subject_id = [sub_data["subject_id"] for sub_data in all_subject_data]
            unique_subject_id = get_unique_subject_id(app, get_all_subject_id)
            register_dict = {
                "subject_id": unique_subject_id,
                "subject_name": subject_name,
                "department_name": department,
                "subject_start_date": subject_date,
                "type": "subject",
                "inserted_on": get_timestamp(app),
                "updated_on": get_timestamp(app)
            }

            data_added(app, db, "subject_data", register_dict)
            flash("Data Added Successfully")
            return redirect(url_for('subject_data_list', _external=True, _scheme=secure_type))
        else:
            return render_template("add-subject.html", type=type, admin_id=admin_id,
                                   photo_link=photo_link, alldepartment=alldepartment)

    except Exception as e:
        app.logger.debug(f"Error in add subject data route: {e}")
        flash("Please try again...")
        return redirect(url_for('add_subject', _external=True, _scheme=secure_type))


@app.route("/admin/classes_data", methods=["GET", "POST"])
def class_data_list():
    """
    That funcation can use show all admins data from admin panel
    """

    try:
        login_dict = session.get("login_dict", "nothing")
        type = login_dict["type"]
        id = login_dict["id"]
        photo_link = "/" + login_dict["photo_link"]
        all_keys, all_values = get_admin_data(app, client, "college_management", "class_data")
        if all_keys and all_values:
            return render_template("classes.html", all_keys=all_keys[0], all_values=all_values, type=type, admin_id=id,
                                   photo_link=photo_link)
        else:
            return render_template("classes.html", all_keys=all_keys, all_values=all_values, type=type, admin_id=id,
                                   photo_link=photo_link)

    except Exception as e:
        app.logger.debug(f"Error in show departments data from department panel: {e}")
        flash("Please try again..")
        return redirect(url_for('class_data_list', _external=True, _scheme=secure_type))


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
            photo_link = "/" + login_dict["photo_link"]
        else:
            type = "Anonymous"
            id = "anonymous"
            photo_link = "/static/assets/img/profiles/avatar-01.jpg"
        db = client["college_management"]
        coll = db["attendance_data"]
        attendance_count = coll.count_documents({"student": id})
        return render_template("student-dashboard.html", student_id=id, type=type, photo_link=photo_link, attendance_count=attendance_count)

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
            photo_link = "/" + login_dict["photo_link"]
        else:
            type = "Anonymous"
            id = "anonymous"
            photo_link = "/static/assets/img/profiles/avatar-01.jpg"
        return render_template("teacher-dashboard.html", teacher_id=id, type=type, photo_link=photo_link)

    except Exception as e:
        flash("Please try again.......................................")
        return redirect(url_for('verification', _external=True, _scheme=secure_type))

@app.route("/teacher/attendance_data", methods=["GET", "POST"])
def attendance_data_list():
    """
    That funcation can use show all admins data from admin panel
    """

    try:
        login_dict = session.get("login_dict", "nothing")
        type = login_dict["type"]
        id = login_dict["id"]
        photo_link = "/" + login_dict["photo_link"]
        all_keys, all_values = get_admin_data(app, client, "college_management", "attendance_data")
        if all_keys and all_values:
            return render_template("attendance.html", all_keys=all_keys[0], all_values=all_values, type=type, teacher_id=id,
                                   photo_link=photo_link)
        else:
            return render_template("attendance.html", all_keys=all_keys, all_values=all_values, type=type, teacher_id=id,
                                   photo_link=photo_link)

    except Exception as e:
        flash("Please try again.......................................")
        return redirect(url_for('attendance_data_list', _external=True, _scheme=secure_type))

@app.route("/student/attendance_data", methods=["GET", "POST"])
def student_attendance_data_list():
    """
    That funcation can use show all admins data from admin panel
    """

    try:
        login_dict = session.get("login_dict", "nothing")
        type = login_dict["type"]
        id = login_dict["id"]
        photo_link = "/" + login_dict["photo_link"]
        condition_dict = {"student":id}
        all_keys, all_values = get_student_data(app, client, "college_management", "attendance_data", condition_dict)
        if all_keys and all_values:
            return render_template("student_attendance.html", all_keys=all_keys[0], all_values=all_values, type=type, student_id=id,
                                   photo_link=photo_link)
        else:
            return render_template("student_attendance.html", all_keys=all_keys, all_values=all_values, type=type, student_id=id,
                                   photo_link=photo_link)

    except Exception as e:
        flash("Please try again.......................................")
        return redirect(url_for('student_attendance_data_list', _external=True, _scheme=secure_type))

@app.route("/teacher/add_attendance", methods=["GET", "POST"])
def teacher_add_attendance():
    """
    In this route we can handling admin register process
    :return: register template
    """
    try:
        login_dict = session.get("login_dict", "nothing")
        type = login_dict["type"]
        teacher_id = login_dict["id"]
        photo_main_link = "/" + login_dict["photo_link"]
        db = client["college_management"]
        department_data = find_all_data(app, db, "department_data")
        alldepartment = [department["department_name"] for department in department_data]
        student_data = find_all_data(app, db, "students_data")
        allstudents = [student["username"] for student in student_data]
        if request.method == "POST":
            student = request.form["student"]
            department = request.form["department"]
            class_name = request.form["class"]
            teacher_name = request.form["teacher_name"]
            attendance_date = request.form["attendance_date"]
            status = request.form["status"]
            reason = request.form.get("reason", "")

            register_dict = {
                "student": student,
                "department": department,
                "class_name": class_name,
                "teacher_name": teacher_name,
                "attendance_date": attendance_date,
                "status": status,
                "reason": reason,
                "inserted_on": get_timestamp(app),
                "updated_on": get_timestamp(app)
            }

            data_added(app, db, "attendance_data", register_dict)
            flash("Data Added Successfully")
            return redirect(url_for('attendance_data_list', _external=True, _scheme=secure_type))
        else:
            return render_template("add-attendance.html", type=type, photo_link=photo_main_link, teacher_id=teacher_id,
                                   alldepartment=alldepartment, allstudents=allstudents)

    except Exception as e:
        app.logger.debug(f"Error in add attendance data route: {e}")
        flash("Please try again...")
        return redirect(url_for('teacher_add_attendance', _external=True, _scheme=secure_type))


@app.route("/livechat", methods=["GET", "POST"])
def livechat():
    """
    That funcation can use for live chat
    """

    try:
        login_dict = session.get("login_dict", "nothing")
        type = login_dict["type"]
        admin_id = login_dict["id"]
        photo_teacher_link = "/" + login_dict["photo_link"]
        return render_template("chatscreen.html", admin_id=admin_id, type=type, photo_link=photo_teacher_link)

    except Exception as e:
        flash("Please try again.......................................")
        return redirect(url_for('verification', _external=True, _scheme=secure_type))


if __name__ == "__main__":
    app.run()
