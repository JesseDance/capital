from parse_commission_file import parse_commission_file
from datetime import date
import datetime
import calendar
from jinja2 import Environment, FileSystemLoader, select_autoescape
import uuid
import json
import xmltodict
from sqs_send_message import send_fifo_sqs_message
from boto_session_manager import select_service
from sqs_get_message_v2 import receive_message, delete_message

def process_file_name(file_name):

	sorted_commission_set_list, sorted_commission_list = parse_commission_file(file_name)
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
	check_count = 0
	
	
	for commission_payee in sorted_commission_set_list:
		
		hold = "N"
		check_count = check_count + 1

		selected_commission_payee_dict = select_payees_by_id(sorted_commission_list, commission_payee)
		spayee_number, payee_name, payment_amount = get_commission_data(selected_commission_payee_dict)
		spayee_number = f"{spayee_number} V"
		negative_positive_flag = negative_positive_amount(payment_amount)
		print()
		print("%%%%%%%%%%%%%")
		print("Amount : ",payment_amount)
		print("Negative or Positive Flag : ",negative_positive_flag)
		print("%%%%%%%%%%%%%")
		print()
		
		# N=Negative P=Positive
		if negative_positive_flag == "N":
			#process_bill_template(spayee_number, month_name, check_date, payment_amount)
			print("DDDD")
		
		
		
		if hold == "N":
				completed_template = create_bill_template(spayee_number, month_name, check_date, payment_amount)
				commission_msg = create_sqs_msg(completed_template, today_str, job_uuid, request_msg_que, response_msg_que )
				send_sqs_msg(commission_msg, request_msg_que)
				qb_response_dict = receive_sqs_msg(response_msg_que)
				api_name = "BillAddRs" 
				job_number, job_date, request_date_time, response_date_time, request_number, request_msg_que, response_msg_que, quickbooks_response_dict = get_response_details(qb_response_dict)
				statuscode, statusseverity, statusmessage = get_response_status(quickbooks_response_dict, api_name)
				
				print(statuscode)
				print(statusseverity)
				print(statusmessage)
				#exit()
				
	print("Total Check Count : ",check_count)
		
	return
	

def select_payees_by_id(sorted_commission_list, commission_payee):

	selected_commission_payee_list = next((sub for sub in sorted_commission_list if sub['spayee_number'] == commission_payee), None)
	
	return selected_commission_payee_list


def get_commission_data(row_list_dicts):

	spayee_number = row_list_dicts['spayee_number']
	payee_name = row_list_dicts['spayee_name']
	payment_amount = row_list_dicts['Textbox66']
	payment_amount_no_parentheses = payment_amount.replace("(","")
	payment_amount_no_parentheses = payment_amount_no_parentheses.replace(")","")
	payment_amount_no_dollar_sign = payment_amount_no_parentheses.replace("$","")
	payment_amount_stripped = payment_amount_no_dollar_sign.replace(",","")
	
	is_payment_negative = payment_amount.find("(")
	if is_payment_negative >= 0:
		payment_amount_stripped = f"-{payment_amount_stripped}"
		print()
		print("Dan $$$$$$$$$$$$$$$$$$$$$$$$$")
		print(payment_amount_stripped)
		print("Dan $$$$$$$$$$$$$$$$$$$$$$$$$")
		print()
	print("^^^^^^^^^^^^^^^^^")
	print(is_payment_negative)
	print(payment_amount)
	print(payment_amount_stripped)
	print("^^^^^^^^^^^^^^^^^")
		
	
	
	return spayee_number, payee_name, payment_amount_stripped
	
	
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
	
def create_bill_template(spayee_number, month_name, check_date, payment_amount):

	env = Environment(loader=FileSystemLoader("templates/"),autoescape=select_autoescape())
	template = env.get_template("BillAdd_1.XML")

	FullName = spayee_number
	TxnDate = check_date
	RefNumber = month_name
	Payment_Amount = payment_amount
	
	completed_template = template.render(FullName=FullName, TxnDate=TxnDate, RefNumber=RefNumber, Payment_Amount=Payment_Amount)
	

	return completed_template
	

