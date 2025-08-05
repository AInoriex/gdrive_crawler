import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import requests
from utils.logger import logger
from utils.utime import random_sleep
from utils.request import download_resource

# 导出任务状态
export_status_ok = str("SUCCEEDED") # 可下载
export_status_queue = str("QUEUED") # 队列中

# COOKIES
gdrive_cookies = {
    "__Secure-ENID": "25.SE=ZWdFz-VamEuN1WQShh3kXxtDBgivqR_KOI8MBajzWqKaoWPmBTiKLrBBFF2ilsPZUorUqgFgy7jzlAcL3er3BnusSiddt54ZVdc0O9Y9o4-jGMSoHhmsLUF8Imbb9qphvKbyixwcOeU6bNhM4hsD2URKuxk_KX6KIaYUi_5Gi6aK8E7w4FnNbpi-ynqN_KNt7EnV0NtGPsrZCs6W7UY9O2l-5en_fN52txLK9JlDMWsl6XcoABg6Qbfjd-yqJUvnW8SrDVSf2rO7sZCDyoywXsMtaqLCHm2DWXw0",
    "SEARCH_SAMESITE": "CgQIt54B",
    "HSID": "Awo8FiVS0M34jgf4j",
    "SSID": "ATk52MC2_acaaGWDD",
    "APISID": "pbTU2TMmmN_ZNn1Y/AM89reg3D6M8OLz_V",
    "SAPISID": "sQBQb1Et2x14Wd--/AtS6yoDpsIzzJriSl",
    "__Secure-1PAPISID": "sQBQb1Et2x14Wd--/AtS6yoDpsIzzJriSl",
    "__Secure-3PAPISID": "sQBQb1Et2x14Wd--/AtS6yoDpsIzzJriSl",
    "SID": "g.a000zQjjWpM-EcYWAJ4jNOhKpWkIJyE3uiXUs8mkW29dNYg_1-OOhsJGQk6X_HP0_QVt9_qTCwACgYKAa0SARQSFQHGX2MiYM5JjUGqNRrfYuFB44fE8hoVAUF8yKrICvQgLaQe-IUSD8hjMSqG0076",
    "__Secure-1PSID": "g.a000zQjjWpM-EcYWAJ4jNOhKpWkIJyE3uiXUs8mkW29dNYg_1-OOrRy7-5sQtfXTOvAP8mcQ8AACgYKAfUSARQSFQHGX2MiAJpq0peR4A0rCsMN0OG_ARoVAUF8yKrRkFZ1NhRtCBx97tGRqRnR0076",
    "__Secure-3PSID": "g.a000zQjjWpM-EcYWAJ4jNOhKpWkIJyE3uiXUs8mkW29dNYg_1-OO7nKV1evVUu2K4RRRXr8ChwACgYKAfgSARQSFQHGX2MiTAlWIgnbdx4GwccDqMLzYhoVAUF8yKp9uYTTuzA4FUMqMtnPX3tJ0076",
    "AEC": "AVh_V2gUefDYXDgU_o7w7M0iW5Jl7WdSaQ9i-yBW1VTb88eZyMVUeau50w",
    "__Secure-1PSIDTS": "sidts-CjIB5H03P-Jirr1kKGqPauIYI3H2OEJk28VFiUojana4j1BhpXhhxK7Hgqop3DRKpeL2wRAA",
    "__Secure-3PSIDTS": "sidts-CjIB5H03P-Jirr1kKGqPauIYI3H2OEJk28VFiUojana4j1BhpXhhxK7Hgqop3DRKpeL2wRAA",
    "SIDCC": "AKEyXzX8HdbvtoNeUSttQ90-T5RR4Ee_T6gE1DFLnI4LsF-u63RwMOg_nkExws8FHnRetxG6jMpf",
    "__Secure-1PSIDCC": "AKEyXzXHWKzVWM5-fVX8FOWfLMYBYIko19TvemguQIIy5wHPHE6zeaF-S8fOvgLSmSUeryJ4_Wo",
    "__Secure-3PSIDCC": "AKEyXzUJB9U_uJQ3LyRPe2hpb75Y6vmjdG2qrX81PlLujJJYYxxrUc5XjGqmt71E1y0wATzIxWe9",
    "NID": "525=hnHO4W0v0YqapmE8R7RbyoYCk7ARJGCE2SiIWXn22VUq4vcmVw87Pm7yAtbVDOyoW_gVse37DKFJ75P_YBYIx1YIgEvFHZaQ2oUbc4sH3F2PPui3PK2p0I5pp_Cwe2aQ-lK5nTfraFOA4i-kbw5raDBrS8eKJuL3ad8lLXA3ZWfvAUcL-kxiB4xsUjCht7HdG68DDH7Pi-KDUlOpdG9RDyEhbLwDJNJDAqAiTo9a7Go0dYO_jl6BIFOWDNQM4F8KUFYHtsqm0ftk7BCI5rP1yvXj0tT7-CJcOiuqVjEOqFADsMzzQkEvFT7I_BC4KJTFzyHh6DbRTrfEzeKrXjVKtuF4Cl9_O09X-gCm3EjKNOT3--a77AOz1jI6wA"
}

