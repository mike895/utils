import frappe
import re
from urllib.parse import urlencode
is_full_url = re.compile("^((http|https)(://))(((\S+)\.)+)(\S+)/(((\S+)(/?))+)")

def public_url(url):
    if(type(url) is not str):
        return None
    if is_full_url.match(url) != None:
        return url.replace(" ", "%20")
    return frappe.utils.get_url(url).replace(" ", "%20")
