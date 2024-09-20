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
import csv


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
	bill_count = 0
	credit_count = 0
	new_customer_count = 0
	invoice_count = 0
	commission_count = 0

	file = open('profiles2.csv', 'w', newline='')
	writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
	writer.writerow("'Test'")
	

	
	
	
	for commission_payee in sorted_commission_set_list:

		commission_count = commission_count + 1
		
		hold = "N"
		out_of_business = "N"
		
		selected_commission_payee_dict = select_payees_by_id(sorted_commission_list, commission_payee)
		spayee_number, payee_name, payment_amount = get_commission_data(selected_commission_payee_dict)
		spayee_number_customer = f"{spayee_number} C"
		spayee_number_vendor = f"{spayee_number} V"

		if spayee_number == "P0000316":
			out_of_business = "Y"

		# N=Negativeor P=Positive
		negative_positive_flag = negative_positive_amount(payment_amount)

		if negative_positive_flag == "N" and out_of_business == "Y":
			customer_found  = process_customer_query_template(today_str, job_uuid, request_msg_que, response_msg_que, spayee_number_customer)
			if customer_found == "N":
				vendor_found, qb_name, qb_companyname, qb_addr1, qb_addr2, qb_addr3, qb_city, qb_state, qb_postalcode, qb_country, qb_phone, qb_email = process_vendor_query_template(today_str, job_uuid, request_msg_que, response_msg_que, spayee_number_vendor)
				
				if vendor_found == "Y":
					customer_added = process_customer_add_template(today_str, job_uuid, request_msg_que, response_msg_que, spayee_number_customer ,qb_companyname, qb_addr1, qb_addr2, qb_addr3, qb_city, qb_state, qb_postalcode, qb_phone, qb_email)
					new_customer_count = new_customer_count + 1

			process_invoice_add_template(today_str, job_uuid, request_msg_que, response_msg_que, spayee_number_customer, check_date, payment_amount)
			invoice_count = invoice_count + 1
		
		
		
		if negative_positive_flag == "P":
			
			if hold == "N":
				bill_count = bill_count + 1
				process_bill_template(today_str, job_uuid, request_msg_que, response_msg_que, spayee_number_vendor, month_name, check_date, payment_amount)
				
			
		elif negative_positive_flag == "N" and out_of_business == "N":
		
			if hold == "N":
				credit_count = credit_count + 1
				process_credit_template(today_str, job_uuid, request_msg_que, response_msg_que, spayee_number_vendor, month_name, check_date, payment_amount)
				
		          
		
		
	print()		
	print("Total Commission Count : ", commission_count)
	print("Total Bill Count : ",bill_count)
	print("Total Credit Count : ",credit_count)
	print("Total Invoice Count : ",invoice_count)
	print("Total New Customers Added : ",new_customer_count)
	print()

	file.close()

	
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
	template = env.get_template("Bill_Add.XML")

	FullName = spayee_number
	TxnDate = check_date
	RefNumber = month_name
	Payment_Amount = payment_amount
	
	completed_template = template.render(FullName=FullName, TxnDate=TxnDate, RefNumber=RefNumber, Payment_Amount=Payment_Amount)
	
	return completed_template
	

def create_vendor_credit_template(spayee_number, month_name, check_date, payment_amount):

	env = Environment(loader=FileSystemLoader("templates/"),autoescape=select_autoescape())
	template = env.get_template("Vendor_Credit_Add.XML")

	FullName = spayee_number 
	TxnDate = check_date
	RefNumber = month_name
	Payment_Amount = payment_amount
	
	completed_template = template.render(FullName=FullName, TxnDate=TxnDate, RefNumber=RefNumber, Payment_Amount=Payment_Amount)
	

	return completed_template


def create_customer_query_template(Customer_Name):

	env = Environment(loader=FileSystemLoader("templates/"),autoescape=select_autoescape())
	template = env.get_template("Customer_Query.XML")
	completed_template = template.render(Customer_Name=Customer_Name)

	return completed_template



def create_customer_add_template(payeenumber, companyname, addr1, addr2, addr3, city, state, postalcode, phone, email):

	env = Environment(loader=FileSystemLoader("templates/"),autoescape=select_autoescape())
	template = env.get_template("Customer_Add.XML")
	
	IsActive = "1"
	Customer_Id = payeenumber
	CompanyName = companyname
	Addr1 = addr1
	Addr2 = addr2
	Addr3 = addr3
	City = city
	State = state
	PostalCode = postalcode
	Email = email
	Phone = phone 
	completed_template = template.render(Is_Active=IsActive,Customer_Id=Customer_Id ,CompanyName=CompanyName, Addr1=Addr1, Addr2=Addr2, Addr3=Addr3, City=City, State=State, PostalCode=PostalCode, Phone=Phone, Email=Email)

	return completed_template


def create_invoice_add_template(payeenumber, txndate, payment_amount):

	env = Environment(loader=FileSystemLoader("templates/"),autoescape=select_autoescape())
	template = env.get_template("Invoice_Add.XML")
	
	completed_template = template.render(FullName=payeenumber, TxnDate=txndate, Payment_Amount=payment_amount)


	return completed_template