def gdrive_create_exports_task(folder_name:str, folder_id:str) -> (str, str, list[str]):
    '''
    创建谷歌云盘导出任务
    :param folder_name: 文件夹名称(请求参数)
    :param folder_id: 文件夹ID(请求参数)
    :return: 导出任务ID, 导出任务状态, 导出任务文件列表
    '''
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Referer": "https://drive.google.com/"
    }
    cookies = gdrive_cookies
    url = "https://takeout-pa.clients6.google.com/v1/exports"
    params = {
        "key": "AIzaSyC1qbk75NzWBvSaDh6KnsjjA9pIrP4lYIE"
    }
    # data = '{"archivePrefix":"0018","items":[{"id":"1Xsp000qDz3t5cEFPPUXNDrLSiuu56sZC"}]}'.encode('unicode_escape')
    data_json = {
        "archivePrefix": folder_name,
        "items": [
            {
                "id": folder_id
            }
        ]
    }
    data = json.dumps(data_json).encode('unicode_escape')
    response = requests.post(url, headers=headers, cookies=cookies, params=params, data=data)
    # print(response.text)
    # print(response)

    return parse_exports_task_archives(response)

def gdrive_query_exports_task(task_id:str) -> (str, str, list[str]):
    '''
    轮询谷歌云盘导出任务
    :param task_id: 导出任务ID
    :return: 导出任务ID, 导出任务状态, 导出任务文件列表
    '''
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Referer": "https://drive.google.com/"
    }
    url = f"https://takeout-pa.clients6.google.com/v1/exports/{task_id}"
    # url = "https://takeout-pa.clients6.google.com/v1/exports/3c2075d3-c116-48c0-9a2f-32146e2c614e"
    params = {
        "key": "AIzaSyC1qbk75NzWBvSaDh6KnsjjA9pIrP4lYIE"
    }
    response = requests.get(url, headers=headers, params=params)
    # print(response.text)
    # print(response)

    return parse_exports_task_archives(response)

def parse_exports_task_archives(response:requests.Response) -> (str, str, list[str]):
    '''
    解析导出任务响应结果
    :param response: 导出任务响应结果
    :return: 导出任务ID, 导出任务状态, 导出任务文件列表
    '''
    data_json = response.json()
    # logger.debug(f"解析响应结果：{data_json}")
    if "exportJob" not in data_json:
        logger.error(f"解析响应结果失败，响应结果：{data_json}")
        return "", "Unknown", []
    exportjob_id = data_json["exportJob"].get("id", "")
    exportjob_status = data_json["exportJob"].get("status", "Unknown")
    exportjob_archives = data_json["exportJob"].get("archives", [])
    logger.debug(f"导出任务结果 exportjob_id: {exportjob_id}, exportjob_status: {exportjob_status}, exportjob_archives: {exportjob_archives}")
    return exportjob_id, exportjob_status, exportjob_archives

