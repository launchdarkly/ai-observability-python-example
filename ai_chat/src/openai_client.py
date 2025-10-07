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
            print("🚀 Initializing LaunchDarkly with observability plugin...")

            # Use environment variables for O11y config
            backend_url = os.getenv("LD_BACKEND_URL")
            otlp_endpoint = os.getenv("LD_OTLP_ENDPOINT")

            if not backend_url:
                print("❌ Error: LD_BACKEND_URL environment variable is required but not found")
                raise ValueError("LD_BACKEND_URL environment variable is required")
            if not otlp_endpoint:
                print("❌ Error: LD_OTLP_ENDPOINT environment variable is required but not found")
                raise ValueError("LD_OTLP_ENDPOINT environment variable is required")

            # Configure observability plugin according to official docs
            observability_config = ObservabilityConfig(
                service_name="ai-chat-cli",
                service_version="0.1.0",
                environment="staging",
                backend_url=backend_url,
                otlp_endpoint=otlp_endpoint
            )
            plugin = ObservabilityPlugin(observability_config)
            
            # Use environment variables for LaunchDarkly endpoints
            base_uri = os.getenv("LD_BASE_URI")
            stream_uri = os.getenv("LD_STREAM_URI")
            events_uri = os.getenv("LD_EVENTS_URI")
            
            if not base_uri:
                print("❌ Error: LD_BASE_URI environment variable is required but not found")
                raise ValueError("LD_BASE_URI environment variable is required")
            if not stream_uri:
                print("❌ Error: LD_STREAM_URI environment variable is required but not found")
                raise ValueError("LD_STREAM_URI environment variable is required")
            if not events_uri:
                print("❌ Error: LD_EVENTS_URI environment variable is required but not found")
                raise ValueError("LD_EVENTS_URI environment variable is required")
            
            config = Config(
                sdk_key=self.ld_sdk_key,
                base_uri=base_uri,
                stream_uri=stream_uri,
                events_uri=events_uri,
                plugins=[plugin]
            )
            ldclient.set_config(config)
            self.ld_client = ldclient.get()
            self.ai_client = LDAIClient(self.ld_client)
            print("✅ LaunchDarkly initialized successfully")
        else:
            print("⚠️  No LaunchDarkly SDK key provided - observability disabled")
    
    def add_message(self, role: str, content: str) -> None:
        self.conversation_history.append(ChatMessage(role=role, content=content))
        # Keep last 20 messages + system message
        if len(self.conversation_history) > 21:
            self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-20:]
    
    def get_response(self, user_message: str) -> str:
        with observe.start_span("get_openai_response") as span:
            print(f"🔍 LaunchDarkly span created: {span}")
            print(f"🔍 Span context: {span.get_span_context()}")
            self.add_message("user", user_message)
            messages = [msg.to_dict() for msg in self.conversation_history]
            
            try:
                if self.ai_client:
                    print("🔍 Using LaunchDarkly AI client for tracing...")
                    context = Context.builder('user-key').build()
                    
                    # Get AI config key from environment variable
                    ai_config_key = os.getenv("AI_CONFIG_KEY")
                    if not ai_config_key:
                        raise ValueError("AI_CONFIG_KEY environment variable is required")
                    
                    config, tracker = self.ai_client.config(
                        ai_config_key,
                        context,
                        AIConfig(enabled=True),
                        {}
                    )
                    print(f"🔍 AI Config enabled: {config.enabled}")
                    print(f"🔍 AI Config messages: {len(config.messages) if config.messages else 0}")
                    print(f"🔍 Tracker object: {tracker}")
                    print(f"🔍 Tracker type: {type(tracker)}")
                    
                    if config.enabled and config.messages:
                        messages = [message.to_dict() for message in config.messages]
                        messages.append({"role": "user", "content": user_message})
                        
                        if config.model and config.model.name:
                            self.model = config.model.name

                    print(f"🔍 Tracking OpenAI call with model: {self.model}")
                    print(f"🔍 Messages being sent: {len(messages)}")
                    
                    response = tracker.track_openai_metrics(lambda: 
                        self.client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                        )
                    )
                    
                    print(f"🔍 OpenAI response received - tokens used: {response.usage.total_tokens if response.usage else 'unknown'}")
                    
                    # Try to get trace information from the tracker
                    if hasattr(tracker, 'get_trace_id'):
                        print(f"🔍 LaunchDarkly trace ID: {tracker.get_trace_id()}")
                    if hasattr(tracker, 'trace_id'):
                        print(f"🔍 LaunchDarkly trace ID (attr): {tracker.trace_id}")
                    if hasattr(tracker, '_trace_id'):
                        print(f"🔍 LaunchDarkly trace ID (private): {tracker._trace_id}")
                    
                    print(f"🔍 Tracker attributes: {dir(tracker)}")
                    
                    # Try to get the summary which might contain trace info
                    try:
                        summary = tracker.get_summary()
                        print(f"🔍 Tracker summary: {summary}")
                        if hasattr(summary, '__dict__'):
                            print(f"🔍 Summary attributes: {summary.__dict__}")
                    except Exception as e:
                        print(f"🔍 Could not get tracker summary: {e}")
                    
                    # Check if there's a trace ID in the tracker's internal data
                    try:
                        track_data = tracker._LDAIConfigTracker__get_track_data()
                        print(f"🔍 Tracker track data: {track_data}")
                    except Exception as e:
                        print(f"🔍 Could not get tracker track data: {e}")
                else:
                    print("⚠️  LaunchDarkly AI client not available - using basic OpenAI call")
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