import json
import sys
from datetime import datetime


def parse_and_sort_messages(json_data):
    """
    解析JSON消息数组，按时间排序并转换时间格式
    """
    # 解析JSON数据
    if isinstance(json_data, str):
        messages = json.loads(json_data)
    else:
        messages = json_data

    # 按add_time排序（转换为整数）
    sorted_messages = sorted(messages, key=lambda x: int(x['add_time']))

    # 转换时间戳并格式化输出
    formatted_messages = []
    for msg in sorted_messages:
        timestamp = int(msg['add_time'])
        dt = datetime.fromtimestamp(timestamp)
        formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')

        formatted_msg = msg.copy()
        formatted_msg['add_time_formatted'] = formatted_time
        formatted_messages.append(formatted_msg)

    return formatted_messages


def main():
    # 检查是否传入了参数
    if len(sys.argv) < 2:
        print("用法: python demo.py '<JSON数据>'")
        print("示例: python demo.py '[{\"message_type\":\"text\",\"sender\":\"STAFF\"}]'")
        sys.exit(1)

    # 获取命令行传入的JSON字符串
    json_str = sys.argv[1]

    try:
        result = parse_and_sort_messages(json_str)

        # 打印格式化结果
        print("=" * 70)
        for msg in result:
            print(f"{msg['add_time_formatted']} - {msg['sender']:10} | {msg['content']}")
        print("=" * 70)

        # 如需同时输出完整JSON，取消下面注释
        # print(json.dumps(result, ensure_ascii=False, indent=2))

    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        sys.exit(1)
    except KeyError as e:
        print(f"字段缺失错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()