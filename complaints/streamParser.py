# Stream json data
import json
import ijson
import urllib

# Temp File Creation
import os



def parse_json(input_url_path, output_file_name):
    # Saves downloaded file - on failure this file will remain for inspection
    tmp_file_name = "todaysData.json"

    if not os.path.isfile(tmp_file_name):
        download_file = urllib.URLopener()
        download_file.retrieve(input_url_path, tmp_file_name)

    parse_json_file(tmp_file_name, output_file_name)

    try:
        os.remove(tmp_file_name)
    except OSError:
        print "Failed temp file removal in fake_crdb_data.py"
        pass

def parse_json_file(input_file_name, output_file_name):
    target = open(output_file_name, 'w')

    with open(input_file_name,'r') as f:
        parser = ijson.parse(f)

        my_data_array = []
        my_column_array = []

        for prefix, event, value in parser:
            if prefix == 'data.item.item':
                my_data_array.append(value)
            elif (prefix, event) == ('data.item', 'start_array'):
                continue
                n += 1
            elif (prefix, event) == ('data.item', 'end_array'):
                new_complaint = dict(zip(my_column_array, my_data_array))
                new_complaint["has_narrative"] = (not (not new_complaint["complaint_what_happened"] or len(new_complaint["complaint_what_happened"]) == 0))

                if new_complaint["tags"] == None:
                    new_complaint["tags"] = []
                else:
                    new_complaint["tags"] = new_complaint["tags"].split(", ")

                my_data_array = []
                target.write(json.dumps(new_complaint))
                target.write('\n')
            elif prefix == 'meta.view.columns.item.fieldName':
                my_column_array.append(value)

__all__ = ['parse_json']
