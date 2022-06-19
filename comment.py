import frappe
from frappe.model.document import Document
import json
import requests
import re
import datetime
is_full_url = re.compile("^((http|https)(://))(((\S+)\.)+)(\S+)/(((\S+)(/?))+)")

from stars_et.utils.urlutils import public_url


def sendcomment(doc):
    eval_sub = frappe.get_doc("Evaluation Submission", doc.reference_name)
    call = frappe.get_doc("Call", eval_sub.call)
    owner = frappe.get_doc("Stars Company", call.source)
    frappe.get_doc({"doctype": "WebUser Notification", "user_id": eval_sub.user, "is_message": 1, "message_channel":eval_sub.name}).save(ignore_permissions=True)
    requests.post("https://app.stars.360magic.link/live_comment", json={
        "user": eval_sub.user,
    "content":{
        "is_you": 0,
        "content": doc.content,
        "modified": doc.modified,
        "sender": eval_sub.name,
        "logo": public_url(owner.logo),
		"owner": owner.name,
		"call": call.name,
        "last_modify":datetime.datetime.now().timestamp()*1000,
        "constructor": {
            "name": eval_sub.name,
            "flair": "Evaluation",
            "title": eval_sub.call,
            "logo": public_url(owner.logo),
            "uid": eval_sub.uid
        }
    }}).text


def sendcomment_complaint(doc):
    complaint = frappe.get_doc("Stars Complaint", doc.reference_name)
    frappe.get_doc({"doctype": "WebUser Notification", "user_id": complaint.complaintee, "is_message": 1, "message_channel":complaint.name}).save(ignore_permissions=True)
    requests.post("https://app.stars.360magic.link/live_comment", json={
        "user": complaint.complaintee,
    "content":{
        "is_you": 0,
        "content": doc.content,
        "modified": doc.modified,
        "sender": complaint.name,
        "logo": "/stars.svg",
        "last_modify":datetime.datetime.now().timestamp()*1000,
        "constructor": {
            "name": complaint.name,
            "flair": "Complaint",
            "title": "Complaint",
            "logo": "/stars.svg",
            "uid": complaint.code
        }
    }}).text

def notify(doc: Document,method=None):
    doctype = doc.reference_doctype
    if(doctype == "Evaluation Submission"):
        if("@applicant" in (doc.content or "")):
            sendcomment(doc)
    if(doctype == "Stars Complaint"):
        if("@complainant" in (doc.content or "")):
            sendcomment_complaint(doc)        
    pass