def gdrive_download_simple_handler(folder_name:str, folder_id:str, download_dir:str):
    ''' 
    谷歌网盘下载处理(最简洁处理)
    1. 创建导出任务
    2. 轮询导出任务结果
    3. 下载导出任务结果
    :param folder_name: 文件夹名称
    :param folder_id: 文件夹ID
    :param download_dir: 下载目录
    '''
    logger.info(f"开始处理文件夹：{folder_name}，文件夹ID：{folder_id}，下载目录：{download_dir}")
    # 1. 创建导出任务
    task_id, status, archives = gdrive_create_exports_task(folder_name, folder_id)
    if not task_id:
        logger.error(f"创建导出任务失败，task_id: {task_id}, status: {status}, archives: {archives}")
        return
    # 2. 轮询导出任务结果
    while status != export_status_ok:
        task_id, status, archives = gdrive_query_exports_task(task_id)
        logger.info(f"轮询导出任务结果，task_id: {task_id}, status: {status}, archives: {archives}")
        if status == export_status_ok:
            logger.success(f"导出任务成功，task_id: {task_id}, status: {status}, archives: {archives}")
            break
        random_sleep(5, 10)
    # 3. 下载导出任务结果
    if not archives:
        logger.error(f"导出任务结果为空，task_id: {task_id}, status: {status}, archives: {archives}")
        return
    logger.info(f"获取结果成功，一共{len(archives)}个导出文件， 导出文件列表：{archives}")
    # archives = [
    #   {'fileName': '0018_s3_all_raw-001.smc', 'storagePath': 'https://storage.googleapis.com/drive-bulk-export-anonymous/20250804T073625.538Z/4133399871716478688/a7099e1a-c1c6-4659-8fa4-517a72773cd6/1/c4565253-ee49-48bd-91b6-7d12a08377d8', 'compressedSize': '5975017860', 'sizeOfContents': '5975017860'}, 
    #   {'fileName': '0018-20250804T073625Z-1-002.zip', 'storagePath': 'https://storage.googleapis.com/drive-bulk-export-anonymous/20250804T073625.538Z/4133399871716478688/a7099e1a-c1c6-4659-8fa4-517a72773cd6/1/62240b12-53b5-40ab-a847-870ac40f6433', 'compressedSize': '1976011705', 'sizeOfContents': '2033103353'}, 
    #   {'fileName': '0018-20250804T073625Z-1-003.zip', 'storagePath': 'https://storage.googleapis.com/drive-bulk-export-anonymous/20250804T073625.538Z/4133399871716478688/a7099e1a-c1c6-4659-8fa4-517a72773cd6/1/761130fa-f1f6-4f1d-aeb1-ec0f43ba82fc', 'compressedSize': '1804410450', 'sizeOfContents': '1871853079'}, 
    #   {'fileName': '0018-20250804T073625Z-1-004.zip', 'storagePath': 'https://storage.googleapis.com/drive-bulk-export-anonymous/20250804T073625.538Z/4133399871716478688/a7099e1a-c1c6-4659-8fa4-517a72773cd6/1/88b74a9b-f6a7-45a3-9fb2-6ee2f4599569', 'compressedSize': '1484264950', 'sizeOfContents': '1534893581'},
    # ]
    for archive in archives:
        file_name = archive.get('fileName', '')
        storage_path = archive.get('storagePath', '')
        compressed_size = archive.get('compressedSize', '')
        size_of_contents = archive.get('sizeOfContents', '')
        if file_name and storage_path:
            download_resource(storage_path, f"{download_dir}/{file_name}")
        else:
            logger.error(f"导出任务结果为空，file_name: {file_name}, storage_path: {storage_path}")

# 格式化文件大小输出
def format_gdrive_filesize_output(filesize:str) -> str:
    filesize = int(filesize)
    # 如果大于1GB适用GB输出
    if filesize / 1024 / 1024 / 1024 > 1:
        filesize = filesize / 1024 / 1024 / 1024
        return f"{filesize:.2f} GB"
    # 如果大于100MB用MB输出
    elif filesize / 1024 / 1024 > 100:
        filesize = filesize / 1024 / 1024
        return f"{filesize:.2f} MB"
    # 如果大于100KB用KB输出
    elif filesize / 1024 > 100:
        filesize = filesize / 1024
        return f"{filesize:.2f} KB"
    # 其余用B输出
    else:
        return f"{filesize:.2f} B"

# 根据folder_id获取谷歌云盘源链接
def get_google_drive_folder_url(folder_id:str) -> str:
    return f"https://drive.google.com/drive/folders/{folder_id}"

if __name__ == "__main__":
    # task_id, status, archives = gdrive_query_exports_task(task_id="3c2075d3-c116-48c0-9a2f-32146e2c614e")
    # print(task_id, status, archives)

    # gdrive_download_simple_handler("0018", "1Xsp000qDz3t5cEFPPUXNDrLSiuu56sZC", "./downloads/renderme-360")
    gdrive_download_simple_handler("0109", "1yBmoXcru6S0Fq7pR6LcqxSPC_AfmArtp", "./downloads/renderme-360")
