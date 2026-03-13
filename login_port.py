# login_port.py
import sys
import time
from bilibili_api import Credential, sync
from bilibili_api.login_v2 import QrCodeLogin, QrCodeLoginEvents
from bilibili_api.exceptions import LoginError

def login_with_qrcode_term() -> Credential:
    """
    终端扫描二维码登录 (极简提炼版)
    """
    qrcode = QrCodeLogin()
    sync(qrcode.generate_qrcode())
    print(qrcode.get_qrcode_terminal() + "\n")
    
    while True:
        result = sync(qrcode.check_state())
        if result == QrCodeLoginEvents.SCAN:
            sys.stdout.write("\r [状态] 请在手机上确认登录...")
            sys.stdout.flush()
        elif result == QrCodeLoginEvents.CONF:
            sys.stdout.write("\r [状态] 已扫码，请点下确认啊！")
            sys.stdout.flush()
        elif result == QrCodeLoginEvents.TIMEOUT:
            print("\n⚠️ 二维码过期，正在生成新二维码！")
            sync(qrcode.generate_qrcode())
            print(qrcode.get_qrcode_terminal() + "\n")
        elif result == QrCodeLoginEvents.DONE:
            print("\n✅ 成功获取高权重登录凭证！")
            return qrcode.get_credential()
        time.sleep(0.5)

__all__ = ['login_with_qrcode_term']