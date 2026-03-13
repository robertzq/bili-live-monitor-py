import asyncio
import datetime
from bilibili_api import live, sync, Credential
from login_port import login_with_qrcode_term

async def main():
    print("🚀 正在初始化凭证...")
    # 1. 扫码登录拿到凭证（只扫一次）
    credential = login_with_qrcode_term()
    room_id = 1950858520
    
    # 统计运行信息
    start_time = datetime.datetime.now()

    while True:
        try:
            print(f"\n📡 [{datetime.datetime.now().strftime('%H:%M:%S')}] 尝试建立新连接...")
            
            # 关键：每次循环都创建一个全新的 room 实例
            room = live.LiveDanmaku(room_id, credential=credential)

            @room.on('DANMU_MSG')
            async def on_danmaku(event):
                try:
                    raw_info = event['data']['info']
                    user_name = raw_info[2][1]
                    msg = raw_info[1]
                    
                    # 修复后的等级抓取：UL.43 这种主站等级通常在倒数第二个元素
                    ul_level = raw_info[-2][0]
                    timestamp = raw_info[0][4]
                    time_str = datetime.datetime.fromtimestamp(timestamp / 1000.0).strftime('%H:%M:%S')

                    # 勋章（灯牌）
                    medal_str = ""
                    medal_info = raw_info[3]
                    if medal_info:
                        medal_str = f"[{medal_info[1]} Lv.{medal_info[0]}] "

                    print(f"[{time_str}] {medal_str}UL.{ul_level} {user_name}: {msg}")
                except:
                    pass

            @room.on('SEND_GIFT')
            async def on_gift(event):
                try:
                    g = event['data']['data']
                    battery = g['total_coin'] // 100 if g['coin_type'] == "gold" else 0
                    print(f"🎁 [礼物] {g['uname']} -> {g['giftName']} x {g['num']} ({battery} 电池)")
                except:
                    pass

            # 设置超时检查：如果 5 分钟没有任何消息，也可以考虑重连（可选）
            # 这里先使用最直接的连接方式
            await room.connect()
            
            # 如果 connect() 正常返回了，说明连接被服务端关闭了
            print("💡 连接被服务器正常关闭，准备重连...")

        except Exception as e:
            print(f"⚠️ 捕获到连接异常: {e}")
        
        # 无论成功失败，休息 5 秒后彻底重启
        print("🔄 5秒后进行完整链路重启...")
        await asyncio.sleep(5)

if __name__ == '__main__':
    try:
        # 使用新的运行方式
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 监控已手动停止")