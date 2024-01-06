"""
Maintain common function code like we can use all function in every where
"""

import logging
from datetime import datetime
from constant import constant_data
import random
import phonenumbers
import pandas as pd
import json
import os

def logger_con(app):
    """
    Configure logger with filename

    :param app: app-name
    :return:
    """
    try:
        server_file_name = constant_data.get("log_file_name", constant_data.get("log_file_name", "server.log"))
        logging.basicConfig(filename=server_file_name, level=logging.DEBUG)

    except Exception as e:
        app.logger.error(f"Error when connecting logger: {e}")

def get_timestamp(app):
    """
    Get current time

    :param app: app-name
    :return: current_date
    """
    try:
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%m-%d-%Y %H:%M:%S")

        return formatted_datetime

    except Exception as e:
        app.logger.debug(f"Error in get timestamp: {e}")

def get_error_msg(app, e):
    """
    Get error response with formatting

    :param app: app-name
    :param e: error
    :return: error-response
    """
    try:
        response_data_msg = {
          "data": "null",
          "message": f"Server Not Responding Error {e}",
          "status": "FORBIDDEN",
          "statusCode": 403,
          "timestamp": get_timestamp(app)
        }

        return response_data_msg

    except Exception as e:
        app.logger.debug(f"Error in get response msg: {e}")

def get_response_msg(app,status, statuscode, message, data):
    """
    Get success response with formatting

    :param app: app-name
    :param status: status-name
    :param statuscode: status-code like 200,300
    :param message: status message
    :param data: response data
    :return: formatted response
    """

    try:
        response_data_msg = {
            "timestamp": get_timestamp(app),
            "status": status,
            "statusCode": statuscode,
            "message": message,
            "data": data
        }

        return response_data_msg

    except Exception as e:
        app.logger.debug(f"Error in get response msg: {e}")

def get_unique_student_id(app, all_student_id):
    """
    Get unique student id

    :param app: app-name
    :param all_student_id: registered all student ids
    :return: unique student id
    """
    try:
        flag = True
        while flag:
            student_id = random.randint(100000000000, 999999999999)
            if student_id not in all_student_id:
                flag = False

        return student_id

    except Exception as e:
        app.logger.debug(f"Error in get unique student id: {e}")


def get_unique_teacher_id(app, all_teacher_id):
    """
    Get unique teacher id

    :param app: app-name
    :param all_teacher_id: registered all teacher ids
    :return: unique teacher id
    """
    try:
        flag = True
        while flag:
            teacher_id = random.randint(10000000000000, 99999999999999)
            if teacher_id not in all_teacher_id:
                flag = False

        return teacher_id

    except Exception as e:
        app.logger.debug(f"Error in get unique teacher: {e}")

def get_unique_admin_id(app, all_admin_id):
    """
    Get unique teacher id

    :param app: app-name
    :param all_teacher_id: registered all teacher ids
    :return: unique teacher id
    """
    try:
        flag = True
        while flag:
            admin_id = random.randint(1000000000000000, 9999999999999999)
            if admin_id not in all_admin_id:
                flag = False

        return admin_id

    except Exception as e:
        app.logger.debug(f"Error in get unique admin: {e}")

def password_validation(app, password):
    """
    Check password is validate or not

    :param app: app-name
    :param password: user password
    :return: True or False
    """
    try:
        capital = False
        number = False
        special_char = False
        special_char_list = ["@", "#", "$", "-", "_", "*"]
        for char in password:
            if char.isupper():
                capital = True
            try:
                char = int(char)
                number=True
            except:
                pass

            if char in special_char_list:
                special_char=True

        if capital and number and special_char:
            matching = True
        else:
            matching = False

        return matching

    except Exception as e:
        app.logger.debug(f"Error in validate password: {e}")

def validate_phone_number(app, phone_number):
    """
    Check phone number is validate or not

    :param app: app-name
    :param phone_number: user phone-number
    :return: True or False
    """
    try:
        # Parse the phone number
        parsed_number = phonenumbers.parse(phone_number, None)

        # Check if the number is valid
        is_valid = phonenumbers.is_valid_number(parsed_number)

        if is_valid:
            return "valid number"
        else:
            return "invalid number"

    except Exception as e:
        app.logger.debug(f"Error in validate password: {e}")

def get_admin_data(app, client, db_name, coll_name):
    """
    get all data from student, admin and teacher database table

    :param app: app-name
    :param client: mongo client
    :param db_name: database-name
    :param coll_name: collection-name
    :return: database_unique_keys and database_userdata
    """
    try:
        db = client[db_name]
        coll = db[coll_name]
        res = coll.find({})
        keys = []
        values = []
        for each_res in res:
            all_keys = list(each_res.keys())
            if all_keys[1:] not in keys:
                keys.append(all_keys[1:])

            all_values = list(each_res.values())
            values.append(all_values[1:])


        return keys[0], values

    except Exception as e:
        app.logger.debug(f"Error in get data from admin database: {e}")

def delete_panel_data(app, client, db_name, coll_name, delete_dict):
    """
    delete data from database

    :param app: app-name
    :param client: mongo-client
    :param db_name: database-name
    :param coll_name: collection-name
    :param delete_dict: condition dict
    :return: status
    """

    try:
        db = client[db_name]
        coll = db[coll_name]
        coll.delete_one(delete_dict)
        coll1 = db["login_mapping"]
        coll1.delete_one(delete_dict)
        return "data deleted"

    except Exception as e:
        app.logger.debug(f"Error in delete data from database: {e}")

def export_panel_data(app, database_data, panel, type):
    """
    export data for different format like csv, excel and csv

    :param app: app-name
    :param database_data: database data
    :param type: excel, csv, json
    :return: filename
    """

    try:
        if type=="excel":
            output_path = os.path.join(app.config["EXPORT_UPLOAD_FOLDER"], f"export_{panel}_excel.xlsx")
            df = pd.DataFrame(database_data)
            df.to_excel(output_path, index=False)
        elif type=="csv":
            output_path = os.path.join(app.config["EXPORT_UPLOAD_FOLDER"], f"export_{panel}_csv.csv")
            df = pd.DataFrame(database_data)
            df.to_csv(output_path, index=False)
        else:
            output_path = os.path.join(app.config["EXPORT_UPLOAD_FOLDER"], f"export_{panel}_json.json")
            with open(output_path, 'w') as json_file:
                json.dump(database_data, json_file, indent=2)

        return output_path

    except Exception as e:
        app.logger.debug(f"Error in export data from database: {e}")

def search_panel_data(app, client, db_name, search_value, coll_name):
    """
    search data from the database based on panel and search value

    :param app: app-name
    :param panel: panel
    :param search_value: id, name, phone numer, email
    :return: data regarding search value
    """

    try:
        if coll_name == "admin_data":
            """"""
        elif coll_name == "students_data":
            print("Inside students data column in college mgmnt database")
            db = client[db_name]
            print(f"db is : {db}")
            coll = db[coll_name]
            print(f"Coll is : {coll}")
            print(f"Search value : {search_value} and type is : {type(search_value)}")
            result = coll.find_one({'student_id':int(search_value)})
            print(f"Res is : {result}")
        else:
            """"""

        return result

    except Exception as e:
        app.logger.debug(f"Error in export data from database: {e}")