def create_vendor_query_template(Vendor_Name):

	env = Environment(loader=FileSystemLoader("templates/"),autoescape=select_autoescape())
	template = env.get_template("Vendor_Query.XML")
	completed_template = template.render(Vendor_Name=Vendor_Name)

	return completed_template


def get_vendor_query_data(quickbooks_response_dict):

	
	


	qb_listid =  ""
	qb_edit_sequence = ""
	qb_name = ""
	qb_companyname = ""
	qb_addr1 = ""
	qb_addr2 = ""
	qb_addr3 = ""
	qb_city = ""
	qb_state = ''
	qb_postalcode = ""
	qb_country = ""
	qb_phone = ""
	qb_email = ""
	qb_notes = ""
	qb_vendortaxid = ""

	

	
	qb_name = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get('VendorRet').get('Name')
	
	if qb_name == None:
		qb_name = ""
	qb_companyname = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get('VendorRet').get('CompanyName')
	if qb_companyname == None:
		qb_companyname = ""
	qb_addr1 = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get('VendorRet').get('VendorAddress').get('Addr1')
	if qb_addr1 == None:
		qb_addr1 = ""
	qb_addr2 = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get('VendorRet').get('VendorAddress').get('Addr2')
	if qb_addr2 == None:
		qb_addr2 = ""
	#qb_addr3 = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VewndorQueryRs').get('VendorRet').get('VendorAddressBlock').get('Addr3')
	#if qb_addr3 == None:
		#qb_addr3 = ""
	qb_city = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get('VendorRet').get('VendorAddress').get('City')
	if qb_city == None:
		qb_city = ""
	qb_state = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get('VendorRet').get('VendorAddress').get('State')
	if qb_state == None:
		qb_state = ""
	qb_postalcode = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get('VendorRet').get('VendorAddress').get('PostalCode')
	if qb_postalcode == None:
		qb_postalcode = ""
	qb_country = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get('VendorRet').get('VendorAddress').get('Country')
	if qb_country == None:
		qb_country = ""
	qb_phone = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get('VendorRet').get('Phone')
	if qb_phone == None:
		qb_phone = ""
	qb_email = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get("VendorRet").get("Email")
	if qb_email == None:
		qb_email = ""
	
	return  qb_name, qb_companyname, qb_addr1, qb_addr2, qb_addr3, qb_city, qb_state, qb_postalcode, qb_country, qb_phone, qb_email




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
	print("SQS Message : ",commission_msg)
	print()
	
	
	return commission_msg

	
def get_uuid():

	current_uuid = uuid.uuid4()
	current_uuid_str = str(current_uuid)

	return current_uuid_str

def send_sqs_msg(message, request_msg_que):

	httpsstatuscode = None
	error = "N"
	create_customer_query_template
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
	

def negative_positive_amount(amount):

	negative_positive_flag = "P"
	negative_positive = amount.find("-")
	if negative_positive >= 0:
		negative_positive_flag = "N"

	return negative_positive_flag


def process_bill_template(today_str, job_uuid, request_msg_que, response_msg_que, spayee_number, month_name, check_date, payment_amount):

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
				
	return

def process_credit_template(today_str, job_uuid, request_msg_que, response_msg_que, spayee_number, month_name, check_date, payment_amount):

	payment_amount = payment_amount.replace("-", "")
	payment_amount = payment_amount.strip()
	completed_template = create_vendor_credit_template(spayee_number, month_name, check_date, payment_amount)
	commission_msg = create_sqs_msg(completed_template, today_str, job_uuid, request_msg_que, response_msg_que )
	send_sqs_msg(commission_msg, request_msg_que)
	qb_response_dict = receive_sqs_msg(response_msg_que)
	api_name = "VendorCreditAddRs" 
	job_number, job_date, request_date_time, response_date_time, request_number, request_msg_que, response_msg_que, quickbooks_response_dict = get_response_details(qb_response_dict)
	statuscode, statusseverity, statusmessage = get_response_status(quickbooks_response_dict, api_name)
	
	print()
	print("Credit Template : ")			
	print(statuscode)
	print(statusseverity)
	print(statusmessage)
	print()
	
				
	return	


def process_customer_query_template(today_str, job_uuid, request_msg_que, response_msg_que, spayee_number_customer):


	completed_template = create_customer_query_template(spayee_number_customer)
	commission_msg = create_sqs_msg(completed_template, today_str, job_uuid, request_msg_que, response_msg_que )
	send_sqs_msg(commission_msg, request_msg_que)
	qb_response_dict = receive_sqs_msg(response_msg_que)
	api_name = "CustomerQueryRs" 
	job_number, job_date, request_date_time, response_date_time, request_number, request_msg_que, response_msg_que, quickbooks_response_dict = get_response_details(qb_response_dict)
	statuscode, statusseverity, statusmessage = get_response_status(quickbooks_response_dict, api_name)
	
	if statuscode == "0" :
		customer_found = "Y"
	else:
		customer_found = "N"

	return customer_found


