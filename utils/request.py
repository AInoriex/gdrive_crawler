import os
import time
from fake_useragent import UserAgent
from random import choice, randint
import requests
import urllib.request as request

def get_file_size(filePath):
    ''' 获取本地文件大小(MB) '''
    fsize = os.path.getsize(filePath)
    return round(fsize / float(1024 * 1024), 2)

def get_download_speed(file_size:float, time_seconds_used:int):
    """
    计算下载速度
    :param file_size: 文件大小（字节Byte）
    :param time_seconds_used: 下载时间（秒）
    :return: 下载速度
    """
    if time_seconds_used > 0:
        download_speed = file_size / time_seconds_used / 1024
        if download_speed >= 1000:
            speed_str = f"{download_speed / 1024:.2f} MB/s"
        else:
            speed_str = f"{download_speed:.2f} KB/s"
    else:
        speed_str = "NA"
    return speed_str

def get_random_headers():
    ''' 随机生成请求头
    
    @Example Header
    {
        'sec-ch-ua': '"Firefox";v="99", "Gecko";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"', 
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36', 
        'Accept': 'text/html,application/json;q=0.9,application/x-www-form-urlencoded;q=0.8,application/xml;q=0.8,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'Accept-Charset': 'utf-8'
    }
    '''
    from fake_useragent import UserAgent
    ua = UserAgent()

    # 随机选择浏览器类型
    browser_type = choice(['chrome', 'firefox', 'safari', 'edge', 'opera'])

    # 随机选择是移动端还是网页端
    is_mobile = choice([True, False])

    # 随机选择操作系统
    if is_mobile:
        os = choice(['android', 'ios'])
    else:
        # os = choice(['windows', 'macos', 'linux'])
        os = choice(['windows', 'macos'])

    # 随机生成 sec-ch-ua 字段
    if browser_type == 'chrome':
        sec_ch_ua = '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"'
    elif browser_type == 'firefox':
        sec_ch_ua = '"Firefox";v="99", "Gecko";v="99"'
    elif browser_type == 'safari':
        sec_ch_ua = '"Safari";v="99", "WebKit";v="99"'
    elif browser_type == 'edge':
        sec_ch_ua = '"Microsoft Edge";v="99", "Chromium";v="99"'
    else:
        sec_ch_ua = '"Opera";v="99", "Chromium";v="99"'

    # 随机生成 sec-ch-ua-mobile 字段
    sec_ch_ua_mobile = "?1" if is_mobile else "?0"

    # 随机生成 sec-ch-ua-platform 字段
    if os == 'windows':
        sec_ch_ua_platform = '"Windows"'
    elif os == 'macos':
        sec_ch_ua_platform = '"macOS"'
    elif os == 'linux':
        sec_ch_ua_platform = '"Linux"'
    elif os == 'android':
        sec_ch_ua_platform = '"Android"'
    else:
        sec_ch_ua_platform = '"iOS"'

    # 随机生成 User-Agent 字段
    user_agent = ua.random

    # 定义固定的 Accept, Accept-Encoding, Accept-Language, Accept-Charset 字段
    accept = "text/html,application/json;q=0.9,application/x-www-form-urlencoded;q=0.8,application/xml;q=0.8,image/avif,image/webp,image/apng,*/*;q=0.8"
    accept_encoding = "gzip, deflate, br"
    accept_language = "en-GB,en-US;q=0.9,en;q=0.8"
    accept_charset = "utf-8"

    # 构造请求头字典
    headers = {
        "sec-ch-ua": sec_ch_ua,
        "sec-ch-ua-mobile": sec_ch_ua_mobile,
        "sec-ch-ua-platform": sec_ch_ua_platform,
        "User-Agent": user_agent,
        "Accept": accept,
        "Accept-Encoding": accept_encoding,
        "Accept-Language": accept_language,
        "Accept-Charset": accept_charset
    }

    return headers

def download_resource(url:str, filename:str, proxies=None, download_size_limit:int=-1, max_speed_mbps:int=-1, retry:int=3)->str:
    """
    使用代理服务器从url处下载文件到本地的filename

    :param url: 要下载的文件的url
    :param filename: 保存到本地的文件名
    :param proxies: 下载代理服务器，格式为{"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
    :param download_size_limit: 下载大小限制，单位为MB，-1表示不限制
    :param max_speed_mbps: 最大下载速度，单位为Mbps，-1表示不限制
    :param retry: 重试次数，默认3次
    :return: 下载后的文件路径

    """
    # print(f"download_resource > 参数：{url} -- {filename}")
    if url == "" or filename == "":
        raise ValueError(f"download_resource url or filename is empty, url:{url}, filename:{filename}")
    if max_speed_mbps <= 0:
        max_speed_mbps = 1024 # 默认最高限制1024MB/s
    max_speed_bytes = max_speed_mbps * 1024 * 1024  # 转换为字节/秒
    try:
        # 发送请求，设置流式响应以便跟踪下载进度
        response = requests.get(url, headers=get_random_headers(), proxies=proxies, stream=True, timeout=30)
        response.raise_for_status()  # 检查请求是否成功
        # 获取文件总大小
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        # 计算每个chunk应该耗费的最小时间
        chunk_size=8192
        min_chunk_time = chunk_size / max_speed_bytes
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=chunk_size):  # 每次读取8KB
                if chunk:  # 过滤掉保持连接的新块
                    start_time = time.time()
                    file.write(chunk)
                    downloaded_size += len(chunk)
                    # 打印下载进度
                    if downloaded_size // 16384 == 0:  # 每下载16KB打印一次进度
                        continue
                    if total_size != 0:
                        print(f"\rdownload_resource > {os.path.basename(filename)} 文件大小：{total_size/1048576:.2f}MB | 下载进度：{downloaded_size/total_size*100:.2f}%", end='')
                    # 检查已下载文件大小是否超过限制，如果超过则停止下载
                    if download_size_limit > 0 and downloaded_size >= download_size_limit * 1024 * 1024:
                        raise InterruptedError(f"download_resource > 文件下载超过{download_size_limit}MB限制，停止下载：{filename}")
                    # 计算实际耗费时间
                    elapsed_time = time.time() - start_time
                    # 如果下载太快，则暂停以限制速率
                    if elapsed_time < min_chunk_time:
                        time.sleep(min_chunk_time - elapsed_time)
        # 判断如果文件为空 下载失败
        if get_file_size(filename) <= 0.0:
            raise Exception(f"download_resource > 文件下载为空：{filename}")
        print(f"\ndownload_resource > 文件已下载到：{filename}")
        return filename
    except InterruptedError:
        print(f"\ndownload_resource > 下载文件 {filename} 中断")
        return filename
    except Exception as e:
        print(f"\ndownload_resource > 下载文件时发生异常：{e}")
        if retry > 0:
            time.sleep(randint(3,5))
            return download_resource(url=url, filename=filename, proxies=proxies, retry=retry-1)
        # 清理下载异常文件
        if os.path.exists(filename):
            os.remove(filename)
        raise Exception(f"download_resource 下载文件 {url}->{filename} 失败, {e}")
