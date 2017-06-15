import os
import configargparse
import complaints.index as index
from complaints.streamParser import parse_json

def build_arg_parser():
    p = configargparse.ArgParser(prog='run_pipeline',
                                 description='download complaints and index in Elasticsearch',
                                 ignore_unknown_config_file_keys=True)
    p.add('-c', '--my-config', required=False, is_config_file=True, 
        help='config file path')
    p.add('--es-host', '-o', required=True, dest='es_host', 
        help='Elasticsearch host', env_var='ES_HOST')
    p.add('--es-port', '-p', required=True, dest='es_port', 
        help='Elasticsearch port', env_var='ES_PORT')
    p.add('--es-username', '-u', required=True, dest='es_username', 
        help='Elasticsearch username', env_var='ES_USERNAME')
    p.add('--es-password', '-a', required=True, dest='es_password', 
        help='Elasticsearch password', env_var='ES_PASSWORD')
    p.add('--index-name', '-i', required=True, dest='index_name', 
        help='Elasticsearch index name')
    return p

def download_and_index(parser_args):
    c = parser_args
    
    os.environ["ES_HOST"] = c.es_host
    os.environ["ES_PORT"] = c.es_port
    os.environ["ES_USERNAME"] = c.es_username
    os.environ["ES_PASSWORD"] = c.es_password

    index_alias = c.index_name
    index_name = "{}-v1".format(index_alias)
    backup_index_name = "{}-v2".format(index_alias)

    output_file_name = 'complaints/ccdb/ccdb_output.json'
    input_file_name = 'https://data.consumerfinance.gov/api/views/nsyy-je5y/rows.json'
    parse_json(input_file_name,output_file_name)

    index.index_json_data('complaints/settings.json', 'complaints/ccdb/ccdb_mapping.json', \
      'complaints/ccdb/ccdb_output.json', index_name, backup_index_name, index_alias)

def main():
    p = build_arg_parser()
    c = p.parse_args()
    download_and_index(c)
 
if __name__ == '__main__':
    main()
