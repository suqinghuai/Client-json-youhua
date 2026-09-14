import json
import sys
import os
import glob
import re
from datetime import datetime

if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

RENDER_TYPE_MAP = {
    1: "text",
    3: "image",
    34: "voice",
    47: "emoji",
    50: "voip",
    10000: "system",
}

MESSAGE_TYPES_FILTER = [
    "chathistory", "emoji", "file", "image", "link",
    "quote", "redpacket", "system", "text", "transfer",
    "video", "voice", "voip",
]


def get_render_type(local_type, content):
    if local_type in RENDER_TYPE_MAP:
        return RENDER_TYPE_MAP[local_type]

    if content and isinstance(content, str):
        if content.startswith("[文件]"):
            return "file"
        if content.startswith("[转账]"):
            return "transfer"
        if content.startswith("[红包]"):
            return "redpacket"
        if content.startswith("[链接]"):
            return "link"

    return "chathistory"


def build_empty_message_fields():
    return {
        "title": "",
        "url": "",
        "from": "",
        "fromUsername": "",
        "linkType": "",
        "linkStyle": "",
        "objectId": "",
        "objectNonceId": "",
        "recordItem": "",
        "thumbUrl": "",
        "imageMd5": "",
        "imageFileId": "",
        "imageMd5Candidates": [],
        "imageFileIdCandidates": [],
        "imageUrl": "",
        "emojiMd5": "",
        "emojiUrl": "",
        "videoMd5": "",
        "videoThumbMd5": "",
        "videoFileId": "",
        "videoThumbFileId": "",
        "videoUrl": "",
        "videoThumbUrl": "",
        "voiceLength": "",
        "quoteUsername": "",
        "quoteServerId": "",
        "quoteType": "",
        "quoteThumbUrl": "",
        "quoteVoiceLength": "",
        "quoteTitle": "",
        "quoteContent": "",
        "amount": "",
        "coverUrl": "",
        "fileSize": "",
        "fileMd5": "",
        "paySubType": "",
        "transferStatus": "",
        "transferId": "",
        "voipType": "",
        "locationLat": None,
        "locationLng": None,
        "locationPoiname": "",
        "locationLabel": "",
    }


def convert_message(msg, idx, account_wxid, conversation_username, is_group):
    sender = msg.get("senderUsername", "")
    is_sent = (sender == account_wxid)

    local_type = msg.get("localType", 1)
    content = msg.get("content")
    render_type = get_render_type(local_type, content)

    create_time = msg.get("createTime", 0)
    formatted_time = msg.get("formattedTime", "")
    sort_seq = create_time * 1000 + idx

    server_id_str = msg.get("platformMessageId", "0")
    try:
        server_id = int(server_id_str)
    except (ValueError, TypeError):
        server_id = 0

    sender_display_name = msg.get("senderDisplayName", "")
    sender_avatar_path = f"media/avatars/{sender}.jpg" if sender else ""

    display_content = content
    if content is None:
        if render_type == "voice":
            display_content = "[语音]"
        elif render_type == "image":
            display_content = "[图片]"
        else:
            display_content = ""
    elif render_type == "emoji":
        display_content = "[表情]"

    converted = {
        "id": f"message_{idx + 1}",
        "localId": msg.get("localId", idx + 1),
        "serverId": server_id,
        "createTime": create_time,
        "createTimeText": formatted_time,
        "sortSeq": sort_seq,
        "type": local_type,
        "renderType": render_type,
        "isSent": is_sent,
        "senderUsername": sender,
        "conversationUsername": conversation_username,
        "isGroup": is_group,
        "content": display_content,
    }

    converted.update(build_empty_message_fields())

    if render_type == "emoji":
        converted["emojiMd5"] = msg.get("emojiMd5", "")
        converted["emojiUrl"] = msg.get("emojiCdnUrl", "")

    if render_type == "voice":
        converted["voiceLength"] = msg.get("voiceLength", "")

    if render_type == "voip":
        converted["voipType"] = "audio"

    if render_type == "transfer" and display_content:
        match = re.search(r'￥([\d.]+)', display_content)
        if match:
            converted["amount"] = match.group(1)

    if render_type == "image":
        converted["content"] = "[图片]"

    converted["senderDisplayName"] = sender_display_name
    converted["senderAvatarPath"] = sender_avatar_path

    return converted


