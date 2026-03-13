import os
import sys
import re
from collections import defaultdict

def analyze_bili_log(file_path):
    if not os.path.exists(file_path):
        print(f"❌ 错误: 找不到日志文件 -> {file_path}")
        return

    total_battery = 0
    gifter_rank = defaultdict(int)

    # 核心魔法：正则表达式
    # 匹配规则：查找包含 "🎁 [礼物]" 和 "(xxx 电池)" 的行，提取用户名和电池数
    # (?:\[.*?\] )? 用于跳过可选的粉丝勋章，精准抓取名字
    pattern = re.compile(r'🎁 \[礼物\] (?:\[.*?\] )?(.*?) -> .*? \((\d+) 电池\)')

    print(f"⏳ 正在扫描分析日志: {file_path} ...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = pattern.search(line)
            if match:
                uname = match.group(1).strip()
                battery = int(match.group(2))
                
                total_battery += battery
                gifter_rank[uname] += battery

    # 生成 Top 5 排行榜
    top_5 = sorted(gifter_rank.items(), key=lambda x: x[1], reverse=True)[:5]
    rank_str = "\n".join([f"  NO.{i+1} {name}: {batt} 电池" for i, (name, batt) in enumerate(top_5)])
    
    if not rank_str: 
        rank_str = "  (日志中暂无金瓜子礼物记录)"

    # 打印最终报表
    print(f"\n{'='*40}")
    print(f"📊 战绩统计报告")
    print(f"{'-'*40}")
    print(f"🔋 累计接收电池: {total_battery}\n")
    print(f"🔥 贡献榜 Top 5:")
    print(f"{rank_str}")
    print(f"{'='*40}\n")

if __name__ == '__main__':
    # 支持命令行直接传文件名，比如: python analyze_log.py jiojio_1950858520_20260313.txt
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
    else:
        # 如果不传参数，让用户手动输入
        target_file = input("👉 请输入要分析的日志文件名 (例如 jiojio_1950858520_20260313.txt): ").strip()
        
    analyze_bili_log(target_file)