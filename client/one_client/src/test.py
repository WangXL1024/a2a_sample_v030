import json
import re

def extract_agent_content(stream_data):
    """
    从流式输出中提取role为agent的内容
    
    参数:
        stream_data: 原始的流式输出字符串
    返回:
        拼接后的agent内容字符串
    """
    # 1. 拆分多个JSON对象（处理流式输出中JSON拼接的情况）
    # 使用正则表达式匹配JSON对象的边界
    json_strings = re.findall(r'\{.*?\}', stream_data, re.DOTALL)
    
    agent_content = ""
    
    # 2. 遍历每个JSON对象进行解析和筛选
    for json_str in json_strings:
        try:
            # 解析JSON字符串为字典
            data = json.loads(json_str)
            
            # 3. 定位到可能包含role的字段路径
            # 检查result -> status -> message 路径
            result = data.get("result", {})
            status = result.get("status", {})
            message = status.get("message", {})
            
            # 4. 判断是否为agent角色的内容
            if message.get("role") == "agent":
                # 提取parts中的文本内容（取第一个part的text）
                parts = message.get("parts", [])
                if parts and isinstance(parts[0], dict):
                    text = parts[0].get("text", "")
                    agent_content += text
                    
        except json.JSONDecodeError:
            # 忽略解析失败的JSON（可能是不完整的片段）
            continue
        except Exception as e:
            print(f"处理JSON时出错: {e}")
            continue
    
    return agent_content

