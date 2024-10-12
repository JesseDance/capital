__version__ = '2.0.0'
import boto3
import logging

# from decouple import config
import os
# from common import set_env

'''
    if you specify an aws_access_key_id as a global variable in this code, the set_session will use the aws_access_key_id and aws_secret_access_key for authentication.
    if you leave aws_access_key and aws_secret_access key blank and specify a profile_name or region_name then it will use both or either of those in the session.
    if you leave all four of those global variabless blank, then no profile_name and no region_name will be used for the set_session.

    EXAMPLES:
    # session 1 
    aws_access_key_id='xxxx',
    aws_secret_access_key='xxxx'
    profile_name = "PROFILE_NAME"
    region_name = "us-east-2"

    # session 2
    aws_access_key_id=''
    aws_secret_access_key=''
    profile_name = "PROFILE_NAME"
    region_name = "us-east-2"

    # session 3
    aws_access_key_id=''
    aws_secret_access_key=''
    profile_name = "PROFILE_NAME"
    region_name = ""

    # session 4
    aws_access_key_id=''
    aws_secret_access_key=''
    profile_name = ""
    region_name = "us-east-2"

    # session 5
    aws_access_key_id=''
    aws_secret_access_key=''
    profile_name = ""
    region_name = ""

'''
# ---------------------------------------------------------------------------------------
# GET ENVIRON's
# ---------------------------------------------------------------------------------------
PROFILE_NAME = os.environ.get('BOTO_SESSION_PROFILE_NAME')
REGION_NAME = os.environ.get('REGION_NAME')
EMAIL_REGION_NAME = os.environ.get('EMAIL_REGION_NAME')
EMAIL_PROFILE_NAME = os.environ.get('EMAIL_PROFILE_NAME')
ENVIRONMENT_TYPE = os.environ.get('ENVIRONMENT_TYPE')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

program_name = "boto_session_manager.py"

email_region_name = EMAIL_REGION_NAME
email_profile_name = EMAIL_PROFILE_NAME

aws_access_key_id= os.environ.get('AWS_ACCESS_KEY_ID')
aws_secret_access_key= os.environ.get('AWS_SECRET_ACCESS_KEY')
profile_name = PROFILE_NAME
region_name = REGION_NAME
if ENVIRONMENT_TYPE == 'test':
    print("")
    print("------------------------------------------------------------------------------")
    print(" W O R K I N G  O U T  OF  T E S T  E N V I R O N M E N T")
    print("-- boto session config --")
    print(f"region_name: {region_name}")
    print(f"profile_name: {profile_name}")
    print("")
    print(f"email_region_name: {email_region_name}")
    print(f"email_profile_name: {email_profile_name}")
    print("")
    print(f"ENVIRONMENT_TYPE: {ENVIRONMENT_TYPE}")
    print("------------------------------------------------------------------------------")
    print("")


def set_session():
    function_name = 'set_session'
    logger.info(f'  function: {program_name} {function_name}')
        
    if aws_access_key_id and aws_secret_access_key:
        #print("session 1A")
        logger.info(f'  session 1A: {program_name} {function_name}')

        if region_name:
            session = boto3.Session(aws_access_key_id = aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=region_name)
        else:
            #print("session 1B")
            logger.info(f'  session 1B: {program_name} {function_name}')
            session = boto3.Session(aws_access_key_id = aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

    elif profile_name and region_name:
        #print("session 2")
        logger.info(f'  session 2: {program_name} {function_name}')
        session = boto3.Session(profile_name=profile_name, region_name=region_name)

    elif profile_name and not region_name:
        #print("session 3")
        logger.info(f'  session 3: {program_name} {function_name}')        
        session = boto3.Session(profile_name=profile_name)

    elif region_name and not profile_name:
        #print("session 4")
        logger.info(f'  session 4: {program_name} {function_name}')      
        session = boto3.Session(region_name=region_name)
    
    else:
        #print("session 5")
        logger.info(f'  session 5: {program_name} {function_name}') 
        session = boto3.Session()
    return session 


def select_service(service):
    function_name = 'select_service'
    logger.info(f'  function: {program_name} {function_name}')

    session = set_session()
    if service == 'dynamodb':
        return session.resource(service_name='dynamodb')

    elif service == 's3_resource':
        return session.resource(service_name='s3')
    
    elif service == 's3_client':
        return session.client(service_name='s3')

    elif service == 'ses':
        return session.client(service_name='ses')

    elif service == 'sns':
        return session.client(service_name='sns')

    elif service == 'sqs':
        return session.client(service_name='sqs')

    elif service == 'secretsmanager':
        return session.client(service_name='secretsmanager')  

    elif service == 'ssm':
        return session.client(service_name='ssm')            

    else:
        return None


def email_session_override():
    function_name = 'email_session_override'
    logger.info(f'  function: {program_name} {function_name}')

    if email_profile_name:
        session = boto3.Session(profile_name=email_profile_name, region_name=email_region_name)
    else:
        session = boto3.Session(region_name=email_region_name)
    return session.client(service_name='ses')


def s3fs_profile():
    function_name = 's3fs_profile'
    logger.info(f'  function: {program_name} {function_name}')

    if profile_name:
        return profile_name
    else:
        return None 


if __name__ == "__main__":
    pass
    #set_session()
    #service = 'sqs'
    #select_service(service)
   