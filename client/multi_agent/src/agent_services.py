# services/agent_services.py
from typing import Dict, List, Optional, AsyncGenerator
import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard, 
    Message, 
    Part, 
    Role, 
    TextPart, 
    JSONRPCErrorResponse, 
    MessageSendConfiguration, 
    MessageSendParams, 
    SendStreamingMessageRequest, 
    TaskStatusUpdateEvent
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from src.config.load_key import load_key
from uuid import uuid4
import logging.config
import os

log_config_path = os.path.abspath("src/config/logging.conf")
logging.config.fileConfig(log_config_path, encoding='utf-8')
logger = logging.getLogger(__name__)

class AgentRegistry:
    """Agent注册和发现服务。

    提供注册和列出Agent的功能。
    """
    def __init__(self, http_client: httpx.AsyncClient):
        self.http_client = http_client
        self.agents: Dict[str, AgentCard] = {}
        self.clients: Dict[str, A2AClient] = {}

    async def register_agent(self, url: str) -> Optional[AgentCard]:
        """Register an agent by resolving its card.

        Args:
            url (str): The URL of the agent to register.

        Returns:
            Optional[AgentCard]: The registered AgentCard or None if registration fails.
        """
        try:
            resolver = A2ACardResolver(self.http_client, url)
            try:
                card = await resolver.get_agent_card()
            except Exception as e:
                logger.error(f"❌ Error retrieving agent card: {e}", exc_info=True)
                return None
            card.url = url

            # Create A2A client for this agent
            client = A2AClient(self.http_client, agent_card=card)

            self.agents[card.name] = card
            self.clients[card.name] = client

            logger.info(f"📋 Registered agent: {card.name}")
            logger.info(f"   Description: {card.description}")
            logger.info(f"   URL: {url}")

            return card

        except Exception as e:
            logger.error(f"❌ Failed to register agent at {url}: {e}", exc_info=True)
            return None

    def list_agents(self) -> List[Dict[str, str]]:
        """List all registered agents.

        Returns:
            List[Dict[str, str]]: List of dictionaries containing agent details.
        """
        return [
            {'name': card.name, 'description': card.description, 'url': card.url}
            for card in self.agents.values()
        ]

class AgentSelector:
    """Agent选择服务。

    使用LLM选择最合适的Agent来处理用户请求。
    """
    def __init__(self):
        # 初始化时仅创建LLM实例（可复用，配置固定）
        self.llm = ChatOpenAI(
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=load_key("DASHSCOPE_API_KEY"),
            model="qwen-plus",
        )
        self.parser = StrOutputParser()  # 输出解析器可复用

    async def select_agent(self, user_query: str, available_agents: List[Dict[str, str]]) -> Optional[str]:
        """Select the best agent for the user query using LLM.

        Args:
            user_query (str): The user's request.
            available_agents (List[Dict[str, str]]): List of available agents.

        Returns:
            Optional[str]: The name of the selected agent or None if no suitable agent is found.
        """
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
            logger.error(f"❌ Error selecting agent with LLM: {e}", exc_info=True)
            return None

class AgentQueryService:
    """统一查询处理服务。

    处理用户查询并将请求路由到适当的Agent。
    """
    def __init__(self, registry: AgentRegistry, selector: AgentSelector):
        self.registry = registry
        self.selector = selector

    # 流式处理方法
    async def handle_stream_query(self, user_input: str, session_id: str) -> AsyncGenerator[Dict, None]:
        """统一处理流式查询，返回异步生成器。

        Args:
            user_input (str): 用户的请求。
            session_id (str): 会话ID。

        Yields:
            Dict: 查询结果的字典。
        """
        try:
            # 1. 获取可用Agent列表
            available_agents = self.registry.list_agents()

            if not available_agents:
                logger.error("No agents available")
                yield {"type": "error", "text": "No agents available"}
                return

            # 2. 选择Agent
            selected_agent_name = await self.selector.select_agent(user_input, available_agents)
            if not selected_agent_name:
                logger.error("No suitable agent found")
                yield {"type": "error", "text": "No suitable agent found"}
                return

            # 3. 获取Agent客户端
            client = self.registry.clients.get(selected_agent_name)
            if not client:
                logger.error(f"Agent client not found: {selected_agent_name}")
                yield {"type": "error", "text": f"Agent client not found: {selected_agent_name}"}
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
            logger.error(f"❌ Error processing streaming response: {e}", exc_info=True)
            yield {"type": "error", "text": f"Error processing streaming response: {e}"}

    async def _process_streaming_response(self, client, payload) -> AsyncGenerator[Dict, None]:
        """处理流式响应。

        Args:
            client: Agent客户端。
            payload: 发送的消息负载。

        Yields:
            Dict: 处理后的响应字典。
        """
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
