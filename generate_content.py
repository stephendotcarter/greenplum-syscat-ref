import sys
import inflection
import json
import collections
import subprocess
from jinja2 import Environment, PackageLoader

(script_name, input_file_name) = sys.argv

graph_template_file_name = 'graph_template.jinja.dot'
label_template_file_name = 'label_template.jinja.dot'
html_template_file_name = 'html_template.jinja.html'

output_file_name = 'html/index.html'


def format_yesno(value):
    return "Yes" if str(value) == "1" else "No"


def format_unique(value):
    return "UNIQUE" if str(value) == "1" else ""


def format_underscore(value):
    return inflection.underscore(value)


def format_index_cols(values):
    temp = []
    for index in values:
        temp.append("<a>%s</a>" % index[0])
    return ", ".join(temp)


env = Environment(loader=PackageLoader('generate_content', '.'))

env.filters['yesno'] = format_yesno
env.filters['unique'] = format_unique
env.filters['underscore'] = format_underscore
env.filters['index_cols'] = format_index_cols

# Load Jinja templates
t_graph = env.get_template(graph_template_file_name)
t_label = env.get_template(label_template_file_name)
t_html = env.get_template(html_template_file_name)

sys.stdout.write("Reading catalog JSON from \"%s\" ... " % input_file_name)

input_file = open(input_file_name)
raw_catalog = json.load(input_file)

sys.stdout.write("DONE\n")

sys.stdout.write("Generating metadata ... ")

catalog = {
    'version': input_file_name[5:-5],
    'info': raw_catalog['__info'],
    'comment': raw_catalog['__comment'],
    'relations': collections.OrderedDict(),
}

catalog_metadata = {
    'fields': [
        'oid',
        'shared',
        'persistent',
        'master_only',
        'segment_local'
    ],
    'data': {
        'shared': [],
        'persistent': [],
        'master_only': [],
        'segment_local': [],
        'oid': []
    }
}

# unset the original values
del raw_catalog['__comment']
del raw_catalog['__info']


fks = []
for relname in sorted(raw_catalog.keys()):
    rel = raw_catalog[relname]
    rel['name'] = relname

    if rel['with']['oid'] == 1:
        rel['cols'] = [{
            "colname": "oid",
            "ctype": "Oid",
            "sqltype": "oid"
        }] + rel['cols']
        catalog_metadata['data']['oid'].append(relname)

    if rel['with']['shared'] == "1":
        catalog_metadata['data']['shared'].append(relname)        

    if 'content' in rel['with']:
        key = rel['with']['content'].lower()
        catalog_metadata['data'][key].append(relname)

    for col in rel['cols']:
        col['foreign_key'] = None
        col['reference_keys'] = []
    catalog['relations'][relname] = rel
    

for relname, rel in catalog['relations'].items():
    if 'foreign_keys' in rel:
        for fk in rel['foreign_keys']:
            new_fk = {
                'local_relname': relname,
                'local_colname': fk[0][0],
                'remote_relname': fk[1],
                'remote_colname': fk[2][0]
            }

            new_fk['local_id'] = "{0}.{1}".format(new_fk['local_relname'], new_fk['local_colname'])
            new_fk['remote_id'] = "{0}.{1}".format(new_fk['remote_relname'], new_fk['remote_colname'])

            fks.append(new_fk)

            # Save the local foreign key reference
            for col in rel['cols']:
                if col['colname'] == new_fk['local_colname']:
                    col['foreign_key'] = new_fk
                    break

            # Update the remote foreign key references
            if new_fk['remote_relname'] in catalog['relations']:
                remote_rel = catalog['relations'][new_fk['remote_relname']]
                
                for col in remote_rel['cols']:
                    if col['colname'] == new_fk['remote_colname']:
                        col['reference_keys'].append(new_fk)

            else:
                print ("We got a problem...")
                exit()


# Convert to list for easier templating
relnames = list(catalog['relations'].keys())
catalog['relationsByName'] = catalog['relations']
catalog['relations'] = list(catalog['relations'].values())

sys.stdout.write("DONE\n")


sys.stdout.write("Generating HTML ... ")

