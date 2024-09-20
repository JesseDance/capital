from parse_cancellations_file import parse_cancellation_file
from process_checks_log_csv import write_log
from datetime import date
import datetime
import calendar
import uuid
import json
import xmltodict
from jinja2 import Environment, FileSystemLoader, select_autoescape
from decimal import Decimal
from sqs_send_message import send_fifo_sqs_message
from boto_session_manager import select_service
from sqs_get_message_v2 import receive_message, delete_message
import process_checks_log_csv
import csv

def process_file_name(file_name):

	cancellations_list_of_dicts, list_of_names, list_of_payee_ids = parse_cancellation_file(file_name)
	month_name, check_date = get_check_dates()
	print()
	print("Month Name : ", month_name)
	print("Check Date : ", check_date)
	print()

	today = date.today()
	today_str = str(today)
	job_uuid = get_uuid()
	request_msg_que = 'https://sqs.us-east-2.amazonaws.com/028067736227/qb_xml_requests_msg_que.fifo'
	response_msg_que = 'https://sqs.us-east-2.amazonaws.com/028067736227/vendor_response_msg_que.fifo'


	max_cancellations_per_check = 15
	cancellations_by_distinct_name_grouped = []

	log_detail_list = []
	log_header_line = create_log_header_line()
	log_detail_list.append(log_header_line)
	total_payment_amount_processed = 0 

	for distinct_name in list_of_names:

		print()
		print(distinct_name)

		total_cancellation_count = 0
		sublist_cancellation_count = 0
		check_amount = 0
		payee_amount = 0
		check_templates_filled = 0

		cancellations_by_distinct_name = list(filter(lambda name: name['Payee Name'] == distinct_name, cancellations_list_of_dicts))
		cancellations_by_name_max = []

		for cancellation in cancellations_by_distinct_name:

			sublist_cancellation_count +=1
			cancellations_by_name_max.append(cancellation)
			total_cancellation_count += 1
			
			cancellation_amount = cancellation['Cancellation_Amt']
			check_amount += Decimal(cancellation_amount)
			payee_amount += Decimal(cancellation_amount)
			total_payment_amount_processed += Decimal(cancellation_amount)
			log_detail_line = create_log_detail_line(cancellation)
			log_detail_list.append(list(log_detail_line))

			if sublist_cancellation_count == max_cancellations_per_check:
				print("items in sublist:", sublist_cancellation_count)
				cancellations_by_distinct_name_grouped.append(list(cancellations_by_name_max))
				sublist_cancellation_count = 0
				cancellations_by_name_max.clear()

				log_check_total_line = ['', '', '', '', '', '', check_amount]
				log_detail_list.append(list(log_check_total_line))
				check_amount = 0

		if cancellations_by_name_max:
			print("items in sublist:", sublist_cancellation_count)
			cancellations_by_distinct_name_grouped.append(list(cancellations_by_name_max))

			log_check_total_line = ['', '', '', '', '', '', check_amount]
			log_detail_list.append(list(log_check_total_line))
			check_amount = 0


		log_payee_total_line = ['', '', '', '', '', '', '', payee_amount]
		log_detail_list.append(list(log_payee_total_line))


		print("total cancellations for this name: ", total_cancellation_count)
		print("total groups so far: ", len(cancellations_by_distinct_name_grouped))
		print()


	for cancellation_group in cancellations_by_distinct_name_grouped:

		'''
		completed_template = create_check_template(distinct_name, check_date, cancellation_group)
		print(completed_template)
		check_templates_filled +=1
		'''

		payee_id = get_group_payee_id(cancellation_group)
		process_bill_template(today_str, job_uuid, request_msg_que, response_msg_que, payee_id, check_date, cancellation_group)
		#print(completed_template)
		check_templates_filled +=1
	




	print("total check templates filled: ", check_templates_filled)
	print()
	log_total_payment_processed_line = ['', '', '', '', '', '', '', '', total_payment_amount_processed]
	log_detail_list.append(list(log_total_payment_processed_line))
	process_checks_log_csv.main(log_detail_list)


def get_group_payee_id(cancellation_group):
	for cancellation in cancellation_group:
		group_payee_id = cancellation['Account']

	return group_payee_id
				

def get_check_dates():

	today = datetime.date.today()
	first = today.replace(day=1)
	lastMonth = first - datetime.timedelta(days=1)
	lastMonth = lastMonth.strftime("%m")
	datetime_object = datetime.datetime.strptime(lastMonth, "%m")
	month_name = datetime_object.strftime("%b")
	current_year = date.today().year
	month = int(lastMonth)
	last_day_month = calendar.monthrange(current_year, month)[1]
	check_date = f"{current_year}-{lastMonth}-{last_day_month}"
	
	return month_name, check_date

def get_uuid():

	current_uuid = uuid.uuid4()
	current_uuid_str = str(current_uuid)

	return current_uuid_str


def create_check_template(payee_id, check_date, cancellation_group):

	env = Environment(loader=FileSystemLoader("templates/"),autoescape=select_autoescape())
	template = env.get_template("CheckAdd-cancels.xml")

	FullName = payee_id
	TxnDate = check_date
	Cancellation_List = cancellation_group
	completed_template = template.render(FullName=FullName, TxnDate=TxnDate, Cancellation_List=Cancellation_List)

	return completed_template

