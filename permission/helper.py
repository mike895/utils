from stars_et.stars_et.doctype.stars_permission.stars_permission import StarsPermission
from stars_et.stars_et.doctype.stars_department.stars_department import StarsDepartment
from typing import Union
import frappe
def remove_else(container, child):
    return list(set(container) - set(child))

def is_role_allowed(required_role, my_roles, throw=False):
    if(required_role not in my_roles):
        if(throw): raise Exception("You don't have permission for this document!")
        return False
    return True


def is_allowed(permission:Union[StarsPermission, str], regions:list, sectors:list, department: StarsDepartment = None, throw=False, department_first=False, all_match=True):
    if(department_first):
        if(( permission.department if(permission != "admin") else "Stars.et") != department):
            if(throw): raise Exception("You don't have permission for this department.")
            return False
    if(permission == "admin"):
        return True
    if(permission.all_regions != 1):
        allowed_regions = [i.region_item for i in permission.regions]
        if(not (all if(all_match) else any)(region in allowed_regions for region in regions)):
            if(throw): raise Exception(f"You don't have permission for those regions {', '.join(remove_else(regions, allowed_regions))}.")
            return False
    if(permission.all_sectors != 1):
        allowed_sectors = [i.sector_item for i in permission.sectors]
        if(not (all if(all_match) else any)(sector in allowed_sectors for sector in sectors)):
            if(throw): raise Exception(f"You don't have permission for those sectors {', '.join(remove_else(sectors, allowed_sectors))}.")
            return False 
    if(department and not department_first):
        if((permission.department) != department):
            if(throw): raise Exception("You don't have permission for this department.")
            return False              
    return True
    