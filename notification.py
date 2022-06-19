import requests
import frappe
import jinja2
import traceback

baseUrl = "http://localhost:9521"

def notify_all(payload):
    """
    payload = {
        "sms": {
            "to": "+....",
            "template": "",
            "args": {}
        },
        "email": {
            "to": "",
            "subject": "",
            "htmltemplate": "",
            "texttemplate": "",
            "args": {}
        }
    }
    """
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.request("POST", f"{baseUrl}/notification/all", json=payload, headers=headers)
        return response.text
    except:
        traceback.print_exc()
        return None

def notify_phone(payload):
    """
    {
       "to": "string",
       "template": "string",
       "args": {}
    }
    """
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.request("POST", f"{baseUrl}/notification/sms", json=payload, headers=headers)
        return response.text
    except:
        traceback.print_exc()
        return None

def notify_email(payload):
    """
    {
        "to": "string",
        "subject": "string",
        "htmltemplate": "string",
        "texttemplate": "string",
        "args": {}
    }
    """
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.request("POST", f"{baseUrl}/notification/email", json=payload, headers=headers)
        return response.text
    except:
        traceback.print_exc()
        return None

def notify_telegram(payload):
    """
    {
        "id": 0,
        "message":""
    }
    """
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.request("POST", f"{baseUrl}/notification/telegram", json=payload, headers=headers)
        return response.text
    except:
        traceback.print_exc()
        return None


def notify_webuser(payload):
    notification = frappe.get_doc({
        "doctype":"WebUser Notification",
        "user_id": payload["user"],
        "link": payload["link"],
        "title": payload["title"],
        "small_text": jinja2.Template(payload["message"]).render(payload["args"]),
        "flair": payload["flair"]
    })
    notification.save(ignore_permissions=True)
    frappe.db.commit()



def notify_user(payload: dict):
    notification = frappe.get_doc({
        "doctype": "Notification Log",
        "for_user": payload["user"],
        "type": payload["type"],
        "document_type": payload["document_type"],
        "document_name": payload["document_name"],
        "subject": payload["subject"]
    })
    notification.insert(ignore_permissions=True)
    frappe.db.commit()



def conditional_notify(payload=None, is_phone_available=False, is_email_available=False, is_telegram_available=False, desk_notificaiton=None):
    if(desk_notificaiton is not None):
        if(desk_notificaiton["type"] == "web"):
            notify_webuser(desk_notificaiton["payload"])
        elif(desk_notificaiton["type"] == "sys"):
            notify_user(desk_notificaiton["payload"])
    if(is_email_available and is_phone_available and is_telegram_available):
        notify_all(payload)
    else:  
        if(is_phone_available):
            notify_phone(payload["sms"])
        if(is_email_available):
            notify_email(payload["email"])
        if(is_telegram_available):
            notify_telegram(payload["telegram"])    

