# a2a_sample_v030
## 前提准备
- 本地安装Mysql(存储汽车信息)
- 本地安装Podman(容器化Redis，存储贷款方案)
- 本地安装MongoDB(存储测试用户征信信息)
- Python虚拟环境创建(如果需要的话，需要安装的模块包参见：requirements.txt)

## 数据准备
- MysqlDB，汽车信息表创建和数据初始化：chat_bot\remotes\auto_recommend\ddl.sql
- Redis，贷款方案RAG初始化，chat_bot\remotes\loan_suggest\rag_input.py
> 注意修改向量模型的API-Key
- MongoDB，预审测试用户征信信息初始化，chat_bot\remotes\loan_pre-examination\src\credit_info_service.py

## 设定修改
- chat_bot\remotes\auto_recommend\src\agent.py 修改自己的Mysql的用户名和密码
- 后端各个子文件夹下的config文件夹下放置Keys.json(设定DASHSCOPE_API_KEY的Json数据)


## 后端启动(python 命令启动)
- chat_bot\mcp_server\__main__.py
- chat_bot\remotes\auto_recommend\__main__.py
- chat_bot\remotes\loan_suggest\__main__.py
- chat_bot\remotes\loan_pre-examination\__main__.py
- chat_bot\hosts\__main__.py

## 测试用前端启动(npm install 后 npm run dev)
- chat_bot\Stream_Chat_Demo\frontend\stream-chat
