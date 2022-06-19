import requests

def add_node(url:str, change_freq:str="daily"):
    requests.post("https://app.stars.360magic.link/sitemap_access/M_4_T9_8_F_I_E4", json= {
        "url": url.replace(" ", "%20"),
        "change_freq": change_freq,
        "access_key": "MS-4C9F783%^!@4YT_J'ITUE4T"
    })