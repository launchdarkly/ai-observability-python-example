"""OpenAI client with LaunchDarkly AI Config integration."""

import os
from typing import List, Dict, Optional
from dataclasses import dataclass

from openai import OpenAI
import ldclient
from ldclient import Context
from ldclient.config import Config
from ldai.client import LDAIClient, AIConfig
from ldobserve import ObservabilityConfig, ObservabilityPlugin, observe

from opentelemetry.instrumentation.openai import OpenAIInstrumentor

OpenAIInstrumentor().instrument()

@dataclass
class ChatMessage:
    role: str  # "system", "user", or "assistant"
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}

class OpenAIClient:
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model: str = "gpt-3.5-turbo",
        launchdarkly_sdk_key: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        self.conversation_history = [
            ChatMessage(
                role="system",
                content="You are a helpful assistant. Provide clear, concise responses."
            )
        ]
        
        # Initialize LaunchDarkly
        self.ld_sdk_key = launchdarkly_sdk_key or os.getenv("LAUNCHDARKLY_SDK_KEY")
        self.ld_client = None
        self.ai_client = None
        
        if self.ld_sdk_key:
            config = Config(
                sdk_key=self.ld_sdk_key,
                base_uri="https://ld-stg.launchdarkly.com",
                stream_uri="https://stream-stg.launchdarkly.com",
                events_uri="https://events-stg.launchdarkly.com",
                plugins=[ObservabilityPlugin(ObservabilityConfig(
                    service_name="ai-chat-cli",
                    service_version="0.1.0",
                    environment="development",
                    backend_url="https://pub.observability.ld-stg.launchdarkly.com",
                    otlp_endpoint="https://otel.observability.ld-stg.launchdarkly.com:4317"
                ))]
            )
            ldclient.set_config(config)
            self.ld_client = ldclient.get()
            self.ai_client = LDAIClient(self.ld_client)
    
    def add_message(self, role: str, content: str) -> None:
        self.conversation_history.append(ChatMessage(role=role, content=content))
        # Keep last 20 messages + system message
        if len(self.conversation_history) > 21:
            self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-20:]
    
    def get_response(self, user_message: str) -> str:
        with observe.start_span("get_openai_response"):
            self.add_message("user", user_message)
            messages = [msg.to_dict() for msg in self.conversation_history]
            
            try:
                if self.ai_client:
                    context = Context.builder('user-key').build()
                    config, tracker = self.ai_client.config(
                        "ai-observability-python-chat",
                        context,
                        AIConfig(enabled=True),
                        {}
                    )
                    
                    if config.enabled and config.messages:
                        messages = [message.to_dict() for message in config.messages]
                        messages.append({"role": "user", "content": user_message})
                        
                        if config.model and config.model.name:
                            self.model = config.model.name

                    response = tracker.track_openai_metrics(lambda: 
                        self.client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                        )
                    )
                else:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=1000,
                        temperature=0.7,
                    )
                
                assistant_message = response.choices[0].message.content
                self.add_message("assistant", assistant_message)
                return assistant_message
                
            except Exception as e:
                raise Exception(f"Failed to get response from OpenAI: {str(e)}")
    
    def clear_history(self) -> None:
        self.conversation_history = [self.conversation_history[0]]
    
    def get_conversation_length(self) -> int:
        return len(self.conversation_history) - 1
    
    def close(self) -> None:
        if self.ld_client:
            self.ld_client.close()