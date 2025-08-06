import dotenv
dotenv.load_dotenv()

import csv
import gdown
import os
from pprint import pformat

from utils.logger import logger
from utils.ucsv import read_csv
from utils.lark import alarm_lark_text
from utils.request import download_resource, get_download_speed
from utils.utime import get_now_time_string, get_time_stamp, random_sleep, format_second_to_time_string
import concurrent.futures

from handler.gdrive_web import gdrive_create_exports_task, gdrive_query_exports_task, format_gdrive_filesize_output, get_google_drive_folder_url
from handler.gdrive_web import export_status_ok, export_status_queue, gdrive_cookies

# 使用gdown脚手架下载
# 容易触发下载风控：
# # Too many users have viewed or downloaded this file recently. Please
# # try accessing the file again later. If the file you are trying to
# # access is particularly large or is shared with many people, it may
# # take up to 24 hours to be able to view or download the file. If you
# # still can't access a file after 24 hours, contact your domain
# # administrator.
def gdown_renderme360_handler():
    csv_path = "renderme-360_dataset_folders.csv"
    with open(csv_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            folder_name = row['folder_name']
            folder_id = row['folder_id']
            output_dir = f"./renderme-360/{folder_name}"
            os.makedirs(output_dir, exist_ok=True)
            # [!] 部分文件夹可能未下载完全
            # 判断是否已经下载
            # if os.listdir(output_dir):
            #     print(f"[GDRIVE DOWNLOADER] 数据集renderme-360 {folder_name} 已存在，跳过下载")
            #     continue
            try:
                # 下载Google Drive文件夹
                gdown.download_folder(
                    id=folder_id, url=None,
                    output=output_dir, 
                    use_cookies=True,  # cookie path: ~\.cache\gdown
                    skip_download=False, 
                    resume=True,
                    quiet=False,  # 显示下载进度
                )
            except Exception as e:
                print(f"下载 {folder_name} 失败: {e}")
                alarm_lark_text(
                    text=f"[GDRIVE DOWNLOADER] 数据集renderme-360 下载 {folder_name} 失败: {e}",
                )
                # 文件夹为空，删除空文件夹
                if not os.listdir(output_dir):
                    os.rmdir(output_dir)
            else:
                alarm_lark_text(
                    text=f"[GDRIVE DOWNLOADER] 数据集renderme-360 下载 {folder_name} 成功\n\t下载路径: {output_dir}",
                )
            finally:
                random_sleep(30,50)

def download_gdrive_archive(archive:dict, folder_name:str, folder_id:str, download_dir:str, webhook:str):
    '''
    下载谷歌网盘导出任务结果

    :param archive: 导出任务结果
    :param folder_name: 文件夹名称
    :param folder_id: 文件夹ID
    :param download_dir: 下载目录
    :param webhook: 飞书webhook
    '''
    try:
        file_name = archive.get('fileName', '')
        storage_path = archive.get('storagePath', '')
        compressed_size = str(archive.get('compressedSize', '-1'))
        size_of_contents = str(archive.get('sizeOfContents', '-1'))
        download_filename = f"{download_dir}/{file_name}"
        if not (file_name and storage_path):
            logger.error(f"archive任务解析失败，file_name: {file_name}, storage_path: {storage_path}")
            raise Exception(f"archive任务解析失败，file_name: {file_name}, storage_path: {storage_path}")
        if os.path.exists(download_filename):
            logger.info(f"文件 {download_filename} 已存在，跳过下载")
            return
        logger.info(f"准备下载url：{storage_path} 到 {download_filename}，文件大小：{compressed_size}")
        start_time = get_time_stamp()  # 记录下载开始时间

        download_resource(storage_path, download_filename, max_speed_mbps=int(os.getenv("DOWNLOAD_SPEED_MBPS", -1)))

        end_time = get_time_stamp()  # 记录下载结束时间
        file_size = os.path.getsize(download_filename)  # 获取文件大小（字节）
        time_used = end_time - start_time  # 计算下载用时（秒）
        download_speed = get_download_speed(file_size, time_used)

        alarm_lark_text(
            webhook=webhook,
            text=f"[GDRIVE DOWNLOADER] 数据集 `renderme-360` 文件夹 {folder_name} 下文件 {file_name} 下载成功 \n\t文件位置：{download_filename} \n\t源链接：{storage_path} \n\t文件大小：{format_gdrive_filesize_output(compressed_size)} \n\t解压后大小：{format_gdrive_filesize_output(size_of_contents)} \n\t下载时长：{format_second_to_time_string(time_used)} \n\t下载速率：{download_speed} \n\t告警时间：{get_now_time_string()}",
        )
    except Exception as e:
        logger.error(f"下载文件 {file_name} 失败，文件夹：{folder_name}，文件夹ID：{folder_id}，archive：{archive}，error: {e}")
        alarm_lark_text(
            webhook=webhook,
            text=f"[GDRIVE DOWNLOADER] 数据集 `renderme-360` 文件夹 {folder_name} 下文件 {file_name} 下载失败 \n\t文件位置：{download_filename} \n\t源链接：{storage_path} \n\t文件大小：{format_gdrive_filesize_output(compressed_size)} \n\terror: {e} \n\t告警时间：{get_now_time_string()}",
        )
    
def reverse_web_download_renderme360_handler(folder_name:str, folder_id:str, download_dir:str):
    ''' 
    谷歌网盘文件批量下载，基于模拟google.com/v1/exports网页接口生成任务压缩文件并下载压缩包

    - 修改自`handler/gdrive_web`.`gdrive_download_simple_handler`
    - 1. 创建导出任务
    - 2. 轮询导出任务结果
    - 3. 下载导出任务结果

    :param folder_name: 文件夹名称
    :param folder_id: 文件夹ID
    :param download_dir: 下载目录
    '''
    lark_webhook = os.getenv("LARK_WEBHOOK")
    logger.info(f"开始处理文件夹：{folder_name}，文件夹ID：{folder_id}，下载目录：{download_dir}")
    try:
        # 1. 创建导出任务
        task_id, status, archives = gdrive_create_exports_task(folder_name, folder_id)
        if not task_id:
            logger.error(f"创建导出任务失败，task_id: {task_id}, status: {status}, archives: {archives}")
            raise Exception(f"创建导出任务失败，task_id: {task_id}, status: {status}, archives: {archives}")
        # 2. 轮询导出任务结果
        query_time_limit = 900 # 15分钟
        query_st_time = get_time_stamp()
        while status != export_status_ok:
            if get_time_stamp() - query_st_time >= query_time_limit:
                logger.error(f"轮询导出任务结果超时，task_id: {task_id}")
                raise Exception(f"轮询导出任务结果超时，task_id: {task_id}")
            if status != export_status_queue:
                logger.error(f"导出任务状态异常，task_id: {task_id}, status: {status}, archives: {archives}")
                raise Exception(f"导出任务状态异常，task_id: {task_id}, status: {status}, archives: {archives}")
            task_id, status, archives = gdrive_query_exports_task(task_id)
            logger.info(f"轮询导出任务结果，task_id: {task_id}, status: {status}, archives: {archives}")
            if status == export_status_ok:
                logger.success(f"导出任务成功，task_id: {task_id}, status: {status}, archives: {archives}")
                break
            random_sleep(5, 10)
        if not archives:
            logger.error(f"导出任务结果为空，task_id: {task_id}, status: {status}, archives: {archives}")
            raise Exception(f"导出任务结果为空，task_id: {task_id}, status: {status}, archives: {archives}")
    except Exception as e:
        logger.error(f"获取导出任务失败，文件夹：{folder_name}，文件夹ID：{folder_id}，error: {e}")
        alarm_lark_text(
            text=f"[GDRIVE DOWNLOADER] 数据集 `renderme-360` 文件夹 {folder_name} 导出任务失败 \n\t源链接：{get_google_drive_folder_url(folder_id)} \n\terror: {e} \n\t告警时间：{get_now_time_string()}",
        )
        return
    else:
        logger.info(f"获取导出结果成功，一共{len(archives)}个导出文件， 导出文件列表：{archives}")
        alarm_lark_text(
            text=f"[GDRIVE DOWNLOADER] 数据集 `renderme-360` 文件夹 {folder_name} 导出任务成功 \n\t源链接：{get_google_drive_folder_url(folder_id)} \n\t一共{len(archives)}个导出文件 \n\t导出文件列表：\n{pformat(archives)} \n\t告警时间：{get_now_time_string()}",
        )

    # 3. 下载导出任务结果(并行)   
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
        # 提交所有下载任务到进程池
        futures = [
            executor.submit(
                download_gdrive_archive,
                archive,
                folder_name,
                folder_id,
                download_dir,
                lark_webhook
            )
            for archive in archives
        ]
        
        # 等待所有任务完成
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"下载文件时发生异常: {e}")
                alarm_lark_text(
                    text=f"[GDRIVE DOWNLOADER] 数据集 `renderme-360` 文件夹 {folder_name} 下载文件时发生异常: {e} \n\t告警时间：{get_now_time_string()}",
                )

