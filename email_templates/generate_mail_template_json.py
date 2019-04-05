import os
import json


templates = [f.split('.')[0] for f in os.listdir('html')]

print('templates:', templates)

for template_name in templates:
    with open('templates/%s.json.tmpl' % template_name, 'r') as template_file:
        tmpl = template_file.read()

    with open('html/%s.html' % template_name) as f:
        html = f.read()

    with open('ses_templates/%s.json' % template_name, 'w') as f:
        f.write(tmpl % json.dumps(html))

