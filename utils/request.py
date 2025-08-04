import os
import time
from fake_useragent import UserAgent
from random import choice, randint
import requests
import urllib.request as request

def get_file_size(filePath):
    ''' 获取文件大小(MB) '''
    fsize = os.path.getsize(filePath)
    return round(fsize / float(1024 * 1024), 2)

def get_random_ua():
    """
    Generates a random User-Agent based on a random OS and browser
    
    The random OS can be one of Windows, macOS, or Linux.
    The random browser can be one of safari, firefox, edge (on Windows), or chrome (on Windows or macOS).
    
    Returns a dictionary with three keys: "os", "browser", and "ua", containing the random OS, browser, and User-Agent, respectively.
    """
    # os_list = ["Windows", "macOS", "Linux"]
    # operate_sys = choice(os_list)
    # # print(f"随机os > {operate_sys}")
    # browsers_list = ['safari', 'firefox']
    # if operate_sys == "Windows":
    #     browsers_list.append("edge")
    # if operate_sys != 'Linux':
    #     browsers_list.append("chrome")
    # br = choice(browsers_list)
    # # print(f"随机browser > {br}")
    ua = UserAgent(browsers=['chrome'], os=['windows'])
    user_agent = ua.random
    # print(f"随机生成的User-Agent: {user_agent}")
    return {
        "os": 'Windows',
        "browser": 'chrome',
        "ua": user_agent
    }

def download_resource(url:str, filename:str, proxies=None, download_size_limit:int=-1, retry:int=3):
    """
    使用代理服务器从url处下载文件到本地的filename

    :param url: 要下载的文件的url
    :param filename: 保存到本地的文件名
    :return: None
    """
    # print(f"download_resource > 参数：{url} -- {filename}")
    if url == "" or filename == "":
        raise ValueError(f"download_resource url or filename is empty, url:{url}, filename:{filename}")
    ua = get_random_ua()
    headers = {
        'accept-language': 'zh-CN,zh;q=0.9,en-GB;q=0.8,en;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'sec-ch-ua': '"Microsoft Edge";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        'sec-ch-ua-mobile': '?0',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'sec-ch-ua-platform': ua.get('os'),
        'user-agent': ua.get('ua'),
    }
    
    try:
        # 发送请求，设置流式响应以便跟踪下载进度
        response = requests.get(url, headers=headers, proxies=proxies, stream=True)
        response.raise_for_status()  # 检查请求是否成功
        
        # 获取文件总大小
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):  # 每次读取8KB
                if chunk:  # 过滤掉保持连接的新块
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
        
        # 判断如果文件为空 下载失败
        if get_file_size(filename) <= 0.0:
            raise Exception(f"download_resource > 文件下载为空：{filename}")
        print(f"\ndownload_resource > 文件已下载到：{filename}")
        return filename
    except InterruptedError:
        print(f"\ndownload_resource > 下载文件 {filename} 中断")
        return filename
    except Exception as e:
        print(f"\ndownload_resource > 下载文件时发生错误：{e}")
        if retry > 0:
            time.sleep(randint(3,5))
            return download_resource(url=url, filename=filename, proxies=proxies, retry=retry-1)
        # 判断如果文件为空清理空文件
        if os.path.exists(filename):
            os.remove(filename)
        raise Exception(f"下载文件 {url} 失败, {e}")
