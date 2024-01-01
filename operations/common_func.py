"""
Maintain common function code like we can use all function in every where
"""

import logging
from datetime import datetime
from constant import constant_data
import random

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