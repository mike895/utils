import frappe
import frappe.desk.form.load as load
import frappe.desk.form.save as save_
import frappe.desk.reportview as lister
from ehpea.utils.permission import helper
from frappe.model.db_query import DatabaseQuery
from frappe import _
from frappe.desk.form.load import run_onload

class CustomDatabaseQuery(DatabaseQuery): 
    def build_and_run(self):   # all_regions = all_farm and region_item = farm and regions = farms
        args = self.prepare_args()
        args.limit = self.add_limit()
        if args.conditions:
            args.conditions = "where " + args.conditions
        elif (self.farms != "all"):
            args.conditions = "where "
        query = f"""select %(fields)s
            from %(tables)s
            %(conditions)s
            {f'''{"AND " if(self.conditions.__len__() > 0) else ""}NOT EXISTS(select 1 from `tabSelected Farm` 
                    where `tabSelected Farm`.`parent` = `tabWater Efficiency`.`name`
                    AND  `tabSelected Farm`.`farm` NOT IN ({self.farms}))''' if (self.farms != "all") else ""}
            %(group_by)s
            %(order_by)s
            %(limit)s""" % args
        if self.return_query:
            return query
        else:
            return frappe.db.sql(query, as_dict=not self.as_list, debug=self.debug,
                update=self.update, ignore_ddl=self.ignore_ddl)

@frappe.whitelist(allow_guest=True)
def getlist(permission):
    allowed_farms =  "all" if((permission == "admin") or (permission.all_farm == 1)) else ", ".join([f"'{i.farm}'" for i in permission.farm]) 
    args = lister.get_form_params()
    dbq = CustomDatabaseQuery("Water Efficiency")
    dbq.farms = allowed_farms
    result = (lambda doctype, *args, **kwargs:  dbq.execute( join="inner join",
    group_by="`tabWater Efficiency`.`name`",
    with_childnames=True
    ))(**args)
    return result

def getcount(permission):
    allowed_farms =  "all" if((permission == "admin") or (permission.all_farm == 1)) else ", ".join([f"'{i.farm}'" for i in permission.farm]) 
    args = lister.get_form_params()
    distinct = 'distinct ' if args.distinct=='true' else ''
    args.fields = [f"count({distinct}`tabWater Efficiency`.name) as total_count"]
    dbq = CustomDatabaseQuery("Water Efficiency")
    dbq.farms = allowed_farms
    result = (lambda doctype, *args, **kwargs:  dbq.execute(*args, **kwargs))(**args)
    return result[0].get("total_count")

@frappe.whitelist(allow_guest=True)
def getdoc(name, permission):
    doctype = "Water Efficiency"

    if not (doctype and name):
        raise Exception('doctype and name required!')
    if not name:
        name = doctype
    
    if not frappe.db.exists(doctype, name):
        return []

    try:
        doc = frappe.get_doc(doctype, name)
        helper.is_allowed(permission, [i.farm for i in doc.farm], throw=True, all_match=False)
        load.run_onload(doc)
        if not doc.has_permission("read"):
            frappe.flags.error_message = _('Insufficient Permission for {0}').format(frappe.bold(doctype + ' ' + name))
            raise frappe.PermissionError(("read", doctype, name))

        doc.apply_fieldlevel_read_permissions()

        # add file list
        doc.add_viewed()
        load.get_docinfo(doc)

    except Exception:
        frappe.errprint(frappe.utils.get_traceback())
        raise

    doc.add_seen()

    frappe.response.docs.append(doc)

@frappe.whitelist()
def save(permission, doc, action):
    """save / submit / update doclist"""
    try:
        helper.is_allowed(permission, [i['farm'] for i in doc['farm']], throw=True)
        doc = frappe.get_doc(doc)
        save_.set_local_name(doc)
        # action
        doc.docstatus = {"Save":0, "Submit": 1, "Update": 1, "Cancel": 2}[action]
        if doc.docstatus==1:
            doc.submit()
        else:
            doc.save()

        # update recent documents
        run_onload(doc)
        save_.send_updated_docs(doc)

        frappe.msgprint(frappe._("Saved"), indicator='green', alert=True)
    except Exception:
        frappe.errprint(frappe.utils.get_traceback())
        raise
        