# 示例用法
if __name__ == "__main__":
    # 原始流式输出数据（替换为实际的流式输出字符串）
    stream_data = '''{"id":"391331e3-df54-418b-bd54-9bbe12e8253f","jsonrpc":"2.0","result":{"artifacts":null,"contextId":"e7e249fa-8b67-4793-974d-963be0d83a79","history":[{"contextId":"e7e249fa-8b67-4793-974d-963be0d83a79","extensions":null,"kind":"message","messageId":"90c3fad321cb4b38b404fe8235d732b9","metadata":null,"parts":[{"kind":"text","metadata":null,"text":"写个Java Hello World"}],"referenceTaskIds":null,"role":"user","taskId":"4f907d5c-2df5-4ca4-9075-f0d7bdce3994"}],"id":"4f907d5c-2df5-4ca4-9075-f0d7bdce3994","kind":"task","metadata":null,"status":{"message":null,"state":"submitted","timestamp":null}}}{"id":"391331e3-df54-418b-bd54-9bbe12e8253f","jsonrpc":"2.0","result":{"contextId":"e7e249fa-8b67-4793-974d-963be0d83a79","final":false,"kind":"status-update","metadata":null,"status":{"message":{"contextId":"e7e249fa-8b67-4793-974d-963be0d83a79","extensions":null,"kind":"message","messageId":"c1cf0f03-5792-4595-b7a8-4d6dce049f43","metadata":null,"parts":[{"kind":"text","metadata":null,"text":"```"}],"referenceTaskIds":null,"role":"agent","taskId":"4f907d5c-2df5-4ca4-9075-f0d7bdce3994"},"state":"working","timestamp":"2025-08-14T06:30:49.860908+00:00"},"taskId":"4f907d5c-2df5-4ca4-9075-f0d7bdce3994"}}{"id":"391331e3-df54-418b-bd54-9bbe12e8253f","jsonrpc":"2.0","result":{"contextId":"e7e249fa-8b67-4793-974d-963be0d83a79","final":false,"kind":"status-update","metadata":null,"status":{"message":{"contextId":"e7e249fa-8b67-4793-974d-963be0d83a79","extensions":null,"kind":"message","messageId":"8b9527c3-d1da-429b-a7f7-6a7ee3e9900c","metadata":null,"parts":[{"kind":"text","metadata":null,"text":"java\npublic"}],"referenceTaskIds":null,"role":"agent","taskId":"4f907d5c-2df5-4ca4-9075-f0d7bdce3994"},"state":"working","timestamp":"2025-08-14T06:30:49.911770+00:00"},"taskId":"4f907d5c-2df5-4ca4-9075-f0d7bdce3994"}}{"id":"391331e3-df54-418b-bd54-9bbe12e8253f","jsonrpc":"2.0","result":{"contextId":"e7e249fa-8b67-4793-974d-963be0d83a79","final":false,"kind":"status-update","metadata":null,"status":{"message":{"contextId":"e7e249fa-8b67-4793-974d-963be0d83a79","extensions":null,"kind":"message","messageId":"bcdae15c-a7bb-45c8-a191-7e0217503445","metadata":null,"parts":[{"kind":"text","metadata":null,"text":" class HelloWorld {\n"}],"referenceTaskIds":null,"role":"agent","taskId":"4f907d5c-2df5-4ca4-9075-f0d7bdce3994"},"state":"working","timestamp":"2025-08-14T06:30:49.953125+00:00"},"taskId":"4f907d5c-2df5-4ca4-9075-f0d7bdce3994"}}{"id":"391331e3-df54-418b-bd54-9bbe12e8253f","jsonrpc":"2.0","result":{"contextId":"e7e249fa-8b67-4793-974d-963be0d83a79","final":false,"kind":"status-update","metadata":null,"status":{"message":{"contextId":"e7e249fa-8b67-4793-974d-963be0d83a79","extensions":null,"kind":"message","messageId":"532125d7-5490-4b55-81a8-813377652fda","metadata":null,"parts":[{"kind":"text","metadata":null,"text":"    public static"}],"referenceTaskIds":null,"role":"agent","taskId":"4f907d5c-2df5-4ca4-9075-f0d7bdce3994"},"state":"working","timestamp":"2025-08-14T06:30:50.026482+00:00"},"taskId":"4f907d5c-2df5-4ca4-9075-f0d7bdce3994"}}{"id":"391331e3-df54-418b-bd54-9bbe12e8253f","jsonrpc":"2.0","result":{"contextId":"e7e249fa-8b67-4793-974d-963be0d83a79","final":false,"kind":"status-update","metadata":null,"status":{"message":{"contextId":"e7e249fa-8b67-4793-974d-963be0d83a79","extensions":null,"kind":"message","messageId":"e57dd9b0-e4d7-4c96-a0a7-a84b653474b2","metadata":null,"parts":[{"kind":"text","metadata":null,"text":" void main(String[] args)"}],"referenceTaskIds":null,"role":"agent","taskId":"4f907d5c-2df5-4ca4-9075-f0d7bdce3994"},"state":"working","timestamp":"2025-08-14T06:30:50.109379+00:00"},"taskId":"4f907d5c-2df5-4ca4-9075-f0d7bdce3994"}}{"id":"391331e3-df54-418b-bd54-9bbe12e8253f","jsonrpc":"2.0","result":{"contextId":"e7e249fa-8b67-4793-974d-963be0d83a79","final":false,"kind":"status-update","metadata":null,"status":{"message":{"contextId":"e7e249fa-8b67-4793-974d-963be0d83a79","extensions":null,"kind":"message","messageId":"2feff4b6-f6fb-430d-b443-39af731c0868","metadata":null,"parts":[{"kind":"text","metadata":null,"text":" {\n        System.out.println(\""}],"referenceTaskIds":null,"role":"agent","taskId":"4f907d5c-2df5-4ca4-9075-f0d7bdce3994"},"state":"working","timestamp":"2025-08-14T06:30:50.525477+00:00"},"taskId":"4f907d5c-2df5-4ca4-9075-f0d7bdce3994"}}{"id":"391331e3-df54-418b-bd54-9bbe12e8253f","jsonrpc":"2.0","result":{"contextId":"e7e249fa-8b67-4793-974d-963be0d83a79","final":false,"kind":"status-update","metadata":null,"status":{"message":{"contextId":"e7e249fa-8b67-4793-974d-963be0d83a79","extensions":null,"kind":"message","messageId":"a3b87191-81a6-4cc8-9183-ebddc0a086b7","metadata":null,"parts":[{"kind":"text","metadata":null,"text":"Hello, World!\");\n    }\n"}],"referenceTaskIds":null,"role":"agent","taskId":"4f907d5c-2df5-4ca4-9075-f0d7bdce3994"},"state":"working","timestamp":"2025-08-14T06:30:50.547658+00:00"},"taskId":"4f907d5c-2df5-4ca4-9075-f0d7bdce3994"}}{"id":"391331e3-df54-418b-bd54-9bbe12e8253f","jsonrpc":"2.0","result":{"contextId":"e7e249fa-8b67-4793-974d-963be0d83a79","final":false,"kind":"status-update","metadata":null,"status":{"message":{"contextId":"e7e249fa-8b67-4793-974d-963be0d83a79","extensions":null,"kind":"message","messageId":"9431a20a-f344-4562-8db0-9709799a5074","metadata":null,"parts":[{"kind":"text","metadata":null,"text":"}\n```"}],"referenceTaskIds":null,"role":"agent","taskId":"4f907d5c-2df5-4ca4-9075-f0d7bdce3994"},"state":"working","timestamp":"2025-08-14T06:30:50.566785+00:00"},"taskId":"4f907d5c-2df5-4ca4-9075-f0d7bdce3994"}}{"id":"391331e3-df54-418b-bd54-9bbe12e8253f","jsonrpc":"2.0","result":{"contextId":"e7e249fa-8b67-4793-974d-963be0d83a79","final":false,"kind":"status-update","metadata":null,"status":{"message":{"contextId":"e7e249fa-8b67-4793-974d-963be0d83a79","extensions":null,"kind":"message","messageId":"be300bc1-fd8f-4557-b383-2a29d4791ed2","metadata":null,"parts":[{"kind":"text","metadata":null,"text":""}],"referenceTaskIds":null,"role":"agent","taskId":"4f907d5c-2df5-4ca4-9075-f0d7bdce3994"},"state":"working","timestamp":"2025-08-14T06:30:50.570303+00:00"},"taskId":"4f907d5c-2df5-4ca4-9075-f0d7bdce3994"}}{"id":"391331e3-df54-418b-bd54-9bbe12e8253f","jsonrpc":"2.0","result":{"append":null,"artifact":{"artifactId":"d043e142-bf08-47c1-a7b7-cba4a5efb6f3","description":null,"extensions":null,"metadata":null,"name":"coding_result","parts":[{"kind":"text","metadata":null,"text":""}]},"contextId":"e7e249fa-8b67-4793-974d-963be0d83a79","kind":"artifact-update","lastChunk":true,"metadata":null,"taskId":"4f907d5c-2df5-4ca4-9075-f0d7bdce3994"}}{"id":"391331e3-df54-418b-bd54-9bbe12e8253f","jsonrpc":"2.0","result":{"contextId":"e7e249fa-8b67-4793-974d-963be0d83a79","final":true,"kind":"status-update","metadata":null,"status":{"message":null,"state":"completed","timestamp":"2025-08-14T06:30:53.375936+00:00"},"taskId":"4f907d5c-2df5-4ca4-9075-f0d7bdce3994"}}'''
    
    # 提取agent内容
    agent_content = extract_agent_content(stream_data)
    
    # 打印结果（实际应用中可返回给前端）
    print("提取的agent内容：")
    print(agent_content)