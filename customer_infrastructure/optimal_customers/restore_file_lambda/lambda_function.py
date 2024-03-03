import os
import boto3
import botocore
import stat

customer_name = os.environ.get('CUSTOMER_NAME')
gwbk_restore_bucket =os.environ.get('GWBK_RESTORE_BUCKET')

local_file_path = '/mnt/efs/'
source_file = f'{customer_name}.gwbk'
#full_file_path = local_file_path+source_file
# source_bucket_name = gwbk_restore_bucket
# source_object_key = source_file
    
# Initialize the S3 client
s3 = boto3.client('s3')

def cleanup(filename):
    # Remove the destination file if it exists
    full_file_path = local_file_path + filename
    if os.path.exists(full_file_path):
        print(f'removing existing {filename} file')
        os.chmod(full_file_path, 0o777)
        os.remove(full_file_path)
    else:
        print(f'existing file {filename} file found for: {local_file_path}')

def copy_data_zip(source_bucket, source_key):
# copy the gwbk file from s3 bucket and unzip to efs path
    full_file_path = local_file_path+source_key
    try:
        print('starting s3')
        print(f'Copying from {source_bucket}/{source_key} to {full_file_path}')
        s3.download_file(source_bucket, source_key, full_file_path)
        print(f'Objects copied from {source_bucket}/{source_key} to {full_file_path}')

    except botocore.exceptions.ClientError as e:
        print(f'Error: {e.response["Error"]["Message"]}')
        
def list_files(directory):
    with os.scandir(directory) as entries:
        for entry in entries:
            info = entry.stat()
            file_mode = stat.filemode(info.st_mode)
            file_size = human_readable_size(info.st_size)
            print(f'{file_mode} {file_size} {entry.name}')

def human_readable_size(size, decimal_places=2):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"

# Test the function
 
def lambda_handler(event, context):
    # Extract bucket name and key from the event
    source_bucket = event['Records'][0]['s3']['bucket']['name']
    source_key = event['Records'][0]['s3']['object']['key']
    filename = source_key
    print(f'source_bucket: {source_bucket}')
    print(f'source_key: {source_key}')
    
    print('checking local files before copy')
    list_files(local_file_path)
    print('starting run')
    print('starting cleanup')
    cleanup(filename)
    print('checking results of cleanup')
    list_files(local_file_path)
    print('cleanup complete')
    print('starting copy')
    copy_data_zip(source_bucket, source_key)
    print('checking results after copy')
    list_files(local_file_path)
    