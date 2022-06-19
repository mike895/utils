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
        query = f"""select %(fields)s
            from %(tables)s
            INNER JOIN `tabCall` ON `tabCall`.`name` = `tabEvaluation Submission`.`call`
            INNER JOIN `tabEvaluation Step` ON `tabEvaluation Step`.`step_id` = `tabEvaluation Submission`.`uid` 
            INNER JOIN `tabCall Submission` ON `tabCall Submission`.`name` = `tabEvaluation Submission`.`submission` 
            AND `tabEvaluation Step`.`parent` = `tabCall`.`name`
            AND `tabEvaluation Step`.`department` = '{self.department}'
            %(conditions)s
            {
                f'''
                {"AND " if(self.conditions.__len__() > 0) else ""}
                `tabEvaluation Step`.`step_evaluator` IN ({u_roles})
                '''
            }
            {f'''AND ((`tabCall Submission`.`region` IN ({self.regions})))
                                        ''' if (self.regions != "all") else ""}
            {f'''AND (NOT EXISTS(select 1 from `tabSector List` 
                    where `tabSector List`.`parent` = `tabCall Submission`.`name`
                    AND  `tabSector List`.`sector_item` NOT IN ({self.sectors})))''' if (self.sectors != "all") else ""}
            {f'''AND ((`tabEvaluation Submission`.`docstatus` != 1) OR (`tabEvaluation Submission`.`submitter` = "{frappe.session.user}"))''' if (not self.see_all_eval) else ""}
            {f'''
            AND  ((`tabEvaluation Submission`.`submitter` = "{frappe.session.user}")  OR NOT EXISTS(SELECT 1 FROM `tabEvaluation Submission` WHERE (`tabEvaluation Submission`.`submitter` = "{frappe.session.user}") 
            AND (`tabEvaluation Submission`.`submission` = `tabCall Submission`.`name`)
            AND (`tabEvaluation Submission`.`uid` = `tabEvaluation Step`.`step_id`)
            ))
            ''' if (not self.more_once) else ""}                       
            %(group_by)s
            %(order_by)s
            %(limit)s""" % args

        if self.return_query:
            return query
        else:
            return frappe.db.sql(query,
                                 as_dict=not self.as_list,
                                 debug=self.debug,
                                 update=self.update,
                                 ignore_ddl=self.ignore_ddl)


@frappe.whitelist(allow_guest=True)
def getlist(permission):
    allowed_regions = "all" if ((permission == "admin") or
                                (permission.all_regions == 1)) else ", ".join([
                                    f"'{i.region_item}'"
                                    for i in permission.regions
                                ])
    allowed_sectors = "all" if ((permission == "admin") or
                                (permission.all_sectors == 1)) else ", ".join([
                                    f"'{i.sector_item}'"
                                    for i in permission.sectors
                                ])
    args = lister.get_form_params()
    dbq = CustomDatabaseQuery("Evaluation Submission")
    dbq.regions = allowed_regions
    dbq.sectors = allowed_sectors
    dbq.not_all = not args.all_results
    dbq.see_all_eval = ((permission == "admin") or (permission.pen_eval == 1))
    dbq.more_once = (args.all_results) or ((permission == "admin") or (permission.more_once == 1))
    dbq.u_roles = frappe.get_roles()
    dbq.department = "Stars.et" if (permission
                                    == "admin") else permission.department
    result = (lambda doctype, all_results=None, *args, **kwargs: dbq.execute(
        *args,
        **kwargs,
        join="inner join",
        group_by="`tabEvaluation Submission`.`name`",
        with_childnames=True))(**args)
    return result


