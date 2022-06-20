from ehpea.ehpea.doctype.ehpea_permission.ehpea_permission import EhpeaPermission
#from stars_et.stars_et.doctype.stars_department.stars_department import StarsDepartment
from typing import Union
import frappe
def remove_else(container, child):
    return list(set(container) - set(child))

def is_role_allowed(required_role, my_roles, throw=False):
    if(required_role not in my_roles):
        if(throw): raise Exception("You don't have permission for this document!")
        return False
    return True


def is_allowed(permission:Union[EhpeaPermission, str], farms:list, throw=False, all_match=True):
#    if(department_first):
#        if(( permission.department if(permission != "admin") else "Stars.et") != department):
#            if(throw): raise Exception("You don't have permission for this department.")
#            return False
    if(permission == "admin"):
        return True
    if(permission.all_farm != 1):   # all_regions = all_farm and region_item = farm and regions = farms
        allowed_farms = [i.farm for i in permission.farms]
        if(not (all if(all_match) else any)(region in allowed_farms for farm in farms)):
            if(throw): raise Exception(f"You don't have permission for those farms {', '.join(remove_else(farms, allowed_farms))}.")
            return False            
    return True
    
