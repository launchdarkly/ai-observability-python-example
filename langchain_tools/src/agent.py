import os
from typing import Dict, Any, Optional

from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.chains import LLMMathChain
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from ldclient import Context
from ldclient.config import Config
from ldai.client import LDAIClient, LDAIAgentConfig, LDAIAgentDefaults
import ldclient
from ldobserve import ObservabilityConfig, ObservabilityPlugin, observe

from opentelemetry.instrumentation.openai import OpenAIInstrumentor
from opentelemetry.instrumentation.langchain import LangchainInstrumentor

LangchainInstrumentor().instrument()
OpenAIInstrumentor().instrument()

class LangChainAgent:
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        launchdarkly_sdk_key: Optional[str] = None,
        ai_config_agent_key: str = "langchain-agent-config",
        context_key: str = "default-langchain-user",
    ):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required")

        # Initialize core components
        self.llm = ChatOpenAI(temperature=0, streaming=True, openai_api_key=self.openai_api_key)
        self.tools = [
            Tool(
                name="Search",
                func=DuckDuckGoSearchAPIWrapper().run,
                description="useful for when you need to answer questions about current events"
            ),
            Tool(
                name="Calculator",
                func=LLMMathChain.from_llm(self.llm).run,
                description="useful for when you need to answer questions about math"
            ),
        ]

        # Initialize LaunchDarkly if SDK key is provided
        self.ld_client = None
        self.ai_client = None
        self.context = None
        ld_sdk_key = launchdarkly_sdk_key or os.getenv("LAUNCHDARKLY_SDK_KEY")
        if ld_sdk_key:
            self._setup_launchdarkly(ld_sdk_key, context_key)
        
        self.ai_config_agent_key = ai_config_agent_key

    def _setup_launchdarkly(self, sdk_key: str, context_key: str):
        config = Config(
            sdk_key=sdk_key,
            plugins=[ObservabilityPlugin(ObservabilityConfig(
                service_name="langchain-agent-cli",
                service_version="0.1.0",
                environment="development"
            ))]
        )
        ldclient.set_config(config)
        self.ld_client = ldclient.get()
        self.ai_client = LDAIClient(self.ld_client)
        self.context = Context.builder(context_key).build()

    def run_agent(self, query: str) -> str:
        with observe.start_span("run_langchain_agent"):
            # Default prompt template
            prompt = PromptTemplate(
                template="""Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
{agent_scratchpad}""",
                input_variables=["input", "agent_scratchpad", "tools", "tool_names"]
            )

            # Get agent configuration from LaunchDarkly if available
            agent_llm = self.llm
            if self.ai_client and self.ld_client:
                agent_config = LDAIAgentConfig(
                    key=self.ai_config_agent_key,
                    default_value=LDAIAgentDefaults(
                        enabled=False,
                        instructions="You are a default assistant for {task}."
                    ),
                    variables={'task': 'general assistance'}
                )
                agent = self.ai_client.agent(agent_config, self.context)
                
                if agent.enabled and agent.model and agent.model.name:
                    agent_llm = ChatOpenAI(streaming=True, openai_api_key=self.openai_api_key, model_name=agent.model.name)
                    prompt = PromptTemplate(
                        template=f"""Answer the following questions as best you can, following these instructions:
{agent.instructions}

You have access to the following tools:

{{tools}}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{{tool_names}}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {{input}}
{{agent_scratchpad}}""",
                        input_variables=["input", "agent_scratchpad", "tools", "tool_names"]
                    )

            # Create and run the agent
            agent = create_react_agent(llm=agent_llm, tools=self.tools, prompt=prompt)
            agent_exec = AgentExecutor(agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True)
            return agent_exec.invoke({"input": query})["output"]

    def close(self):
        if self.ld_client:
            self.ld_client.close()