import os
import json
import csv
import requests

# 配置参数
DICT_JSON_DIR = r'D:\project\eng-ai-teacher\test_audio'
DICT_JSON_PATH = os.path.join(DICT_JSON_DIR, 'dict.json')  # 替换为你的dict.json路径
AUDIO_DIR = r'D:\project\eng-ai-teacher\test_audio\audio'
CSV_PATH = os.path.join(AUDIO_DIR, 'dict_audio_mapping.csv')
API_URL = 'http://ikuai.safepayer.cn:49966/tts'

# 创建音频目录（如果不存在）
os.makedirs(AUDIO_DIR, exist_ok=True)

def extract_words(json_data):
    """从嵌套的JSON结构中提取所有唯一的单词"""
    words = set()
    
    def recurse(data):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "word":
                    words.add(value.strip().lower())
                else:
                    recurse(value)
        elif isinstance(data, list):
            for item in data:
                recurse(item)
    
    recurse(json_data)
    return sorted(words)

def process_word(word, writer):
    """处理单个单词的API调用和文件保存"""
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
        print("word: ",word, "res: " ,res)
        
        # 处理响应
        if res.get('code') == 0 and res.get('audio_files'):
            url = res['audio_files'][0]['url']
            filename = f"{word}.wav"
            local_path = os.path.join(AUDIO_DIR, filename)
            
            # 下载音频文件
            audio_response = requests.get(url, timeout=60)
            with open(local_path, 'wb') as f:
                f.write(audio_response.content)
            
            # 记录成功
            writer.writerow([word, 'success', url, filename])
            return True
        else:
            # 记录API错误
            print("res get error!")
            writer.writerow([word, 'failed', '', ''])
            return False
            
    except Exception as e:
        # 记录异常
        print("response error!",str(e))
        writer.writerow([word, 'error', '', str(e)])
        return False

def main():
    # 步骤1：初始化CSV文件
    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='|')
        writer.writerow(['word', 'state', 'url', 'audio'])

    try:
        with open(DICT_JSON_PATH, 'r', encoding='utf-8') as f:
            content = f.read().lstrip('\ufeff')
            data = json.loads(content)
            #print(data)    
            # 提取所有唯一单词（已转为小写）
            words = extract_words(data)
            total = len(words)

    
            success = 0
            failed = 0

            # 处理每个单词
            with open(CSV_PATH, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter='|')

                for idx, word in enumerate(words, 1):
                    print(f"Processing ({idx}/{total}): {word}")
                    if process_word(word, writer):
                        success += 1
                    else:
                        failed += 1

            # 输出统计结果
            print(f"\n处理完成！共 {total} 个单词")
            print(f"成功生成: {success} 个")
            print(f"失败: {failed} 个")
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {e}")  

if __name__ == '__main__':
    main()