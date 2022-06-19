from frappe.model.document import Document
from algoliasearch.search_client import SearchClient
from io import StringIO
from html.parser import HTMLParser

client = SearchClient.create('ZF4ZNYJV04', 'e3004390fba361e8634dba89c11ca9a6')
index = client.init_index('dev_stars')

#previous
#1WN8V37WWO
#6dedad05dd3b82f5280cac9c1e3c0c5c

def add_index(doc:{}):
    return index.save_objects([
        {"objectID": f"{doc['type']}-{doc['name']}" , **doc}
    ])

def delete_index(doc:{}):
    return index.delete_object(f"{doc['type']}-{doc['name']}")







class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.text = StringIO()
    def handle_data(self, d):
        self.text.write(d)
    def get_data(self):
        return self.text.getvalue()

def strip_html_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()
