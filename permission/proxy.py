from frappe.desk.reportview import *
import frappe.desk.form.load as load
import importlib
import frappe.desk.form.save as save 


for_doctypes = ["Action Plan", "Bio Agent Introduction", "Bio Agent Purchase", "Certification", "Ehpea Permission", "Energy", "Fertilizer", "Food safety Lab", "Fuel", "Gender Audit Checklist IRMS part1", "Gender Audit Checklist IRMS part2", "Gender Audit Checklist IRMS part3", "Gender Grievance Handling", "Genders Grievance Management", "Green waste Management checklist", "Implementation of pest management", "Implementation of pest management part 2", "Implementation of pest management part 3", "Landscape and natural conservation audit", "Liquid Waste Management", "Liquid Waste Management Part2", "List of Species", "Meeting Minutes", "Pesticide Application", "Pesticide Purchase", "Training Attendance", "Training Plan", "Water Efficiency", "Water Record", "Workers Walfare OSH", "Workers Walfare OSH part 2", "Workers Walfare OSH part 3"]

def is_required_doctype(doctype=None):
    doctype = doctype or get_form_params().get("doctype") 
    return doctype in for_doctypes


def get_user_permission():
    if(frappe.session.user == "Administrator"):
        return "admin"
    try:
        test = frappe.get_doc("Ehpea Permission", frappe.session.user)
        return test # frappe.get_doc("Ehpea Permission", frappe.session.user)
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
        
        
        
