import mimetypes
import requests
import os

def upload_file_url(filepath):
    # 1. 预签名
    presigned_url = "https://api.platform.archivemodel.cn/files/pre-signed-url"
    signed_url = "https://api.platform.archivemodel.cn/files"
    apikey = "sk-ag6ui8h6haj71ouhis7c-d6f2c04e6ef24893f4b7fecec2b5ee6ac917df90"
    filename = os.path.basename(filepath)
    filemime = mimetypes.guess_type(filepath)[0] or "application/octet-stream"  # 修正 MIME 类型
    filesize = os.path.getsize(filepath)
    print(filemime, filename, filesize)
    
    headers = {
        "X-API-Key": apikey,
        "Content-Type": "application/json"
    }
    data = {
        "name": filename,
        "method": "PUT"
    }
    response = requests.post(presigned_url, headers=headers, json=data)
    response = response.json()
    
    if "object_key" not in response or "url" not in response:
        print("预签名 URL 请求失败:", response)
        return
    
    object_key = response["object_key"]
    upload_url = response["url"]
    print("预签名 URL 响应:", response)

    # 2. 上传文件
    with open(filepath, 'rb') as file_to_upload:
        file_content = file_to_upload.read()
    
    upload_response = requests.put(upload_url, data=file_content)
    if upload_response.status_code != 200:
        print("文件上传失败:", upload_response.status_code, upload_response.text)
        return
    
    # 3. 拿到文件地址
    data = {
        "type": filemime,  # 确保 filemime 不为 None
        "name": filename,
        "size": filesize,
        "object_key": object_key
    }
    response = requests.post(signed_url, headers=headers, json=data)
    return response.json()["pre_signed_url"]