def process_vendor_query_template(today_str, job_uuid, request_msg_que, response_msg_que, spayee_number_vendor):

	completed_template = create_vendor_query_template(spayee_number_vendor)
	commission_msg = create_sqs_msg(completed_template, today_str, job_uuid, request_msg_que, response_msg_que )
	send_sqs_msg(commission_msg, request_msg_que)
	qb_response_dict = receive_sqs_msg(response_msg_que)
	print("XXXXXXXXXXXXXXXXXXX")
	print(qb_response_dict)
	print("XXXXXXXXXXXXXXXXXXX")
	api_name = "VendorQueryRs" 
	job_number, job_date, request_date_time, response_date_time, request_number, request_msg_que, response_msg_que, quickbooks_response_dict = get_response_details(qb_response_dict)
	statuscode, statusseverity, statusmessage = get_response_status(quickbooks_response_dict, api_name)

	print("")
	print("Status Code : ",statuscode)

	if statuscode == "0":

		vendor_found = "Y"

		

		qb_name, qb_companyname, qb_addr1, qb_addr2, qb_addr3, qb_city, qb_state, qb_postalcode, qb_country, qb_phone, qb_email = get_vendor_query_data(quickbooks_response_dict)

		print("Done in Query Data")
	
		print()
		print("Koz Dan")	
		print()
		print("QB Vendor Response Dict : ",quickbooks_response_dict)
		print("Vendor Template :", completed_template)
		print()		
		print("Vendor Status : ", statuscode)
		print("Vendor Severity : ",statusseverity)
		print("Vendor Status :",statusmessage)
		print("Koz Dan")
		print()

	else:

		vendor_found = "N"
		qb_name = ""
		qb_companyname = ""
		qb_addr1 = ""
		qb_addr2 = ""
		qb_addr3 = ""
		qb_city = ""
		qb_state = ""
		qb_postalcode = ""
		qb_country = ""
		qb_phone = ""
		qb_email = ""


	return vendor_found, qb_name, qb_companyname, qb_addr1, qb_addr2, qb_addr3, qb_city, qb_state, qb_postalcode, qb_country, qb_phone, qb_email


def process_customer_add_template(today_str, job_uuid, request_msg_que, response_msg_que, spayee_number_customer ,companyname, addr1, addr2, addr3, city, state, postalcode, phone, email):

	completed_template = create_customer_add_template(spayee_number_customer ,companyname, addr1, addr2, addr3, city, state, postalcode, phone, email)
	commission_msg = create_sqs_msg(completed_template, today_str, job_uuid, request_msg_que, response_msg_que )
	send_sqs_msg(commission_msg, request_msg_que)
	qb_response_dict = receive_sqs_msg(response_msg_que)
	api_name = "CustomerAddRs" 
	job_number, job_date, request_date_time, response_date_time, request_number, request_msg_que, response_msg_que, quickbooks_response_dict = get_response_details(qb_response_dict)
	statuscode, statusseverity, statusmessage = get_response_status(quickbooks_response_dict, api_name)
	
	if statuscode == "0" :
		customer_added= "Y"
	else:
		customer_added = "N"

	return customer_added

	
def process_invoice_add_template(today_str, job_uuid, request_msg_que, response_msg_que, spayee_number_customer, txndate, payment_amount):

    
	payment_amount_positive = payment_amount.replace("-", "")

	completed_template = create_invoice_add_template(spayee_number_customer, txndate, payment_amount_positive)
	commission_msg = create_sqs_msg(completed_template, today_str, job_uuid, request_msg_que, response_msg_que )
	send_sqs_msg(commission_msg, request_msg_que)
	qb_response_dict = receive_sqs_msg(response_msg_que)
	api_name = "InvoiceAddRs" 
	job_number, job_date, request_date_time, response_date_time, request_number, request_msg_que, response_msg_que, quickbooks_response_dict = get_response_details(qb_response_dict)
	statuscode, statusseverity, statusmessage = get_response_status(quickbooks_response_dict, api_name)
	
	print("Invoice Add Templete : ")
	print()
	print(completed_template)
	print()
	print("Status Codes : ")
	print(statuscode, statusseverity, statusmessage)
	print()
	print("Invoice Add Templete : ")
	

	if statuscode == "0" :
		invoice_added= "Y"
	else:
		invoice_added = "N"

	
	return invoice_added


def main():

	# put in parm store
	# Add message ques
	sftp_dir = "/Extracts/Payees"
	local_server_dir = "/home/bwdrkr2/Data/Consulting/Capital/sftp_download/"
	bucket_name = "cps-use2-stone-eagle-payee-reports"
	
	
	#downloaded_file_list, error_file_list = get_sftp_files(sftp_dir, local_server_dir)
	
	#x = process_file_name("/home/bwdrkr2/Data/Consulting/Capital/Commissions/Commission_File/SCSRPT057 Commission Summary.csv")
	x = process_file_name("/home/bwdrkr2/Data/Consulting/Capital/Commissions/Commission_File/2024_06_14_SCSRPT057_Commission_Summary.csv")



	

	return
	




if __name__ == "__main__":
	main()