def filiter_renderme360_dataset_folders(csv_file:str, latest_download_folder_name:str='0090'):
    ''' 过滤跳过处理已经下载好的文件夹folder_name '''
    result_list = []
    batch = read_csv(csv_file)
    for batch_row in batch:
        for row in batch_row:
            folder_name = row['folder_name']
            # 比较文件夹名称（作为字符串比较，因为它们是等长的数字字符串）
            if folder_name > latest_download_folder_name:
                result_list.append(row)
    return result_list

if __name__ == "__main__":
    TARGET_CSV = "renderme-360_dataset_folders.csv"
    DOWNLOAD_PATH = r"./downloads/renderme-360" if os.getenv("DOWNLOAD_PATH","") == "" else os.getenv("DOWNLOAD_PATH")
    # gdown_renderme360_handler()

    # 读取renderme-360_dataset_folders.csv的folder_name,folder_id
    folder_list = filiter_renderme360_dataset_folders(TARGET_CSV, latest_download_folder_name='0090')
    for data in folder_list:
        folder_id = data["folder_id"]
        folder_name = data["folder_name"]
        alarm_lark_text(
            webhook=os.getenv("LARK_WEBHOOK"),
            text=f"[GDRIVE DOWNLOADER] 开始处理数据集 `renderme-360` 文件夹 {folder_name} \n\t文件夹ID：{folder_id} \n\t进度：{folder_list.index(data)+1}/{len(folder_list)} \n\t告警时间：{get_now_time_string()}",
        )
        reverse_web_download_renderme360_handler(
            folder_id=folder_id,
            folder_name=folder_name,
            download_dir=DOWNLOAD_PATH,
        )