def find_conversation_partner(messages, account_wxid):
    for msg in messages:
        sender = msg.get("senderUsername", "")
        if sender and sender != account_wxid:
            return sender, msg.get("senderDisplayName", "")
    return "", ""


def convert_weflow_to_exporter(source_data):
    session = source_data["session"]
    source_messages = source_data["messages"]

    account_wxid = session["wxid"]
    is_group = session.get("type") == "群聊"

    partner_wxid, partner_display_name = find_conversation_partner(
        source_messages, account_wxid
    )

    if not partner_display_name:
        partner_display_name = session.get("nickname", "")

    conversation_username = partner_wxid
    conversation_display_name = partner_display_name
    conversation_avatar_path = (
        f"media/avatars/{partner_wxid}.jpg" if partner_wxid else ""
    )

    converted_messages = []
    for idx, msg in enumerate(source_messages):
        converted_msg = convert_message(
            msg, idx, account_wxid, conversation_username, is_group
        )
        converted_messages.append(converted_msg)

    exported_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    result = {
        "schemaVersion": 1,
        "exportedAt": exported_at,
        "account": account_wxid,
        "conversation": {
            "username": conversation_username,
            "displayName": conversation_display_name,
            "avatarPath": conversation_avatar_path,
            "isGroup": is_group,
        },
        "filters": {
            "startTime": None,
            "endTime": None,
            "messageTypes": MESSAGE_TYPES_FILTER,
        },
        "messages": converted_messages,
    }

    return result


QQ_TYPE_TO_RENDER = {
    "type_1": "text",
    "type_2": "file",
    "type_3": "quote",
    "type_4": "link",
    "type_6": "image",
    "type_7": "link",
    "type_9": "video",
    "type_19": "video",
    "type_23": "image",
    "type_25": "voip",
    "type_33": "image",
    "type_34": "voice",
    "type_47": "emoji",
    "audio": "voice",
    "file": "file",
    "video": "video",
    "image": "image",
    "reply": "quote",
}


def detect_format(data):
    if "weflow" in data and "session" in data and "messages" in data:
        return "weflow"
    if "metadata" in data and "chatInfo" in data and "messages" in data:
        meta = data.get("metadata", {})
        name = meta.get("name", "")
        if "QQChatExporter" in name:
            return "qqchat"
    return None


def is_source_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        fmt = detect_format(data)
        if fmt:
            return fmt
        return None
    except (json.JSONDecodeError, UnicodeDecodeError, FileNotFoundError):
        return None


def get_qq_render_type(msg):
    msg_type = msg.get("type", "")
    elements = msg.get("content", {}).get("elements", [])
    resources = msg.get("content", {}).get("resources", [])
    is_system = msg.get("system", False)

    if is_system:
        return "system"

    for elem in elements:
        elem_type = elem.get("type", "")
        if elem_type == "image":
            return "image"
        if elem_type == "video":
            return "video"
        if elem_type == "audio":
            return "voice"
        if elem_type == "file":
            return "file"
        if elem_type == "reply":
            return "quote"
        if elem_type == "face":
            return "emoji"

    for res in resources:
        res_type = res.get("type", "")
        if res_type == "image":
            return "image"
        if res_type == "video":
            return "video"
        if res_type == "audio":
            return "voice"
        if res_type == "file":
            return "file"

    if msg_type in QQ_TYPE_TO_RENDER:
        return QQ_TYPE_TO_RENDER[msg_type]

    text = msg.get("content", {}).get("text", "")
    if "[图片:" in text:
        return "image"
    if "[视频:" in text:
        return "video"
    if "[语音]" in text:
        return "voice"
    if "[卡片消息:" in text:
        return "link"
    if "[文件:" in text:
        return "file"

    return "text"


