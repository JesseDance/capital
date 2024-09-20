__version__ = '1.0.1'
import boto3
import json
import logging
from boto_session_manager import select_service


logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.info('IMPORT FUNCTION START: PY sns_get_message')
program_name = 'sqs_get_message_v2.py'


def receive_message(QueueUrl):
    function_name = "receive_message"
    sqs_client = select_service('sqs')
    message = None    
    response = sqs_client.receive_message(
        QueueUrl=QueueUrl,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10
    )
        
    msg = {}   
    for message in response.get("Messages", []):
        message_body = message["Body"]
        msg['message_id'] = message['MessageId']
        msg['receipt_handle'] = message['ReceiptHandle']
        msg['msg_content'] = json.loads(message_body)
        msg['HTTPStatusCode'] = response['ResponseMetadata']['HTTPStatusCode']

    logger.info('receive_message: parm: ' + str(QueueUrl))
    logger.info('receive_message: response: ' + str(msg))        
    return msg


def delete_message(receipt_handle, QueueUrl):
    function_name = "delete_message"
    sqs_client = select_service('sqs')
    response = sqs_client.delete_message(
        QueueUrl=QueueUrl,
        ReceiptHandle=receipt_handle
    )
    #print(response)
    logger.info('delete_message: parm: ' + str(receipt_handle))
    logger.info('delete_message: parm: ' + str(QueueUrl))
    logger.info('delete_message: response: ' + str(response))
    return response 


if __name__ == '__main__':
    QueueUrl="https://sqs.us-east-2.amazonaws.com/519327521817/sqs-files-to-sftp-get.fifo"

    
   
    msg = receive_message(QueueUrl)
    print("*** Message : ",msg)

    """
    ftp_msg = msg.get('msg_content')
    print(" ")
    print("SFTP Message : ",ftp_msg)

    job_run = ftp_msg.get('job_run')
    client = ftp_msg.get('client')
    from_bucket = ftp_msg.get('from_bucket')
    file_name = ftp_msg.get('file_name')
    to_directory = ftp_msg.get('to_directory')

    print(" ")
    print("Job Run : ",job_run)
    print("Client : ",client)
    print("From Bucket : ",from_bucket)
    print("File Name : ",file_name)
    print("To Directory : ",to_directory)
"""
    

    receipt_handle = msg.get('receipt_handle')
    print(" ")
    print("Receipt Handle : ",receipt_handle)

    delete = delete_message(receipt_handle, QueueUrl)

    print(" ")
    print("Delete Message : ",delete)