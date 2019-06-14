from __future__ import absolute_import

from celery import shared_task

from tools import send_email_tool


@shared_task
def async_send_email(email, verify_type):
    """异步发送邮件
    :param email: string
    :param verify_type: int
    :return: bool. if successfully send email return True else return False
    """
    send_success = send_email_tool.send_email_code(email=email, verify_type=verify_type)
    return send_success