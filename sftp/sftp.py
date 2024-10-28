import paramiko
import os
from common.secrets_package.secret_from_secret_manager import get_secret
import json

def download_files_from_sftp_directory(remote_directory, local_directory):
    """
    Download all files from an SFTP directory to a local directory.

    :param hostname: The hostname or IP address of the SFTP server.
    :param port: The port of the SFTP server (usually 22 for SFTP).
    :param username: The username to authenticate with.
    :param password: The password to authenticate with.
    :param remote_directory: The path to the directory on the SFTP server.
    :param local_directory: The path to the local directory where the files should be saved.
    """
    try:
        secret_data=get_secret('sftp_creds')
        data = json.loads(secret_data)
        print(data)
        hostname = data.get('server_sftp')
        username = data.get('username_sftp')
        password = data.get('password_sftp')
        port = 22
        # Initialize SSH transport
        transport = paramiko.Transport((hostname, port))

        # Connect to the server
        transport.connect(username=username, password=password)

        # Create an SFTP client from the transport object
        sftp = paramiko.SFTPClient.from_transport(transport)
        # import pdb; pdb.set_trace()
        # List all files in the remote directory
        file_list = sftp.listdir(remote_directory)
        print(f"Found {len(file_list)} files in {remote_directory}.")

        # Ensure the local directory exists
        os.makedirs(local_directory, exist_ok=True)
        found_file_name = ''
        # Download each file in the remote directory
        for file_name in file_list:
            remote_file_path = f"{remote_directory}/{file_name}"
            local_file_path = os.path.join(local_directory, file_name)
            found_file_name = file_name
            try:
                sftp.get(remote_file_path, local_file_path)
                print(f"Downloaded: {remote_file_path} to {local_file_path}")
            except FileNotFoundError as fnfException:
                print(f"File not found: {remote_file_path}")
            except Exception as e:
                print(f"An error occurred while downloading {remote_file_path}: {e}")

        # Close the SFTP connection
        sftp.close()
        transport.close()
        return found_file_name
    except paramiko.SSHException as sshException:
        print(f"Unable to establish SSH connection: {sshException}")
    except paramiko.AuthenticationException as authException:
        print(f"Authentication failed, please verify your credentials: {authException}")
    except paramiko.SFTPError as sftpException:
        print(f"SFTP error occurred: {sftpException}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    download_files_from_sftp_directory("/Extracts/Reinsurance_Extracts", "/home/jessedance/DRK_dev/capital_extracts/Treaties")
    
    
    