output_html = t_html.render(
    catalog=catalog,
    catalog_metadata=catalog_metadata
    )

output_file = open(output_file_name, 'w')
output_file.write(output_html)

sys.stdout.write("Done\n")


def build_relation_dot(rels):
    import copy
    uniq_rels = list(set(rels))
    for key, rel in enumerate(uniq_rels):
        this_rel = copy.copy(catalog['relationsByName'][rel])
        for col in this_rel['cols']:
            col['in_color'] = "#FFFFFF"
            col['out_color'] = "#FFFFFF"
            col['font_in_color'] = "#000000"
            col['font_out_color'] = "#95a5a6"
            this_id = "{0}.{1}".format(this_rel['name'], col['colname'])
                
            for fk in filtered_fks:
                # Local
                if this_id == fk['local_id']:
                    if fk['remote_port'] == 'in':
                        col['out_color'] = "#18bc9c"
                        col['font_out_color'] = "#FFFFFF"
                    elif fk['remote_port'] == 'out':
                        col['in_color'] = "#18bc9c"
                        col['font_in_color'] = "#FFFFFF"
                # Remote
                if this_id == fk['remote_id']:
                    if fk['remote_port'] == 'out':
                        col['out_color'] = "#18bc9c"
                        col['font_out_color'] = "#FFFFFF"
                    elif fk['remote_port'] == 'in':
                        col['in_color'] = "#18bc9c"
                        col['font_in_color'] = "#FFFFFF"

        
        uniq_rels[key] = {
            'relname': rel,
            'label': t_label.render(table=this_rel)
        }
    return uniq_rels


sys.stdout.write("Generating graphs:\n")

# Generate graphviz charts for each relation.
# Only include directly related relations
for relname in relnames:
    sys.stdout.write("  %s ... " % relname)

    # All fk entries that contain the relname
    filtered_fks = []

    # All relations that point in to relname
    filtered_rels_in = []

    # All relations that relname points out to
    filtered_rels_out = []

    for fk in fks:
        if fk['local_relname'] == relname or fk['remote_relname'] == relname:
            filtered_fks.append(fk)

        if fk['local_relname'] == relname:
            #print(fk['remote_relname'])
            #print(catalog['relationsByName'][fk['remote_relname']])
            filtered_rels_out.append(fk['remote_relname'])
        elif fk['remote_relname'] == relname:
            #print(fk['local_relname'])
            #print(catalog['relationsByName'][fk['local_relname']])
            filtered_rels_in.append(fk['local_relname'])
    
    for fk in fks:
        fk['penwidth'] = 1
        fk['color'] = "#2c3e50"
        fk['remote_port'] = 'in'
        fk['local_port'] = 'out'

        if fk['local_relname'] == fk['remote_relname']:
            fk['penwidth'] = 1
            fk['color'] = "#e74c3c"
            continue


        if fk['remote_relname'] in filtered_rels_in:
            fk['penwidth'] = 1
            fk['color'] = "#3498db"
            fk['remote_port'] = 'out'
            fk['local_port'] = 'in'
            continue
        

    rel_dot = build_relation_dot([relname])
    rels_in_dot = build_relation_dot(filtered_rels_in)
    rels_out_dot = build_relation_dot(filtered_rels_out)
    
    t_graph_dot = t_graph.render(
        relname=relname,
        clusters={
            'cluster_from': rels_in_dot,
            'cluster_selected': rel_dot,
            'cluster_to': rels_out_dot
        },
        fks=filtered_fks
    )

    # Write the dot file
    output_file = open('html/img/%s.dot' % relname, 'w')
    output_file.write(t_graph_dot)
    output_file.close()

    # Generate SVG and PNG
    subprocess.call(["dot", "-Tsvg", "html/img/{0}.dot".format(relname), "-o", "html/img/{0}.svg".format(relname)])
    subprocess.call(["dot", "-Tpng", "html/img/{0}.dot".format(relname), "-o", "html/img/{0}.png".format(relname)])

    sys.stdout.write("DONE\n")

sys.stdout.write("All ... DONE ^_^\n")
exit()
