from flask import (Flask, render_template, request, session, send_file, flash)
import os
from flask_cors import CORS
import json
from constant import constant_data
from operations.mongo_connection import mongo_connect, data_added, find_all_data, find_spec_data, update_mongo_data, delete_data
from operations.common_func import logger_con, get_timestamp, get_error_msg, get_response_msg, get_unique_student_id, get_unique_teacher_id

app = Flask(__name__)
CORS(app)
app.config["enviroment"] = constant_data.get("enviroment", "qa")
app.config["SECRET_KEY"] = constant_data.get("app_secreat_key", "sdfsf65416534sdfsdf4653")

logger_con(app=app)
client = mongo_connect(app=app)

@app.route("/", methods=["GET", "POST"])
def home():
    try:
        data = {
            "Spike Data": "/trst/api/v1/crust/raise_spike",
            "Get all baseline question": "/trst/api/v1/crust/get-baseline-questions?questionId=10001",
            "Data add for baseline question": "/trst/api/v1/crust/baseline-questions/create?user= userId"
        }
        response_data_msg = get_response_msg(app, "GET_ROUTES", 200, "SUCCESS", data)
        return response_data_msg

    except Exception as e:
        error_data = get_error_msg(app, e)
        app.logger.debug(f"Error in home route : {e}")
        return error_data

# return redirect(url_for('admin_home', _external=True, _scheme=secure_type))
@app.route("/admin/student_register", methods=["GET", "POST"])
def student_register():
    try:
        db = client["college_management"]
        if request.method == "POST":
            first_name = request.form["first_name"]
            last_name = request.form["last_name"]
            username = request.form["username"]
            password = request.form["password"]
            dob = request.form["dob"]
            gender = request.form["gender"]
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

            all_student_data = find_all_data(app, db, "students_data")
            get_all_username = [st_data["username"] for st_data in all_student_data]
            if username in get_all_username:
                flash("Username already exits. Please try with different Username")
                response_data_msg = get_response_msg(app, "GET", 200, "Username already exits. Please try with different Username", {})
                return response_data_msg
            else:
                all_student_data = find_spec_data(app, db, "login_mapping", {"type": "student"})
                get_all_student_id = [st_data["student_id"] for st_data in all_student_data]
                unique_student_id = get_unique_student_id(app, get_all_student_id)
                app.config["student_dict"] = {
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
                    "batch_year": batch_year
                }
        else:
            response = {"message": "data not added please use post method"}
            return response

    except Exception as e:
        error_data = get_error_msg(app, e)
        app.logger.debug(f"Error in show log api route : {e}")
        return error_data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=constant_data.get("app_port_number", 7910))