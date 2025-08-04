# -*- coding: UTF8 -*-

import os
import time
import json
import requests

def get_file_size(filePath):
    ''' 获取文件大小(MB) '''
    fsize = os.path.getsize(filePath)
    return round(fsize / float(1024 * 1024), 2)

def write_json_to_file(json_obj, filename:str):
    ''' json数据写入文件
    @json_obj: 待写入数据
    @out_file: 输出文件
    '''
    with open(filename, "w", encoding="utf8") as f:
        json.dump(json_obj, f, indent=4, ensure_ascii=False)
    print(f"write_json_to_file > 数据已写入文件: {filename}")

def add_json_to_file(json_obj, filename:str):
    ''' json数据追加写入文件
    @json_obj: 待写入数据
    @out_file: 输出文件
    '''
    with open(filename, "r", encoding="utf8") as f:
        data = json.load(f)
    data.append(json_obj)
    with open(filename, "w", encoding="utf8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"add_json_to_file > 数据已追加写入文件: {filename}")

def write_csv_to_file(csv_string:str, filename:str):
    ''' csv字符串文本写入文件
    @csv_string: 待写入数据
    @out_file: 输出文件
    '''
    with open(filename, "w", encoding="utf8") as f:
        f.write(csv_string)
        f.write("\n")
    print(f"write_csv_to_file > 数据已写入文件: {filename}")

def add_csv_to_file(csv_string:str, filename:str):
    ''' 追加csv字符串文本到文件
    @csv_string: 待追加数据
    @out_file: 输出文件
    '''
    with open(filename, "a", encoding="utf8") as f:
        f.write(csv_string)
        f.write("\n")
    print(f"add_csv_to_file > 数据已追加文件: {filename}")

def write_string_to_file(text_string:str, filename:str):
    ''' 字符串文本写入文件
    @text_string: 待写入数据
    @out_file: 输出文件
    '''
    with open(filename, "w", encoding="utf8") as f:
        f.write(text_string)
    print(f"write_string_to_file > 数据已写入文件: {filename}")

def add_string_to_file(text_string:str, filename:str):
    ''' 追加字符串文本到文件
    @text_string: 待追加数据
    @out_file: 输出文件
    '''
    with open(filename, "a", encoding="utf8") as f:
        f.write("\n")
        f.write(text_string)
    print(f"add_string_to_file > 数据已追加文件: {filename}")

def remove_file(local_path):
    os.remove(local_path)
    print(f"已删除本地文件: {local_path}")

def read_file(filename:str):
    with open(filename, mode="r", encoding="utf-8") as f:
        res = f.read()
    return res

def read_file_with_lines(filename:str):
    with open(filename, mode="r", encoding="utf-8") as f:
        res = f.read().splitlines()
    return res

# 列举文件夹文件
def list_files_in_folder(folder_path:str):
    files = os.listdir(folder_path)
    return files
