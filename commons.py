import frappe
from stars_et.utils import notification
import json

def notify_final_result(call_sub: frappe.model.document.Document, passed):
    call = frappe.get_doc("Call", call_sub.call)
    user = frappe.get_doc("WebUser", call_sub.applicant)
    company = frappe.get_doc("Stars Company", call_sub.company)
    template = frappe.get_doc("Notification Template",  call.app_pass if passed else call.app_fail)
    email = user.email 
    phone = user.mobile_number
    args = {
			"call_sub": json.loads(call_sub.as_json()),
			"call": json.loads(call.as_json()),
			"user": json.loads(user.as_json()),
            "company": json.loads(company.as_json())
		}
    notification.conditional_notify({ #Notification handler
        "sms": {
            "to": phone,
            "template": template.text,
            "args": args
        },
        "email": {
            "to":email,
            "subject":f"We recieved your application for {call.name}",
            "htmltemplate": template.html,
            "texttemplate": template.text,
            "args": args
        },
        "telegram": {
            "id": int(user.telegram) if(user.telegram_linked == 1) else 0,
            "message": template.text,
            "args":args
        }
    }, len(phone or "")>0, len(email or "") > 0, (user.telegram_linked == 1), {
        "type":"web",
        "payload": {
            "user": user.name,
            "link": f"/profile/applications",
            "message": template.text,
            "flair": "Evaluation",
            "title":template.sh_text,
            "args":args
        }
    })


@frappe.whitelist()
def commons():
    return {
        "regions":[i.name for i in frappe.get_list("Region",  fields=["name"])],
        "sectors":[i.name for i in frappe.get_list("Sector", fields=["name"])]
    }