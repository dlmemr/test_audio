import os
import json
import csv
import requests
from urllib.parse import unquote

# 配置参数
DICT_JSON_DIR = r'D:\project\eng-ai-teacher\test_audio'
DICT_JSON_PATH = os.path.join(DICT_JSON_DIR, 'dict.json')  # 替换为你的dict.json路径
AUDIO_DIR = r'D:\project\eng-ai-teacher\test_audio\audio'
CSV_PATH = os.path.join(AUDIO_DIR, 'dict_audio_mapping.csv')
API_URL = 'http://ikuai.safepayer.cn:49966/tts'

# 创建音频目录（如果不存在）
os.makedirs(AUDIO_DIR, exist_ok=True)

def sanitize_filename(word):
    """生成安全文件名（小写+去特殊字符）"""
    return word.strip().lower().replace(' ', '_') + '.wav'

def extract_words(json_data):
    """从嵌套的JSON结构中提取所有唯一的单词"""
    words = set()
    
    def recurse(data):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "word":
                    clean_word = value.strip().lower()
                    words.add(clean_word)
                else:
                    recurse(value)
        elif isinstance(data, list):
            for item in data:
                recurse(item)
    
    recurse(json_data)
    return sorted(words)

def process_word(word, writer):
    """处理单个单词，返回处理结果状态"""
    filename = sanitize_filename(word)
    local_path = os.path.join(AUDIO_DIR, filename)
    
    # 检查文件是否已存在
    if os.path.exists(local_path):
        writer.writerow([word, 'already exist', '', filename])
        return 'exist'

    try:
        # 调用TTS API
        response = requests.post(API_URL, data={
            "text": word,
            "prompt": "[break_6]",
            "voice": "12.pt",
            "speed": 1,
            "temperature": 0.00001,
            "top_p": 0.501,
            "top_k": 12,
            "refine_max_new_token": 384,
            "infer_max_new_token": 2048,
            "text_seed": 42,
            "skip_refine": 1,
            "is_stream": 0,
            "custom_voice": 0
        }, timeout=60)

        res = response.json()
        
        # 处理API响应
        if res.get('code') == 0 and res.get('audio_files'):
            url = res['audio_files'][0]['url']
            
            # 下载音频文件
            audio_response = requests.get(url, timeout=30)
            with open(local_path, 'wb') as f:
                f.write(audio_response.content)
            
            # 记录成功
            writer.writerow([word, 'success', url, filename])
            return 'success'
        else:
            # 记录API错误
            error_msg = res.get('msg', 'unknown error')
            writer.writerow([word, 'failed', '', error_msg])
            return 'failed'
            
    except Exception as e:
        # 记录异常
        writer.writerow([word, 'error', '', str(e)])
        return 'error'

def main():
    # 步骤1：初始化CSV文件
    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='|')
        writer.writerow(['word', 'state', 'url', 'audio'])

    # 读取JSON数据
    with open(DICT_JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 提取所有唯一单词（已清洗为小写）
    words = extract_words(data)
    total = len(words)
    stats = {'success': 0, 'failed': 0, 'error': 0, 'exist': 0}

    # 处理每个单词
    with open(CSV_PATH, 'a', newline='', encoding='utf-8') as f:  # 追加模式
        writer = csv.writer(f, delimiter='|')
        
        for idx, word in enumerate(words, 1):
            print(f"Processing ({idx}/{total}): {word}")
            status = process_word(word, writer)
            stats[status] += 1

    # 输出统计结果
    print(f"\n处理完成！共 {total} 个单词")
    print(f"新增成功: {stats['success']}")
    print(f"已存在: {stats['exist']}")
    print(f"API失败: {stats['failed']}")
    print(f"异常错误: {stats['error']}")

if __name__ == '__main__':
    main()