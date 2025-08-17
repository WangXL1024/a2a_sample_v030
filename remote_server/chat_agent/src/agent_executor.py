from src.agent import ChatAgent
from a2a.server.agent_execution import AgentExecutor
import os
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.utils import new_agent_text_message, new_task
from a2a.types import TaskState, Part, TextPart
import asyncio
import os
import logging.config

log_config_path = os.path.abspath("src/config/logging.conf")
logging.config.fileConfig(log_config_path,encoding='utf-8')
logger = logging.getLogger(__name__)

class ChatAgentExecutor(AgentExecutor):
    def __init__(self) -> None:
        logger.info("Initializing Agent Executor")
        self.agent = ChatAgent()
        asyncio.run(self.agent.initialize())
        logger.info("Agent Executor initialize completed.")

    # 必须实现execute和cancel方法
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.info("Starting execute method")
        
        session_id = context._params.metadata["session_id"]# 从metadata中获取session_id(交互窗口唯一标识)
        user_input = context.get_user_input()# 获取用户输入

        # 找到当前任务
        task = context.current_task
        if not task:
            logger.info("No current task found, creating a new one")
            task = new_task(context.message)
            context.current_task = task
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        try:
            # 解析了A2A Client发来的请求，就可以让Server智能体干活了，按照正常逻辑进行调用，需要注意执行过程和结束都需要跟Client保持通信，要不断更新当前任务的状态
            async for chunk in self.agent.stream(messages=user_input, session_id=session_id):
                is_final_answer = chunk.get("is_final_answer")
                content = chunk.get("content")
                if not is_final_answer:
                    logger.info(f"Updating task status to working with content: {content}")
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            content,
                            task.context_id,
                            task.id,
                        ),
                    )
                else:
                    # 任务完成了，加一个工件artifact
                    await updater.add_artifact(
                        parts=[Part(root=TextPart(text=content))],
                        name="coding_result",
                        last_chunk=True,
                    )
                    logger.info("Task completed successfully")
                    await updater.complete()
                    break

        except Exception as e:
            logger.error(f"Exception occurred while processing task with session_id={session_id}: {str(e)}", exc_info=True)
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    str(e),
                    task.context_id,
                    task.id,
                ),
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.warning("Cancel method called, but not supported")
        raise Exception("cancel not supported")
