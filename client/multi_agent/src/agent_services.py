# services/agent_services.py
from typing import Dict, List, Optional
import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import AgentCard, Message, Part, Role, TextPart
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from src.config.load_key import load_key
from typing import Dict, List, Optional
from uuid import uuid4
from a2a.types import (
    AgentCard,
    JSONRPCErrorResponse,
    Message,
    MessageSendConfiguration,
    MessageSendParams,
    Part,
    SendStreamingMessageRequest,
    TaskStatusUpdateEvent,
    TextPart,
    Role
)
from typing import AsyncGenerator


class AgentRegistry:
    """Agent注册和发现服务"""
    def __init__(self, http_client: httpx.AsyncClient):
        self.http_client = http_client
        self.agents: Dict[str, AgentCard] = {}
        self.clients: Dict[str, A2AClient] = {}
    
    async def register_agent(self, url: str) -> Optional[AgentCard]:
        # 实现注册逻辑
        """Register an agent by resolving its card"""
        try:
            resolver = A2ACardResolver(self.http_client, url)
            card = await resolver.get_agent_card()
            card.url = url

            # Create A2A client for this agent
            client = A2AClient(self.http_client, agent_card=card)

            self.agents[card.name] = card
            self.clients[card.name] = client

            print(f"📋 Registered agent: {card.name}")
            print(f"   Description: {card.description}")
            print(f"   URL: {url}")

            return card

        except Exception as e:
            print(f"❌ Failed to register agent at {url}: {e}")
            return None
    
    def list_agents(self) -> List[Dict[str, str]]:
        return [
            {'name': card.name, 'description': card.description, 'url': card.url}
            for card in self.agents.values()
        ]

class AgentSelector:
    """Agent选择服务"""
    def __init__(self):
        # 初始化时仅创建LLM实例（可复用，配置固定）
        self.llm = ChatOpenAI(
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=load_key("DASHSCOPE_API_KEY"),
            model="qwen-plus",
        )
        self.parser = StrOutputParser()  # 输出解析器可复用
    
    async def select_agent(self, user_query: str, available_agents: List[Dict[str, str]]) -> Optional[str]:
        # 实现LLM选择逻辑
        """Select the best agent for the user query using LLM"""

        # Build prompt for agent selection
        agent_list = "\n".join([
            f"- {agent['name']}: {agent['description']}"
            for agent in available_agents
        ])

        prompt = f"""Choose the best agent for this task.
            Available agents:
            {agent_list}
            User request: "{user_query}"

            Rules:
            1. For coding → Coding Agent
            2. For automobile recommendation → Automobile Recommendation Agent
            3. For loan scheme suggestion → Loan Scheme Suggestion Agent           
            4. For loan pre-examination → Loan Pre-examination Agent
            5. For other chat → Chat Agent

            Respond with ONLY the agent name exactly as listed above. No explanations."""

        try:
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", prompt),
                ("user", "{text}")
            ])

            chain = prompt_template | self.llm | self.parser 
            selected_agent_name = chain.invoke({"text": user_query})
            return selected_agent_name.strip()

        except Exception as e:
            print(f"❌ Error selecting agent with LLM: {e}")
            return None

class AgentQueryService:
    """统一查询处理服务"""
    def __init__(self, registry: AgentRegistry, selector: AgentSelector):
        self.registry = registry
        self.selector = selector

#流式处理方法
    async def handle_stream_query(self, user_input: str,session_id: str) -> AsyncGenerator[Dict, None]:
        """统一处理流式查询，返回异步生成器"""
        try:
            # 1. 获取可用Agent列表
            available_agents = self.registry.list_agents()

            if not available_agents:
                yield {"type": "error", "message": "No agents available"}
                return

            # 2. 选择Agent
            selected_agent_name = await self.selector.select_agent(user_input, available_agents)
            if not selected_agent_name:
                yield {"type": "error", "message": "No suitable agent found"}
                return

            # 3. 获取Agent客户端
            client = self.registry.clients.get(selected_agent_name)
            if not client:
                yield {"type": "error", "message": f"Agent client not found: {selected_agent_name}"}
                return

            # 4. 构建消息
            message = Message(
                role=Role.user,
                parts=[Part(root=TextPart(text=user_input))],
                messageId=str(uuid4()),
            )
            payload = MessageSendParams(
                id=str(uuid4()),
                message=message,
                configuration=MessageSendConfiguration(
                    acceptedOutputModes=['text', 'text/plain'],
                ),
                metadata={"session_id": session_id}
            )
            # 5. 流式处理响应(流式传输需要每一层（Remote → Host → Client）都支持逐字/分片处理,代码需要修改)
            async for chunk in self._process_streaming_response(client, payload):
                yield chunk

        except Exception as e:
            yield {"type": "error", "message": str(e)}

    async def _process_streaming_response(self, client, payload) -> AsyncGenerator[Dict, None]:
        async for chunk in client.send_message_streaming(SendStreamingMessageRequest(id=str(uuid4()), params=payload)):
            if isinstance(chunk.root, JSONRPCErrorResponse):
                yield {"type": "error", "text": f"Agent error: {chunk.root.error}"}
                continue
            result = chunk.root.result
            if not result:
                yield {"type": "warning", "text": "Empty response from agent"}
                continue
            # 处理最终状态
            if isinstance(result, TaskStatusUpdateEvent):
                if result.final:
                    yield {"type": "complete", "text": "Agent task completed"}
                else:
                    # 确保parts和text存在，避免AttributeError
                    if result.status.message and result.status.message.parts:
                        text = result.status.message.parts[0].root.text
                        yield {"type": "status", "text": text}
                    else:
                        yield {"type": "status", "text": "Agent is processing..."}
            else:
                yield {"type": "unknown", "text": f"Received unknown event: {type(result)}"}



