import frappe
from stars_et.utils import notification
from stars_et.stars_et.doctype.call.call import Call
from typing import List
import json
import jinja2


def do_broadcast(call: Call, submission, handler, extras):
    recipients: List[[str,
                      str]] = [[result.recipient, result.recipient_email]
                               for result in frappe.db.sql("""
		SELECT 
		DISTINCT `tabUser`.`name` as `recipient`,
		`tabUser`.`email` as `recipient_email`
		FROM `tabEvent Notification`
        INNER JOIN `tabCall` ON `tabCall`.`name` = `tabEvent Notification`.`parent`
		INNER JOIN `tabHas Role` ON `tabHas Role`.`role` = `tabEvent Notification`.`role`
		INNER JOIN `tabUser` ON `tabHas Role`.`parent` = `tabUser`.`name`
		INNER JOIN `tabStars Permission` ON `tabStars Permission`.`user` = `tabUser`.`name`
		AND (`tabStars Permission`.`department` = `tabEvent Notification`.`department`)
		AND (NOT EXISTS(
			SELECT 1 
			FROM `tabSector List`
			WHERE
			`tabSector List`.`parent` = %(submission)s
			AND (`tabSector List`.`sector_item` NOT IN (SELECT `tabSector List`.`sector_item` FROM `tabSector List` WHERE `tabSector List`.`parent` = `tabStars Permission`.`name`))
			) OR (`tabStars Permission`.`all_sectors` = 1))

		AND (EXISTS(
			SELECT 1 
			FROM `tabRegion List`
			WHERE
			`tabRegion List`.`parent` = `tabStars Permission`.`name`
			AND (`tabRegion List`.`region_item` = %(region)s)
			) OR (`tabStars Permission`.`all_regions` = 1))

		WHERE
		`tabEvent Notification`.`name`=  %(event_id)s
		AND `tabEvent Notification`.`parent`= %(call)s
		""", {
                                   "event_id": handler.name,
                                   "call": call.name,
								   "region": submission.region,
								   "submission": submission.name
            },as_dict=True)]
    print(f"Notification Recipients", recipients)
    template = frappe.get_doc("Notification Template", handler.template)
    sh_text =(handler.with_notification==1) and jinja2.Template(template.sh_text).render({
                        "call":call,
                        **extras
                    })
    email_text =(handler.with_email==1) and jinja2.Template(template.html).render({
                        "call":call,
                        **extras
                    })
    raw_text =  jinja2.Template(template.text).render({
                        "call":call,
                        **extras
                    }) if (len(template.text or "") > 0) else sh_text		        
    for recipient in recipients:
        notification.conditional_notify(
				payload={
					"email": {
						"to": recipient[1],
						"subject": "New evaluation is pending to be performed!",
						"htmltemplate":email_text,
						"texttemplate": raw_text,
						"args": {}
					}
				},
				is_email_available=(handler.with_email==1),
				desk_notificaiton={
					"type": "sys",
					"payload": {
						"user":recipient[0], #(recipient, recipient_email)
						"type":"Alert",
						"document_type":
						"Call Submission",
						"document_name":
						submission,
						"subject": sh_text
					}
				} if (handler.with_notification==1) else None)

@frappe.whitelist()
def guess_effect(content):
	"""
	{
		"is_region",
		"is_sector",
		"role",
		"department",
		"regions",
		"sectors"
	}
	"""
	content = json.loads(content)
	is_subset = ("is_subset" in content) and (content["is_subset"])
	events : List[dict] = content['events']
	recipients = []
	for event in events:
		query = """
		SELECT 
		DISTINCT `tabUser`.`name` as `user`,
		`tabUser`.`email` as `email`,
		`tabUser`.`full_name` as `full_name`,
		CONCAT('[', (SELECT GROUP_CONCAT(CONCAT('"',`tabRegion List`.`region_item`,'"'))  FROM `tabRegion List`  WHERE `tabRegion List`.`parent` = `tabStars Permission`.`name`) , ']') as `regions`,
		CONCAT('[', (SELECT GROUP_CONCAT(CONCAT('"',`tabSector List`.`sector_item`,'"'))  FROM `tabSector List`  WHERE `tabSector List`.`parent` = `tabStars Permission`.`name`) , ']') as `sectors`,
		CONCAT('[', (SELECT GROUP_CONCAT(CONCAT('"',`tabHas Role`.`role`,'"'))  FROM `tabHas Role`  WHERE `tabHas Role`.`parent` = `tabUser`.`name`) , ']') as `roles`,
		`tabStars Permission`.`all_regions` as `all_regions`,
		`tabStars Permission`.`all_sectors` as `all_sectors`
		FROM `tabUser`
		INNER JOIN `tabStars Permission` ON `tabStars Permission`.`user` = `tabUser`.`name`
		AND (`tabStars Permission`.`department` = %(department)s)
		"""
		results: List[dict] = [{**result, "regions": json.loads(result['regions'] or "[]"), "sectors": json.loads(result['sectors']  or "[]"), "roles": json.loads(result['roles']  or "[]")} for result in frappe.db.sql(query, {
				#"regions": event['regions'],
				#"sectors": event['sectors'],
				#"role": event['role'],
				"department": event['department']
            },as_dict=True, debug=1)]
		real_results = []
		for result in results:

			if( ((any([region in  content['regions'] for region in result['regions']])  if(is_subset) else  set(content['regions']).issubset(result['regions'])) or (result['all_regions'] == 1)) 
			and ((any([sector in  content['sectors'] for sector in result['sectors']])  if(is_subset) else set(content['sectors']).issubset(result["sectors"])) or (result['all_sectors'] == 1))
			and (set(event['role']	if(type(event['role']) is list) else [event['role']]).issubset(result['roles']))):
				real_results.append(result)
		recipients.append({"users": real_results,
			"meta":event['meta']
			})
	return {"results": recipients}


def broadcast(event: str, call: str, submission: frappe.model.document.Document, extras={}):
	print(f"------------ Broadcasting an event started (Event: {event}) (Call: {call}) ----------------")
	call_doc = frappe.get_doc("Call", call) if (type(call) is str) else call
	handlers = [
		handler for handler in call_doc.event_notification
		if (handler.event == event)
	]
	for handler in handlers:
		do_broadcast(call_doc, submission, handler,extras)
	print(f"------------ Broadcasting an event ended (Event: {event}) (Call: {call}) ----------------")
