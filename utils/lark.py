import requests
from os import getenv
from time import sleep
from random import randint
from utils.logger import logger

# class LarkNotice():
#     def __init__(self, notice_text) -> None:
#         self.notice_text = notice_text

def alarm_lark_text(text:str, webhook:str='', retry:int=3):
    """
    飞书机器人告警

    :param webhook string: 飞书机器人webhook
    :param text string: 告警信息
    :param retry int: 重新尝试发送的次数
    :return: None
    """
    # Expamle Json Send
    # {
	#     "msg_type": "text",
	#     "content": {"text": "test hello world."}
    # }
    try:
        webhook = getenv("LARK_WEBHOOK") if webhook == "" else webhook
        if webhook == "":
            logger.ero("[utils.lark] webhook is empty, skip alarm to lark.")
            raise ValueError("lark webhook is empty")
        params = {
            "msg_type": "text",
            "content": {"text": f"{text}"}
        }
        # print(f"request: {webhook} | {params}")
        resp = requests.post(url=webhook, json=params)
        # print(f"response: {resp.status_code} {resp.content}")
        assert resp.status_code == 200
        assert resp.json()["code"] == 0
    except Exception as e:
        logger.error(f"[utils.lark] [!] 发送飞书失败: {e}")
        if retry > 0:
            sleep(randint(3,5))
            return alarm_lark_text(webhook=webhook, text=text, retry=retry-1)
        else:
            # raise e
            logger.error(f"[utils.lark] [!] 重试过多失败退出")
            return
    else:
        logger.debug(f"[utils.lark] 已通知飞书: {webhook}")
