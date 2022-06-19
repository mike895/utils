import frappe
import frappe.desk.form.load as load
import frappe.desk.form.save as save_
import frappe.desk.reportview as lister
from stars_et.utils.permission import helper
from frappe.model.db_query import DatabaseQuery
from frappe import _
from frappe.desk.form.load import run_onload

class CustomDatabaseQuery(DatabaseQuery):
    def build_and_run(self):
        args = self.prepare_args()
        args.limit = self.add_limit()
        if args.conditions:
            args.conditions = "where " + args.conditions
        query = f"""select %(fields)s
            from %(tables)s
            INNER JOIN `tabCall` ON `tabCall`.`name` = `tabCall Submission`.`call`
            %(conditions)s
            {
                f'''
                {"AND " if(self.conditions.__len__() > 0) else "WHERE "} (`tabCall Submission`.`docstatus` = 1)
                '''
            }
            {f'''AND EXISTS(select 1 from `tabRegion List` 
                    where `tabRegion List`.`parent` = `tabCall`.`name`
                    AND  `tabRegion List`.`region_item`  IN ({self.regions}))''' if (self.regions != "all") else ""}
            {f'''AND EXISTS(select 1 from `tabSector List` 
                    where `tabSector List`.`parent` = `tabCall`.`name`
                    AND  `tabSector List`.`sector_item`  IN ({self.sectors}))''' if (self.sectors != "all") else ""}

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
    allowed_regions =  "all" if((permission == "admin") or (permission.all_regions == 1)) else ", ".join([f"'{i.region_item}'" for i in permission.regions]) 
    allowed_sectors = "all" if((permission == "admin") or (permission.all_sectors == 1)) else ", ".join([f"'{i.sector_item}'" for i in permission.sectors])
    args = lister.get_form_params()
    dbq = CustomDatabaseQuery("Call Submission")
    dbq.regions = allowed_regions
    dbq.sectors = allowed_sectors
    result = (lambda doctype, *args, **kwargs:  dbq.execute(*args, **kwargs, join="inner join",
    group_by="`tabCall Submission`.`name`",
    with_childnames=True
    ))(**args)
    return result

def getcount(permission):
    allowed_regions =  "all" if((permission == "admin") or (permission.all_regions == 1)) else ", ".join([f"'{i.region_item}'" for i in permission.regions]) 
    allowed_sectors = "all" if((permission == "admin") or (permission.all_sectors == 1)) else ", ".join([f"'{i.sector_item}'" for i in permission.sectors])
    args = lister.get_form_params()
    distinct = 'distinct ' if args.distinct=='true' else ''
    args.fields = [f"count({distinct}`tabCall Submission`.name) as total_count"]
    dbq = CustomDatabaseQuery("Call Submission")
    dbq.regions = allowed_regions
    dbq.sectors = allowed_sectors
    result = (lambda doctype, *args, **kwargs:  dbq.execute(*args, **kwargs))(**args)
    return result[0].get("total_count")

@frappe.whitelist(allow_guest=True)
def getdoc(name, permission):
    doctype = "Call Submission"

    if not (doctype and name):
        raise Exception('doctype and name required!')
    if not name:
        name = doctype
    
    if not frappe.db.exists(doctype, name):
        return []

    try:
        doc = frappe.get_doc(doctype, name)
        call_doc = frappe.get_doc("Call", doc.call)
        helper.is_allowed(permission, [i.region_item for i in call_doc.region_list], [i.sector_item for i in call_doc.sector_list], throw=True, all_match=False)
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
        helper.is_allowed(permission, [i['region_item'] for i in doc['region_list']], [i['sector_item'] for i in doc['sector_list']], throw=True)
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