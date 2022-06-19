import frappe
import datetime
import os
import string
import random
import re
is_full_url = re.compile("^((http|https)(://))(((\S+)\.)+)(\S+)/(((\S+)(/?))+)")


from stars_et.utils.urlutils import public_url


def id_generator(size=6, chars=string.ascii_lowercase + string.ascii_uppercase + string.digits):
  return ''.join(random.choice(chars) for _ in range(size))

@frappe.whitelist()
def generate_certficate(template, company_name):
    import cairosvg
    template = frappe.get_doc("Certificate Template", template)
    renderable = template.svg_data.replace(template.name_place, company_name).replace('\n', ' ').replace('\r', '')
    renderable = renderable.replace(template.date_place, datetime.datetime.now().strftime("%b %d, %Y"))
    
    site_path = frappe.get_site_path('public', 'files')
    if not os.path.exists(os.path.join(site_path, "certs")):
        os.mkdir(os.path.join(site_path, "certs"))
    cert_id = id_generator(size=15)
    pdf_file_name = cert_id+".pdf"
    png_file_name = cert_id+".png"
    svg_file_name = cert_id+".svg"
    open(os.path.join(site_path, "certs", svg_file_name), mode="w+").write(renderable)
    cairosvg.svg2png(renderable, write_to=os.path.join(site_path, "certs", png_file_name))
    cairosvg.svg2pdf(renderable, write_to=os.path.join(site_path, "certs", pdf_file_name))
    return {
        "pdf": public_url(f"/files/certs/{pdf_file_name}"),
        "png": public_url(f"/files/certs/{png_file_name}"),
        "svg": public_url(f"/files/certs/{svg_file_name}")
    }