def getcount(permission):
    allowed_regions = "all" if ((permission == "admin") or
                                (permission.all_regions == 1)) else ", ".join([
                                    f"'{i.region_item}'"
                                    for i in permission.regions
                                ])
    allowed_sectors = "all" if ((permission == "admin") or
                                (permission.all_sectors == 1)) else ", ".join([
                                    f"'{i.sector_item}'"
                                    for i in permission.sectors
                                ])
    args = lister.get_form_params()
    distinct = 'distinct ' if args.distinct == 'true' else ''
    args.fields = [
        f"count({distinct}`tabEvaluation Submission`.name) as total_count"
    ]
    dbq = CustomDatabaseQuery("Evaluation Submission")
    dbq.regions = allowed_regions
    dbq.sectors = allowed_sectors
    dbq.more_once = (args.all_results) or ((permission == "admin") or (permission.more_once == 1))
    dbq.see_all_eval = ((permission == "admin") or (permission.pen_eval == 1))
    dbq.u_roles = frappe.get_roles()
    dbq.department = "Stars.et" if (permission
                                    == "admin") else permission.department
    result = (lambda doctype, *args, **kwargs: dbq.execute(*args, **kwargs))(
        **args)
    return result[0].get("total_count")


@frappe.whitelist(allow_guest=True)
def getdoc(name, permission):
    doctype = "Evaluation Submission"

    if not (doctype and name):
        raise Exception('doctype and name required!')
    if not name:
        name = doctype

    if not frappe.db.exists(doctype, name):
        return []

    try:
        doc = frappe.get_doc(doctype, name)
        submission = frappe.get_doc("Call Submission",doc.submission)
        call = frappe.get_doc("Call", doc.call)
        step = [
            step for step in call.evaluation_steps if step.step_id == doc.uid
        ][0]
        roles = frappe.get_roles()
        (permission != "admin") and helper.is_role_allowed(
            step.step_evaluator, roles, throw=True)

        if not((permission == "admin") or (permission.pen_eval == 1) or ((doc.submitter == None) or (doc.submitter == frappe.session.user))):
            frappe.throw("You don't own this evaluation")
        if (permission != "admin"):

            
            if(((doc.submitter != frappe.session.user)) and ((permission.pen_eval != 1) and (len(frappe.get_list("Evaluation Submission", filters={
                "submitter": frappe.session.user,
                "submission": doc.submission,
                "uid": doc.uid,
                'docstatus': ['!=', 2],
                'name': ['!=', doc.name]
            })) > 0)) and (not ((permission.more_once == 1) and (doc.submitter == None)))):
                frappe.throw(
                    _("You don't have access to this evaluation CODE:<b>DUPENTRY</b>."
                        ))
        helper.is_allowed(permission,
                          [submission.region],
                          [i.sector_item for i in submission.sector],
                          step.department,
                          throw=True)
        load.run_onload(doc)
        if not doc.has_permission("read"):
            frappe.flags.error_message = _(
                'Insufficient Permission for {0}').format(
                    frappe.bold(doctype + ' ' + name))
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
        submission = frappe.get_doc("Call Submission",doc['submission'])
        call = frappe.get_doc("Call", doc['call'])
        step = [
            step for step in call.evaluation_steps
            if step.step_id == doc['uid']
        ][0]
        if not((permission == "admin") or ((( 'submitter' not in doc) or (doc['submitter'] == None)) or (('submitter' in doc) and (doc["submitter"] == frappe.session.user)))):
            frappe.throw("You don't own this evaluation")
        roles = frappe.get_roles()
        (permission != "admin") and helper.is_role_allowed(
            step.step_evaluator, roles, throw=True)
        if (permission != "admin"):

            if((permission.more_once != 1) and (len(frappe.get_list("Evaluation Submission", filters={
                "submitter": frappe.session.user,
                "submission": doc['submission'],
                "uid": doc['uid'],
                'docstatus': ['!=', 2],
                'name': ['!=', doc['name']]
            })) > 0)):
                frappe.throw(
                    _("You can't save another evaluation for this submission!"
                        ))
        helper.is_allowed(permission,
                            [submission.region],
                            [i.sector_item for i in submission.sector],
                            step.department,
                            throw=True)
        doc = frappe.get_doc(doc)
        save_.set_local_name(doc)
        # action
        doc.docstatus = {
            "Save": 0,
            "Submit": 1,
            "Update": 1,
            "Cancel": 2
        }[action]
        if doc.docstatus == 1:
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