def create_sqs_msg(completed_template, today_str, job_uuid, request_msg_que, response_msg_que):

	cancellation_dict = {}
	#cancellation_list = []
	
	request_date_time = datetime.datetime.now()
	request_date_time = str(request_date_time)			
	current_uuid_str = get_uuid()
	cancellation_dict["job_number"] = job_uuid
	cancellation_dict["job_date"] = today_str
	cancellation_dict["request_date_time"] = request_date_time
	cancellation_dict["response_date_time"] = " "
	cancellation_dict["request_number"] = current_uuid_str
	cancellation_dict["request_msg_que"] = request_msg_que
	cancellation_dict['response_msg_que'] = response_msg_que
	cancellation_dict["quickbooks_request_xml"] = completed_template
	cancellation_msg= json.dumps(cancellation_dict)
	#cancellation_list.append(cancellation_string)
	cancellation_msg = cancellation_msg + "\n"
	
	print()
	print("SQS Message : ",cancellation_msg)
	print()
	
	
	return cancellation_msg


def send_sqs_msg(message, request_msg_que):

	httpsstatuscode = None
	error = "N"
	
	while httpsstatuscode != 200:
		QueueUrl = request_msg_que
		MessageGroupId="qb_xml_request_msg_que"
		status_msg =send_fifo_sqs_message(message, QueueUrl, MessageGroupId)
		responsematadata = status_msg.get("ResponseMetadata")
		httpsstatuscode = responsematadata.get("HTTPStatusCode")
		
		if httpsstatuscode != 200:
			error = "Y"
			# write to report not send to QB
		
	return


def receive_sqs_msg(response_msg_que):

	sqs_msg = None

	while sqs_msg == None:
		QueueUrl = response_msg_que
		msg = receive_message(QueueUrl)
		

		if not msg:
			print("No messages to process in message que")
			#time.sleep(5)
		else:

			receipt_handle = msg.get('receipt_handle')
			
			sqs_msg = msg.get('msg_content')
			delete = delete_message(receipt_handle, QueueUrl)

			print("")
			print("QueueUrl : ",QueueUrl)
			print("Recipt Handle : ",receipt_handle)
			print("SQS Message : ",sqs_msg)
			print("")

	return sqs_msg

def get_response_details(response_msg_dict):

	job_number = response_msg_dict['job_number']
	job_date = response_msg_dict['job_date']
	request_date_time = response_msg_dict['request_date_time']
	response_date_time = response_msg_dict['response_date_time']
	request_number = response_msg_dict['request_number']
	request_msg_que = response_msg_dict['request_msg_que']
	response_msg_que = response_msg_dict['response_msg_que']
	quickbooks_response_xml = response_msg_dict['quickbooks_response_xml']

	quickbooks_response_dict = convert_xml_to_json(quickbooks_response_xml)

	return job_number, job_date, request_date_time, response_date_time, request_number, request_msg_que, response_msg_que, quickbooks_response_dict


def get_response_status(quickbooks_response_dict, api_name):

	statuscode = quickbooks_response_dict['QBXML']['QBXMLMsgsRs'][api_name]['@statusCode']
	statusseverity = quickbooks_response_dict['QBXML']['QBXMLMsgsRs'][api_name]['@statusSeverity']
	statusmessage = quickbooks_response_dict['QBXML']['QBXMLMsgsRs'][api_name]['@statusMessage']

	return statuscode, statusseverity, statusmessage


def convert_xml_to_json(quickbooks_response_xml):

	quickbooks_response_json = xmltodict.parse(quickbooks_response_xml)

	return quickbooks_response_json


def process_bill_template(today_str, job_uuid, request_msg_que, response_msg_que, payee_id, check_date, cancellation_group):

	completed_template = create_check_template(payee_id, check_date, cancellation_group)
	commission_msg = create_sqs_msg(completed_template, today_str, job_uuid, request_msg_que, response_msg_que )
	send_sqs_msg(commission_msg, request_msg_que)
	qb_response_dict = receive_sqs_msg(response_msg_que)
	api_name = "CheckAddRs" 
	job_number, job_date, request_date_time, response_date_time, request_number, request_msg_que, response_msg_que, quickbooks_response_dict = get_response_details(qb_response_dict)
	statuscode, statusseverity, statusmessage = get_response_status(quickbooks_response_dict, api_name)
				
	print(statuscode)
	print(statusseverity)
	print(statusmessage)
	#exit()
				
	return
	

def create_log_detail_line(cancellation_dict):

	name = cancellation_dict['Payee Name']
	account_number = cancellation_dict['Account']
	record_id = cancellation_dict['Record Id']
	contract_number = cancellation_dict['Contract Number']
	check_amount = cancellation_dict['Cancellation_Amt']

	row_list = [name, account_number, record_id, contract_number, check_amount]

	return row_list


def create_log_header_line():

	heading_list = [ 'Payee Name', 'Account Number', 'Record Id', 'Contract Number', 'Cancellation Amt', 'Check Amt', 'Payee Amt', 'Total Amount Processed']

	return heading_list


if __name__ == "__main__":

	file_name = "/home/jessedance/development/capital/Cancellations/REFUNDS_20240612070442343"
	process_file_name(file_name)