def convert_qq_message(msg, idx, self_uid, conversation_uid, is_group):
    sender_info = msg.get("sender", {})
    sender_uid = sender_info.get("uid", "")
    is_sent = (sender_uid == self_uid)

    render_type = get_qq_render_type(msg)

    timestamp_ms = msg.get("timestamp", 0)
    create_time = timestamp_ms // 1000 if timestamp_ms > 0 else 0
    formatted_time = msg.get("time", "")
    sort_seq = timestamp_ms + idx

    server_id_str = msg.get("id", "0")
    try:
        server_id = int(server_id_str)
    except (ValueError, TypeError):
        server_id = 0

    seq_str = msg.get("seq", "0")
    try:
        local_id = int(seq_str)
    except (ValueError, TypeError):
        local_id = idx + 1

    sender_display_name = sender_info.get("nickname", "") or sender_info.get("name", "")
    sender_avatar_path = f"media/avatars/{sender_uid}.jpg" if sender_uid else ""

    text_content = msg.get("content", {}).get("text", "")
    elements = msg.get("content", {}).get("elements", [])

    display_content = text_content
    if render_type == "image":
        display_content = "[图片]"
    elif render_type == "video":
        display_content = "[视频]"
    elif render_type == "voice":
        display_content = "[语音]"
    elif render_type == "emoji":
        face_name = ""
        for elem in elements:
            if elem.get("type") == "face":
                face_name = elem.get("data", {}).get("name", "")
                break
        display_content = f"[表情: {face_name}]" if face_name else "[表情]"
    elif render_type == "file":
        display_content = text_content if text_content else "[文件]"
    elif render_type == "system":
        display_content = text_content

    converted = {
        "id": f"message_{idx + 1}",
        "localId": local_id,
        "serverId": server_id,
        "createTime": create_time,
        "createTimeText": formatted_time,
        "sortSeq": sort_seq,
        "type": 1,
        "renderType": render_type,
        "isSent": is_sent,
        "senderUsername": sender_uid,
        "conversationUsername": conversation_uid,
        "isGroup": is_group,
        "content": display_content,
    }

    converted.update(build_empty_message_fields())

    if render_type == "image":
        for elem in elements:
            if elem.get("type") == "image":
                img_data = elem.get("data", {})
                converted["imageUrl"] = img_data.get("url", "")
                converted["imageMd5"] = img_data.get("md5", "")
                converted["thumbUrl"] = img_data.get("url", "")
                break

    if render_type == "video":
        for elem in elements:
            if elem.get("type") == "video":
                vid_data = elem.get("data", {})
                converted["videoUrl"] = vid_data.get("url", "")
                converted["videoMd5"] = vid_data.get("md5", "")
                break
        for res in msg.get("content", {}).get("resources", []):
            if res.get("type") == "video":
                if not converted["videoUrl"]:
                    converted["videoUrl"] = res.get("url", "")
                break

    if render_type == "voice":
        for elem in elements:
            if elem.get("type") == "audio":
                audio_data = elem.get("data", {})
                converted["voiceLength"] = str(audio_data.get("duration", ""))
                break

    if render_type == "file":
        for elem in elements:
            if elem.get("type") == "file":
                file_data = elem.get("data", {})
                converted["fileSize"] = str(file_data.get("size", ""))
                converted["fileMd5"] = file_data.get("md5", "")
                break

    if render_type == "quote":
        for elem in elements:
            if elem.get("type") == "reply":
                reply_data = elem.get("data", {})
                converted["quoteServerId"] = reply_data.get("messageId", "")
                break

    if render_type == "link":
        converted["content"] = text_content

    converted["senderDisplayName"] = sender_display_name
    converted["senderAvatarPath"] = sender_avatar_path

    return converted