def create_vendor_credit_template(spayee_number, month_name, check_date, payment_amount):

	env = Environment(loader=FileSystemLoader("templates/"),autoescape=select_autoescape())
	template = env.get_template("VendorCreateAdd.XML")

	FullName = spayee_number
	TxnDate = check_date
	RefNumber = month_name
	Payment_Amount = payment_amount
	
	completed_template = template.render(FullName=FullName, TxnDate=TxnDate, RefNumber=RefNumber, Payment_Amount=Payment_Amount)
	

	return completed_template


def create_sqs_msg(completed_template, today_str, job_uuid, request_msg_que, response_msg_que):

	commission_dict = {}
	#commission_list = []
	
	request_date_time = datetime.datetime.now()
	request_date_time = str(request_date_time)			
	current_uuid_str = get_uuid()
	commission_dict["job_number"] = job_uuid
	commission_dict["job_date"] = today_str
	commission_dict["request_date_time"] = request_date_time
	commission_dict["response_date_time"] = " "
	commission_dict["request_number"] = current_uuid_str
	commission_dict["request_msg_que"] = request_msg_que
	commission_dict['response_msg_que'] = response_msg_que
	commission_dict["quickbooks_request_xml"] = completed_template
	commission_msg= json.dumps(commission_dict)
	#commission_list.append(commission_string)
	commission_msg = commission_msg + "\n"
	
	print()
	print("Commission Message : ",commission_msg)
	print()
	
	
	return commission_msg

	
def get_uuid():

	current_uuid = uuid.uuid4()
	current_uuid_str = str(current_uuid)

	return current_uuid_str

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
		#print("***** Response Message = ",msg)

		if not msg:
			print("No messages to process in message que")
			#time.sleep(5)
		else:

			receipt_handle = msg.get('receipt_handle')
			#print("Que Get Message : ",msg)
			sqs_msg = msg.get('msg_content')
			delete = delete_message(receipt_handle, QueueUrl)

			print("****")
			print("QueueUrl : ",QueueUrl)
			print("Recipt Handle : ",receipt_handle)
			print("SQS Message : ",sqs_msg)
			print("****")

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
	

def negative_positive_amount(amount):

	negative_positive_flag = "P"
	negative_positive = amount.find("-")
	if negative_positive >= 1:
		negative_positive_flag = "N"

	return negative_positive_flag


def process_bill_template(spayee_number, month_name, check_date, payment_amount):

	completed_template = create_bill_template(spayee_number, month_name, check_date, payment_amount)
	commission_msg = create_sqs_msg(completed_template, today_str, job_uuid, request_msg_que, response_msg_que )
	send_sqs_msg(commission_msg, request_msg_que)
	qb_response_dict = receive_sqs_msg(response_msg_que)
	api_name = "BillAddRs" 
	job_number, job_date, request_date_time, response_date_time, request_number, request_msg_que, response_msg_que, quickbooks_response_dict = get_response_details(qb_response_dict)
	statuscode, statusseverity, statusmessage = get_response_status(quickbooks_response_dict, api_name)
				
	print(statuscode)
	print(statusseverity)
	print(statusmessage)
	#exit()
				
	print("Total Check Count : ",check_count)
		
	return

	

def main():

	# put in parm store
	# Add message ques
	sftp_dir = "/Extracts/Payees"
	local_server_dir = "/home/bwdrkr2/Data/Consulting/Capital/sftp_download/"
	bucket_name = "cps-use2-stone-eagle-payee-reports"
	
	
	#downloaded_file_list, error_file_list = get_sftp_files(sftp_dir, local_server_dir)
	
	x = process_file_name("/home/bwdrkr2/Data/Consulting/Capital/Commissions/Commission_File/SCSRPT057 Commission Summary.csv")

	return
	




if __name__ == "__main__":
	main()
