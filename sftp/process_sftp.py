import paramiko
from common.secrets_package.secret_from_secret_manager import get_secret
import json

def get_sftp_files(sftp_directory, local_directory):

	
	secret_data = get_secret('capital_ses_email')
	secret_data_d = json.loads(secret_data)
	print(secret_data_d)
	server = secret_data_d.get('CAPTIAL_EMAIL_SERVER')
	user = secret_data_d.get('CAPITAL_EMAIL_USER')
	password = secret_data_d.get('CAPTIAL_EMAIL_PASSWORD')
	print(server, user, password)

	downloaded_file_list = []
	error_file_list = []
	
	# Logon SFTP
	sftp = sftp_logon (server, user, password)
	
	# Chance SFTP Directory
	if sftp:
		error_msg = sftp_chg_dir(sftp, sftp_directory)
	print(error_msg)
	
	# List SFTP Files
	file_list = sftp_list_files(sftp)
	

	# Download SFTP Files
	if file_list:
		downloaded_file_list, error_file_list =  sftp_get(sftp, file_list, local_directory)
		print("Downloaded File List : ", downloaded_file_list)
		print("Error File List : ", error_file_list)
		
	
	return downloaded_file_list, error_file_list
	
	
def sftp_chg_dir(sftp, directory):

	error_msg = " "
	print("Change Directory : ",directory)

	try:
		sftp.chdir(directory)
	except FileNotFoundError: 
		error_msg = "SFTP directory " + directory + " not found"
		
	return error_msg
	
	
def sftp_list_files(sftp):

	file_list = []

	download_list = sftp.listdir()
	
	
	for file_name in download_list:
		is_file = sftp.lstat(file_name)
		is_file = str(is_file)	
		is_file = is_file[0]
		
		# position 1 "-" if a file or "d" for directory

		if is_file == "-":
			found = file_name.find(".bak")
			if found == -1:
				file_list.append(file_name)
	
	return file_list
	
	
def sftp_logon(server, user, pwd):

	print("FUNCTION : sftp_logon")
	
	Error_Msg = " "

	# Open a transport
	server,port = server,22 

	try:

		transport = paramiko.Transport((server,port))
	# Auth    
		username,password = user,pwd
		transport.connect(None,user,pwd)
	# Go!    
		sftp = paramiko.SFTPClient.from_transport(transport)
		# Download
	except paramiko.AuthenticationException:
		print("Auth Error")
		
	print(sftp)

	return sftp	
	
	
def sftp_get(sftp, file_list, local_directory):

	downloaded_file_list = []
	error_file_list = []
	
	for file_name in file_list:
	
		error_msg = None
		local_file_name = f"{local_directory}{file_name}"
		
	
		try:
			sftp.get(file_name,local_file_name)
		except FileNotFoundError:
			error_msg = f"Error - {file_name} is not found on SFTP Server or local server directory {local_directory} is not found."
		if error_msg == None:
			downloaded_file_list.append(local_file_name)
			#rename_sftp_file_name(sftp, file_name)
		else:
			error_file_list.append(error_msg)
			
	return  downloaded_file_list, error_file_list  
	

def rename_sftp_file_name(sftp, existing_sftp_file_name):

	new_ext = ".bak"
	new_sftp_file_name = f"{existing_sftp_file_name}{new_ext}"

	print(existing_sftp_file_name)
	print(new_sftp_file_name)
	print()
		
	sftp.rename(existing_sftp_file_name, new_sftp_file_name)

	return    


if __name__ == "__main__":
	get_sftp_files("/Extracts/Payees", "/home/jessedance/DRK_dev/capital_extracts/Commissions_data")
	
	
	
