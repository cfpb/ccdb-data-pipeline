import os

from simple_salesforce import SalesforceLogin

session_id, instance_url = SalesforceLogin(
    username=os.getenv('SALESFORCE_USERNAME'),
    password=os.getenv('SALESFORCE_PASSWORD'),
    domain=os.getenv('SALESFORCE_DOMAIN'), security_token='')