def convert_qqchat_to_exporter(source_data):
    chat_info = source_data["chatInfo"]
    source_messages = source_data["messages"]

    self_uid = chat_info.get("selfUid", "")
    self_name = chat_info.get("selfName", "")
    chat_name = chat_info.get("name", "")
    chat_type = chat_info.get("type", "private")
    is_group = chat_type == "group"

    if is_group:
        conversation_uid = chat_info.get("groupUid", "")
    else:
        senders = source_data.get("statistics", {}).get("senders", [])
        conversation_uid = ""
        for s in senders:
            if s.get("uid", "") != self_uid:
                conversation_uid = s.get("uid", "")
                break
        if not conversation_uid:
            for msg in source_messages:
                uid = msg.get("sender", {}).get("uid", "")
                if uid and uid != self_uid:
                    conversation_uid = uid
                    break

    conversation_display_name = chat_name
    conversation_avatar_path = f"media/avatars/{conversation_uid}.jpg" if conversation_uid else ""

    converted_messages = []
    for idx, msg in enumerate(source_messages):
        converted_msg = convert_qq_message(
            msg, idx, self_uid, conversation_uid, is_group
        )
        converted_messages.append(converted_msg)

    exported_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    result = {
        "schemaVersion": 1,
        "exportedAt": exported_at,
        "account": self_uid,
        "conversation": {
            "username": conversation_uid,
            "displayName": conversation_display_name,
            "avatarPath": conversation_avatar_path,
            "isGroup": is_group,
        },
        "filters": {
            "startTime": None,
            "endTime": None,
            "messageTypes": MESSAGE_TYPES_FILTER,
        },
        "messages": converted_messages,
    }

    return result


def process_directory(directory):
    specific_patterns = ["私聊_*.json", "群聊_*.json", "friend_*.json", "group_*.json"]
    source_files = []

    seen = set()
    for pattern in specific_patterns:
        for filepath in glob.glob(os.path.join(directory, pattern)):
            if filepath in seen:
                continue
            seen.add(filepath)
            fmt = is_source_file(filepath)
            if fmt:
                source_files.append((filepath, fmt))

    if not source_files:
        for filepath in glob.glob(os.path.join(directory, "*.json")):
            if filepath in seen:
                continue
            seen.add(filepath)
            fmt = is_source_file(filepath)
            if fmt:
                source_files.append((filepath, fmt))

    if not source_files:
        print(f"在目录 {directory} 中未找到可识别的聊天记录文件")
        return False

    print(f"找到 {len(source_files)} 个聊天记录文件")

    for filepath, fmt in source_files:
        basename = os.path.basename(filepath)
        name_without_ext = os.path.splitext(basename)[0]
        fmt_label = "WeFlow" if fmt == "weflow" else "QQChatExporter"
        print(f"\n处理: {basename} (格式: {fmt_label})")

        with open(filepath, "r", encoding="utf-8") as f:
            source_data = json.load(f)

        if fmt == "weflow":
            result = convert_weflow_to_exporter(source_data)
        elif fmt == "qqchat":
            result = convert_qqchat_to_exporter(source_data)
        else:
            print(f"  跳过: 未知格式")
            continue

        if len(source_files) == 1:
            output_path = os.path.join(directory, "messages.json")
        else:
            output_dir = os.path.join(directory, name_without_ext)
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, "messages.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"输出: {output_path}")
        print(f"消息数: {len(result['messages'])}")

    return True


def main():
    if len(sys.argv) > 1:
        directory = os.path.abspath(sys.argv[1])
    else:
        directory = APP_DIR

    if not os.path.isdir(directory):
        print(f"错误: {directory} 不是有效目录")
        input("按任意键退出...")
        sys.exit(1)

    print(f"工作目录: {directory}")
    process_directory(directory)
    input("按任意键退出...")


if __name__ == "__main__":
    main()