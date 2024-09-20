__version__ = '1.0.0'
import boto3
import json
import logging
from boto_session_manager import select_service

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.info('IMPORT FUNCTION START: sqs_send_message')
program_name = 'sqs_send_message.py'

sqs_client = select_service('sqs')


def send_fifo_sqs_message(message, QueueUrl, MessageGroupId):
	
	#message = {"key": "value"}
	response = sqs_client.send_message(
		QueueUrl=QueueUrl,
		MessageBody=json.dumps(message),
		MessageGroupId=MessageGroupId
	)
	#print(response)
	logger.info('send_fifo_sqs_message: parm: ' + str(message))
	logger.info('send_fifo_sqs_message: parm: ' + str(QueueUrl))
	logger.info('send_fifo_sqs_message: parm: ' + str(MessageGroupId))
	logger.info('send_fifo_sqs_message: response: ' + str(response))
	return response


def send_standard_sqs_message(message, QueueUrl):
	
	#message = {"key": "value"}
	response = sqs_client.send_message(
		QueueUrl=QueueUrl,
		MessageBody=json.dumps(message)
	)
	#print(response)
	logger.info('send_fifo_sqs_message: parm: ' + str(message))
	logger.info('send_fifo_sqs_message: parm: ' + str(QueueUrl))
	logger.info('send_standard_sqs_message: response: ' + str(response))
	return response 


if __name__ == '__main__':
	message = {"test_message": "***** this is test message6"}
	#QueueUrl="https://us-east-2.queue.amazonaws.com/519327521817/sqs-encrypt-pcrs-file.fifo"
	QueueUrl="https://sqs.us-east-2.amazonaws.com/519327521817/sqs-files-to-encrypt.fifo"
	#MessageGroupId="encrypt-pcrs-file"
	MessageGroupId="encrypt-files"
	print(send_fifo_sqs_message(message, QueueUrl, MessageGroupId)) 
