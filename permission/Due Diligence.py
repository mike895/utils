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
        else:
            args.conditions = "where "
        u_roles = ",".join([f"'{role}'" for role in self.u_roles])
        args.user = frappe.session.user
        query = f"""select %(fields)s
            from %(tables)s
            INNER JOIN `tabCall` ON `tabCall`.`name` = `tabDue Diligence`.`call`
            INNER JOIN `tabDue Diligence List` ON  `tabDue Diligence List`.`name` = `tabDue Diligence`.`dlg_id`
            AND `tabDue Diligence List`.`department` = '{self.department}'
            INNER JOIN `tabCall Submission` ON `tabCall Submission`.`name` = `tabDue Diligence`.`c_sub` 
            INNER JOIN `tabUser` ON `tabUser`.`name` = "%(user)s"
            INNER JOIN `tabStars Permission` ON `tabStars Permission`.`user` = `tabUser`.`name`
            %(conditions)s
            {
                f'''
                {"AND " if(self.conditions.__len__() > 0) else ""}
                `tabDue Diligence List`.`role` IN ({u_roles})
                '''
            }
            AND (NOT EXISTS(
			    SELECT 1 
			    FROM `tabSector List`
			    WHERE
			    `tabSector List`.`parent` =`tabCall Submission`.`name`
			    AND (`tabSector List`.`sector_item` NOT IN (SELECT `tabSector List`.`sector_item` FROM `tabSector List` WHERE `tabSector List`.`parent` = `tabStars Permission`.`name`))
			    ) OR (`tabStars Permission`.`all_sectors` = 1)) 
            AND (EXISTS(
			    SELECT 1 
			    FROM `tabRegion List`
			    WHERE
			    `tabRegion List`.`parent` = `tabStars Permission`.`name`
			    AND (`tabRegion List`.`region_item` = `tabCall Submission`.region)
			) OR (`tabStars Permission`.`all_regions` = 1)) 
            %(group_by)s
            %(order_by)s
            %(limit)s""" % args
        if self.return_query:
            return query
        else:
            return frappe.db.sql(query, as_dict=not self.as_list, debug=1,
                update=self.update, ignore_ddl=self.ignore_ddl)

@frappe.whitelist(allow_guest=True)
def getlist(permission):
    allowed_regions =  "all" if((permission == "admin") or (permission.all_regions == 1)) else ", ".join([f"'{i.region_item}'" for i in permission.regions]) 
    allowed_sectors = "all" if((permission == "admin") or (permission.all_sectors == 1)) else ", ".join([f"'{i.sector_item}'" for i in permission.sectors])
    args = lister.get_form_params()
    dbq = CustomDatabaseQuery("Due Diligence")
    dbq.u_roles = frappe.get_roles()
    dbq.department = "Stars.et" if(permission == "admin") else permission.department
    result = (lambda doctype, *args, **kwargs:  dbq.execute(*args, **kwargs, join="inner join",
    group_by="`tabDue Diligence`.`name`",
    with_childnames=True
    ))(**args)
    return result

def getcount(permission):
    allowed_regions =  "all" if((permission == "admin") or (permission.all_regions == 1)) else ", ".join([f"'{i.region_item}'" for i in permission.regions]) 
    allowed_sectors = "all" if((permission == "admin") or (permission.all_sectors == 1)) else ", ".join([f"'{i.sector_item}'" for i in permission.sectors])
    args = lister.get_form_params()
    distinct = 'distinct ' if args.distinct=='true' else ''
    args.fields = [f"count({distinct}`tabDue Diligence`.name) as total_count"]
    dbq = CustomDatabaseQuery("Due Diligence")
    dbq.regions = allowed_regions
    dbq.sectors = allowed_sectors
    dbq.u_roles = frappe.get_roles()
    dbq.department = "Stars.et" if(permission == "admin") else permission.department
    result = (lambda doctype, *args, **kwargs:  dbq.execute(*args, **kwargs))(**args)
    return result[0].get("total_count")

@frappe.whitelist(allow_guest=True)
def getdoc(name, permission):
    doctype = "Due Diligence"

    if not (doctype and name):
        raise Exception('doctype and name required!')
    if not name:
        name = doctype
    
    if not frappe.db.exists(doctype, name):
        return []

    try:
        doc = frappe.get_doc(doctype, name)
        call = frappe.get_doc("Call", doc.call) 
        submission = frappe.get_doc("Call Submission",doc.c_sub)
        d_dlg = [due for due in call.due_diligence if(due.name == doc.dlg_id)][0]
        roles = frappe.get_roles()
        (permission != "admin") and helper.is_role_allowed(d_dlg.role, roles, throw=True)

    
        helper.is_allowed(permission, [submission.region],
                          [i.sector_item for i in submission.sector]
                          ,d_dlg.department, department_first=True, throw=True)
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
        call = frappe.get_doc("Call", doc['call'])
        submission = frappe.get_doc("Call Submission",doc['c_sub'])
        d_dlg = [due for due in call.due_diligence if(due.name == doc['dlg_id'])][0]
        roles = frappe.get_roles()
        (permission != "admin") and helper.is_role_allowed(d_dlg.role, roles, throw=True)


        helper.is_allowed(permission, [submission.region],
                          [i.sector_item for i in submission.sector]
                          ,d_dlg.department, department_first=True, throw=True)
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