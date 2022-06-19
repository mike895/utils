import frappe
from frappe.model.document import Document
import stars_et


def create_submission(new_step, application, num):
	submission :Document = frappe.new_doc("Evaluation Submission")
	submission.call = application.call
	submission.can_fail = new_step.can_fail
	submission.user = application.applicant
	submission.submission = application.name
	submission.num = num
	submission.step_name = f"{new_step.step_name}" + (f" ({num+1})" if (num > 0) else "")
	submission.uid = new_step.step_id
	submission.type = new_step.ev_type
	submission.req_html_hidden = new_step.note
	composed_input_html = ""
	for req in (new_step.data_req or "").split(","):
		req_name : str = req.strip()
		if(len(req_name) <= 0):
			continue
		req_doc : Document = frappe.get_list("Evaluation Submission", filters={
			"call": application.call,
			"uid": req_name,
			"submission": application.name,
			"docstatus":1
		}, fields="*")
		if(len(req_doc) <= 0):
			continue
		output = ""
		if(req_doc[0].type == "Scored Evaluation"):
			for ind,req_doc_item in enumerate(req_doc):
				output += f"<b>Evaluation #{ind+1}</b><br/>{req_doc_item.total_score}<br/><br/>"
		else:
			for ind,req_doc_item in enumerate(req_doc):
				output += f"<b>Evaluation #{ind+1}</b><br/>{req_doc_item.html_output_text}<br/><br/>"
		title = req_doc[0].step_name
		composed_input_html += f"<div><h3>{title}</h3>{output}</div><br/>"

	submission.input_html_hidden = 	composed_input_html
	if(new_step.ev_type == "Scored Evaluation"):
		template :  Document = frappe.get_doc("Evaluation Template",new_step.template) 
		for templ in template.template:
			submission.append("html_output_list", {
				"step_name": templ.criteria,
				"weight": templ.weight,
				"hidden_html": frappe.render_template("templates/step_note.html", {
					"description": templ.description,
					"attachments":  frappe.get_doc("Criteria Attachment", templ.attachments).attachment_list if(len(templ.attachments or "") > 0) else []
				})
				})
	submission.insert(ignore_permissions=True)
	return submission.name


def do_evaluation(application, new=False): #TODO: do_evaluation
	call = frappe.get_doc("Call", application.call)
	new_step = call.evaluation_steps[0] if(new) else ""
	for i in range(int(new_step.evlt_amt)):
		create_submission(new_step, application, i)
	frappe.db.commit()
	return new_step