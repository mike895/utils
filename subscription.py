import frappe
from stars_et.utils import notification, urlutils
import json

@frappe.whitelist(allow_guest=True)
def notify_subscriptions(call):
  users = frappe.db.sql("""
  SELECT
  *
  FROM
  `tabWebUser`
  WHERE
  (
    EXISTS (
      SELECT
        1
      FROM
        `tabRegion List`
      WHERE
        (`tabRegion List`.`parent` = `tabWebUser`.`name`)
        AND (`tabRegion List`.`region_item` IN (
            SELECT `tabRegion List`.`region_item` FROM `tabRegion List` WHERE `tabRegion List`.`parent` = %(call)s
        ))
    )
  )
  AND (
    EXISTS (
      SELECT
        1
      FROM
        `tabSector List`
      WHERE
        (`tabSector List`.`parent` = `tabWebUser`.`name`)
        AND (`tabSector List`.`sector_item` IN (
            SELECT `tabSector List`.`sector_item` FROM `tabSector List` WHERE `tabSector List`.`parent` = %(call)s
        ))
    )
  )
  """, {"call": call},as_dict=True, explain=True, formatted=1)
  call_doc = frappe.get_doc("Call", call)
  company = frappe.get_doc("Stars Company", call_doc.source)
  template : Document = frappe.get_doc("Notification Template", "Call Subscription Notification")
  for user in users:
    email = user.email
    phone = user.mobile_number
    args = {
      "call": json.loads(call_doc.as_json()),
      "user": json.loads(json.dumps(user, default=str)),
      "call_back": (call_doc.get_publ_background()),
      "company_logo": urlutils.public_url(company.logo),
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
        "subject":f"To the stars and beyond!",
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
        "link": f"/{call}",
        "message": template.text,
        "flair": "Opportunity",
        "title":template.sh_text,
        "args":args
      }
    })
  return {
    "sucess": True
  }