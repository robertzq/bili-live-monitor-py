import asyncio
import datetime
import time
import traceback
import os
import sys
from dotenv import load_dotenv
from bilibili_api import live, user
from login_port import login_with_qrcode_term

# 加载 .env 配置文件
load_dotenv()

# 全局变量
last_msg_time = time.time()
log_file = None

def get_log_filename(uname, room_id):
    """生成：主播名_房间号_日期.txt"""
    date_str = datetime.datetime.now().strftime('%Y%m%d')
    return f"{uname}_{room_id}_{date_str}.txt"

def write_log(msg, use_raw_time=False, custom_time=None):
    """
    打印到终端并写入文件
    custom_time: 传入弹幕自带的精确时间戳字符串
    """
    global log_file
    # 如果弹幕自带了时间戳，就用弹幕的，否则用系统当前时间
    display_time = custom_time if custom_time else datetime.datetime.now().strftime('%H:%M:%S')
    full_msg = f"[{display_time}] {msg}"
    
    print(full_msg)
    if log_file:
        log_file.write(full_msg + "\n")
        log_file.flush()

async def main():
    global last_msg_time, log_file
    
    room_id_env = os.getenv("ROOM_ID")
    room_uname = os.getenv("ROOM_UNAME")
    if not room_id_env:
        print("❌ 错误: 请在 .env 文件中设置 ROOM_ID")
        return
    room_id = int(room_id_env)

    print("🚀 正在初始化凭证...")
    credential = login_with_qrcode_term()

    uname = room_uname

    filename = get_log_filename(uname, room_id)
    log_file = open(filename, "a", encoding="utf-8")
    write_log(f"✅ 监控启动！目标主播: {uname} ({room_id})")

    while True:
        try:
            write_log("📡 开启重启式重连循环...")
            last_msg_time = time.time() 
            room = live.LiveDanmaku(room_id, credential=credential)

            # --- 1. 弹幕监听 (带勋章、UL等级、精确时间) ---
            @room.on('DANMU_MSG')
            async def on_danmaku(event):
                global last_msg_time
                last_msg_time = time.time()
                try:
                    raw_info = event['data']['info']
                    
                    # 内容与基本信息
                    msg = raw_info[1]
                    user_name = raw_info[2][1]
                    
                    # 用户等级 (UL)
                    ul_level = raw_info[-2][0]
                    
                    # 勋章信息
                    medal_str = ""
                    medal_info = raw_info[3]
                    if medal_info:
                        medal_str = f"[{medal_info[1]} Lv.{medal_info[0]}] "
                    
                    # 弹幕自带的精确时间戳
                    timestamp = raw_info[0][4]
                    time_str = datetime.datetime.fromtimestamp(timestamp / 1000.0).strftime('%H:%M:%S')

                    write_log(f"{medal_str}UL.{ul_level} {user_name}: {msg}", custom_time=time_str)
                except:
                    pass

            # --- 2. 礼物监听 (带电池换算) ---
            @room.on('SEND_GIFT')
            async def on_gift(event):
                global last_msg_time
                last_msg_time = time.time()
                try:
                    g = event['data']['data']
                    gift_name = g['giftName']
                    num = g['num']
                    uname = g['uname']
                    
                    # 电池计算 (100金瓜子 = 1电池)
                    battery = g['total_coin'] // 100 if g['coin_type'] == "gold" else 0
                    battery_str = f"({battery} 电池)" if battery > 0 else "(免费/银瓜子)"
                    
                    write_log(f"🎁 [礼物] {uname} -> {gift_name} x {num} {battery_str}")
                except:
                    pass

            # --- 3. 人数变动 ---
            @room.on('WATCHED_CHANGE')
            async def on_watched(event):
                global last_msg_time
                last_msg_time = time.time()

            # --- 4. 看门狗 ---
            async def watchdog():
                global last_msg_time
                while True:
                    await asyncio.sleep(20)
                    if time.time() - last_msg_time > 120: 
                        write_log("⚠️ 链路静默超过120秒，触发重启...")
                        return

            write_log("📡 已进入直播间，实时监控中...")
            
            task_connect = asyncio.create_task(room.connect())
            task_watchdog = asyncio.create_task(watchdog())

            done, pending = await asyncio.wait(
                [task_connect, task_watchdog],
                return_when=asyncio.FIRST_COMPLETED
            )

            for p in pending: p.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            try:
                await room.disconnect()
            except:
                pass

        except BaseException as e:
            if isinstance(e, KeyboardInterrupt):
                write_log("👋 监控程序已手动退出")
                break
            write_log(f"💥 异常: {type(e).__name__} - {e}")
            traceback.print_exc()
        
        await asyncio.sleep(5)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        if log_file:
            log_file.close()