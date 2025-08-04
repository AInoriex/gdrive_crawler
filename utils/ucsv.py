import csv

def read_csv(file_path, batch_size=1000):
    """
    分批读取CSV文件内容，支持大批量数据。
    
    :param file_path: CSV文件路径
    :param batch_size: 每次读取的行数，默认为1000
    :yield: 每次返回一个批次的数据，数据为列表形式，每行是一个字典
    """
    with open(file_path, mode='r', encoding='utf-8', newline='') as file:
        reader = csv.DictReader(file)
        batch = []
        for row in reader:
            batch.append(row)
            if len(batch) == batch_size:
                yield batch
                batch = []
        if batch:
            yield batch  # 返回剩余的不足一个批次的数据

def write_csv(file_path, data, fieldnames=None, mode='a'):
    """
    将数据写入CSV文件，支持追加模式。
    
    :param file_path: CSV文件路径
    :param data: 要写入的数据，数据为列表形式，每行是一个字典
    :param fieldnames: CSV文件的列名，如果为None，则自动从数据中提取
    :param mode: 写入模式，默认为追加模式'a'
    """
    if mode not in ['a', 'w']:
        raise ValueError("mode must be 'a' (append) or 'w' (write)")

    if not data:
        return  # 如果没有数据，则直接返回

    if fieldnames is None:
        fieldnames = list(data[0].keys())  # 从数据中提取列名

    with open(file_path, mode=mode, encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if mode == 'w':
            writer.writeheader()  # 如果是写入模式，写入表头
        writer.writerows(data)
