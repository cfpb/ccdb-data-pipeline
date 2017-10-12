# Stream json data
import json
import ijson
import urllib
import requests

# Temp File Creation
import os


def parse_json(input_url_path, output_file_name, logger):
    # Saves downloaded file - on failure this file will remain for inspection
    tmp_file_name = "todaysData.json"

    if os.path.isfile(tmp_file_name):
        logger.info("Input file exists. Deleting...")
        os.remove(tmp_file_name)

    logger.info("Downloading input file...")
    temp_file = open(tmp_file_name, 'w')
    with requests.get(input_url_path, stream=True) as r:
        temp_file.write(r.content)

    temp_file.close()

    logger.info("Begin processing JSON data and writing to output file")
    parse_json_file(tmp_file_name, output_file_name, logger)

    try:
        logger.info("Removing temporary data file")
        os.remove(tmp_file_name)
    except OSError:
        print "Failed temp file removal in fake_crdb_data.py"
        pass

def parse_json_file(input_file_name, output_file_name, logger):
    line_counter = 0
    line_count_total = 0

    target = open(output_file_name, 'w')
    logger.info("Opened output file: {}".format(output_file_name))

    with open(input_file_name, 'r') as f:
        logger.info("Opened input file: {}".format(input_file_name))
        
        parser = ijson.parse(f)
        logger.info("Completed parsing input file")

        my_data_array = []
        my_column_array = []

        try:
            for prefix, event, value in parser:
                if prefix == 'data.item.item':
                    my_data_array.append(value)
                elif (prefix, event) == ('data.item', 'start_array'):
                    continue
                    n += 1
                elif (prefix, event) == ('data.item', 'end_array'):
                    new_complaint = dict(zip(my_column_array, my_data_array))
                    new_complaint["has_narrative"] = (not (not new_complaint["complaint_what_happened"] or len(new_complaint["complaint_what_happened"]) == 0))
                    new_complaint["company"] = new_complaint["company"].upper()
                    # :updated_at and :created_at will stay since they are being used
                    for meta in (":sid", ":id", ":meta", ":created_meta", ":position", ":updated_meta"): 
                        del new_complaint[meta]
                    my_data_array = []
                    target.write(json.dumps(new_complaint))
                    target.write('\n')
                elif prefix == 'meta.view.columns.item.fieldName':
                    my_column_array.append(value)

                line_counter += 1
                if line_counter >= 2000000:
                    line_count_total += line_counter
                    logger.info("Processed {} lines, {} total".format(line_counter, line_count_total))
                    line_counter = 0

            if line_counter > 0:
                line_count_total += line_counter
                logger.info("Processed {} lines, {} total".format(line_counter, line_count_total))
        except ijson.common.IncompleteJSONError as e:
            logger.info('IncompleteJSONError! prefix: {}, event: {}, value: {}'.format(prefix, event, value))


    target.close()
    logger.info("Closed output file")

__all__ = ['parse_json']
