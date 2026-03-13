import sys
import asyncio
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


import datetime
import time
import traceback
from bilibili_api import live
from login_port import login_with_qrcode_term

# 全局变量：记录最后一次收到数据的时间
last_msg_time = time.time()

async def main():
    global last_msg_time
    print("🚀 正在初始化凭证...")
    credential = login_with_qrcode_term()
    room_id = 1950858520

    while True:
        try:
            print(f"\n📡 [{datetime.datetime.now().strftime('%H:%M:%S')}] 开启重启式重连...")
            last_msg_time = time.time() 
            room = live.LiveDanmaku(room_id, credential=credential)

            # --- 1. 弹幕监听 ---
            @room.on('DANMU_MSG')
            async def on_danmaku(event):
                global last_msg_time
                last_msg_time = time.time()
                try:
                    raw_info = event['data']['info']
                    user_name = raw_info[2][1]
                    msg = raw_info[1]
                    ul_level = raw_info[-2][0]
                    timestamp = raw_info[0][4]
                    time_str = datetime.datetime.fromtimestamp(timestamp / 1000.0).strftime('%H:%M:%S')

                    medal_str = ""
                    medal_info = raw_info[3]
                    if medal_info:
                        medal_str = f"[{medal_info[1]} Lv.{medal_info[0]}] "

                    print(f"[{time_str}] {medal_str}UL.{ul_level} {user_name}: {msg}")
                except:
                    pass

            # --- 2. 礼物监听 ---
            @room.on('SEND_GIFT')
            async def on_gift(event):
                global last_msg_time
                last_msg_time = time.time()
                try:
                    g = event['data']['data']
                    gift_name = g['giftName']
                    num = g['num']
                    uname = g['uname']
                    battery = g['total_coin'] // 100 if g['coin_type'] == "gold" else 0
                    battery_str = f"({battery} 电池)" if battery > 0 else "(免费/银瓜子)"
                    print(f"🎁 [礼物] {uname} -> {gift_name} x {num} {battery_str}")
                except:
                    pass

            # --- 3. 观看人数变动 ---
            @room.on('WATCHED_CHANGE')
            async def on_watched(event):
                global last_msg_time
                last_msg_time = time.time()

            # --- 4. 看门狗协程 ---
            async def watchdog():
                global last_msg_time
                while True:
                    await asyncio.sleep(20)
                    idle_time = time.time() - last_msg_time
                    if idle_time > 120: 
                        print(f"⚠️ 连接静默断开（已闲置 {int(idle_time)} 秒），看门狗触发链路重启...")
                        return

            print(f"📡 成功进入直播间 {room_id}，正在实时监控中...")
            
            task_connect = asyncio.create_task(room.connect())
            task_watchdog = asyncio.create_task(watchdog())

            done, pending = await asyncio.wait(
                [task_connect, task_watchdog],
                return_when=asyncio.FIRST_COMPLETED
            )

            # 【黑匣子】检查是谁先结束的，并且是否带有报错
            for task in done:
                try:
                    exc = task.exception()
                    if exc:
                        print(f"❌ 内部任务崩溃: {type(exc).__name__}: {exc}")
                except asyncio.CancelledError:
                    pass

            # 安全销毁残留任务
            for p in pending:
                p.cancel()
            
            # 等待取消操作真正落实，防止后台死锁
            await asyncio.gather(*pending, return_exceptions=True)
            
            try:
                await room.disconnect()
            except:
                pass

        # 【防弹衣】抓取包括 KeyboardInterrupt 和 CancelledError 在内的所有致命异常
        except BaseException as e:
            # 如果是手动按了 Ctrl+C，优雅退出
            if isinstance(e, KeyboardInterrupt):
                print("\n👋 监控程序已手动退出")
                break
            
            print(f"\n💥 导致退出的致命异常 (BaseException): {type(e).__name__} - {e}")
            traceback.print_exc() # 打印详细的红色错误栈
        
        print("🔄 5秒后进行完整链路重置...")
        await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(main())