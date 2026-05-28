from datetime import datetime

full_query = (
    "SELECT "
    "CreatedDate,"
    "CCDB_Product__c,"
    "CCDB_Subproduct__c,"
    "CCDB_Issue__c,"
    "CCDB_Subissue__c,"
    "CCDB_Consumer_Narrative__c,"
    "Company_Public_Response_Type__c,"
    "Explorer_Company_Name__c,"
    "CCDB_State_Abbr__c,"
    "CCDB_Zip__c,"
    "CCDB_Tag__c,"
    "CCDB_Submitted_via__c,"
    "Initial_Sent_to_Company_DateTime__c,"
    "CCDB_Company_Response__c,"
    "CCDB_Timely_Response__c,"
    "CCDB_ID__c "
    "FROM Case WHERE CCDB_Eligible__c = true"
)


def ensure_date(dtstring):
    return datetime.fromisoformat(dtstring).isoformat()


def get_time_slice(since, til=None):
    since_q = f"{full_query} AND LastModifiedDate >= {ensure_date(since)}"
    if til:
        return f"{since_q} AND LastModifiedDate < {ensure_date(til)}"
    return since_q
