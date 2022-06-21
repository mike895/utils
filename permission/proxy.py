from frappe.desk.reportview import *
import frappe.desk.form.load as load
import importlib
import frappe.desk.form.save as save 


for_doctypes = ["Farm Profile","Ehpea Permission","Pesticide Purchase","Call", "Stars Permission", "Evaluation Submission", "Due Diligence", "Call Submission"]

def is_required_doctype(doctype=None):
    doctype = doctype or get_form_params().get("doctype") 
    return doctype in for_doctypes


def get_user_permission():
    if(frappe.session.user == "Administrator"):
        return "admin"
    try:
        return frappe.get_doc("Ehpea Permission", frappe.session.user)
    except:
        frappe.throw("You don't have a Ehpea Permission with your account.")
        raise Exception("You don't have a Ehpea Permission with your account.")


@frappe.whitelist()
def proxy_count():
    if(is_required_doctype()):
        doctype = get_form_params().get("doctype") 
        return importlib.import_module(f"ehpea.utils.permission.{doctype}").getcount(get_user_permission())
    else:
        return get_count()

@frappe.whitelist()
def proxy_save(doc, action):
    _doc = json.loads(doc)
    if(is_required_doctype(_doc['doctype'])):
        doc= _doc
        doctype = doc['doctype']
        return importlib.import_module(f"ehpea.utils.permission.{doctype}").save(get_user_permission(), doc, action)
    else:
        return save.savedocs(doc, action)

@frappe.whitelist()
def proxy_get():
    frappe.errprint("yess")
    if(is_required_doctype()):
        doctype = get_form_params().get("doctype") 
        return importlib.import_module(f"ehpea.utils.permission.{doctype}").getlist(get_user_permission())
    else:
        return get()

@frappe.whitelist()
def proxy_doc(doctype, name):
    if(is_required_doctype(doctype)):
        return importlib.import_module(f"ehpea.utils.permission.{doctype}").getdoc(name, get_user_permission())
    else:
        return load.getdoc(doctype, name)
        
        
        
