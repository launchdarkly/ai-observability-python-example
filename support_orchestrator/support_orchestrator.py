"""
Customer Support Orchestrator — OpenAI Function Calling Demo
-----------------------------------------------------------
What it does:
  • Uses OpenAI's native function calling to route customer messages
  • Tools implemented: create_ticket, fetch_order_status, reset_password
  • Direct OpenAI tool integration with comprehensive observability
  • Feature flags control system behavior via LaunchDarkly
  • Full telemetry via OpenTelemetry + LaunchDarkly observability plugin

Install:
  pip install openai opentelemetry-sdk opentelemetry-exporter-otlp \
              opentelemetry-instrumentation-openai python-dotenv \
              launchdarkly-server-sdk launchdarkly-observability
Run:
  export OPENAI_API_KEY="sk-..."
  export LAUNCHDARKLY_SDK_KEY="sdk-..."
  python3 -m venv .venv && source .venv/bin/activate
  python3 support_orchestrator.py --message "Where is order #A1234?"
"""

import argparse
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
load_dotenv()

# ------------------ LaunchDarkly setup ------------------
import ldclient
from ldclient.config import Config
from ldclient import Context
import ldobserve
from ldobserve import ObservabilityPlugin, ObservabilityConfig

LD_SDK_KEY = os.getenv("LAUNCHDARKLY_SDK_KEY", "")
if LD_SDK_KEY:
    ldclient.set_config(Config(
        LD_SDK_KEY,
        base_uri="https://ld-stg.launchdarkly.com",
        stream_uri="https://stream-stg.launchdarkly.com",
        events_uri="https://events-stg.launchdarkly.com",
        plugins=[ObservabilityPlugin(
            ObservabilityConfig(
                service_name="support-orchestrator",
                service_version="1.0.0",
                environment="development",
                backend_url="https://pub.observability.ld-stg.launchdarkly.com",
                otlp_endpoint="https://otel.observability.ld-stg.launchdarkly.com:4317"
            )
        )]
    ))
    ld_client = ldclient.get()
else:
    print("[warn] LAUNCHDARKLY_SDK_KEY not set; feature flags disabled")
    ld_client = None

# ------------------ OpenTelemetry setup ------------------
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

provider = TracerProvider(resource=Resource.create({
    "service.name": "support-orchestrator",
    "service.version": "1.0.0"
}))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
else:
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

# ------------------ OpenLLMetry instrumentation ------------------
try:
    from opentelemetry.instrumentation.openai import OpenAIInstrumentor
    OpenAIInstrumentor().instrument()
except Exception as e:
    print(f"[warn] OpenAI instrumentation inactive: {e}")

# ------------------ OpenAI client ------------------
try:
    from openai import OpenAI
    openai_client = OpenAI()
except Exception as e:
    print(f"[error] OpenAI SDK not available: {e}")
    sys.exit(1)

# ------------------ Data stores ------------------
TICKETS: Dict[str, Dict[str, Any]] = {}
ORDERS: Dict[str, Dict[str, Any]] = {
    "A1234": {"status": "Shipped", "eta_days": 2, "items": 3, "carrier": "AcmeExpress"},
    "B5678": {"status": "Processing", "eta_days": 5, "items": 1, "carrier": None},
    "C9012": {"status": "Delivered", "eta_days": 0, "items": 2, "carrier": "AcmeExpress"},
}
PASSWORD_RESETS: Dict[str, Dict[str, Any]] = {}

# ------------------ Tool Functions ------------------
def create_ticket(summary: str, user_email: str, priority: str = "normal") -> Dict[str, Any]:
    """Create a support ticket."""
    with tracer.start_as_current_span("create_ticket") as span:
        ticket_id = f"TIC-{uuid.uuid4().hex[:8].upper()}"
        TICKETS[ticket_id] = {
            "id": ticket_id, "summary": summary, "email": user_email, 
            "priority": priority, "status": "open", "created_at": time.time()
        }
        span.set_attribute("ticket.id", ticket_id)
        span.set_attribute("ticket.priority", priority)
        return {"ticket_id": ticket_id, "status": "open", "priority": priority}

def fetch_order_status(order_id: str) -> Dict[str, Any]:
    """Fetch order status by ID."""
    with tracer.start_as_current_span("fetch_order_status") as span:
        span.set_attribute("order.id", order_id)
        order_data = ORDERS.get(order_id)
        if not order_data:
            span.set_attribute("order.found", False)
            return {"found": False, "order_id": order_id}
        
        span.set_attribute("order.found", True)
        span.set_attribute("order.status", order_data["status"])
        return {"found": True, "order_id": order_id, **order_data}

def reset_password(email: str) -> Dict[str, Any]:
    """Reset password for user email."""
    with tracer.start_as_current_span("reset_password") as span:
        span.set_attribute("reset.email", email)
        token = uuid.uuid4().hex[:12]
        PASSWORD_RESETS[email] = {
            "email": email, "token": token, "created_at": time.time(), "status": "pending"
        }
        span.set_attribute("reset.token_generated", True)
        return {
            "email": email, 
            "reset_token": token, 
            "instructions": "Password reset link emailed if account exists."
        }

# ------------------ OpenAI Tools Configuration ------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_ticket",
            "description": "Create a support ticket for customer issues",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Brief summary of the customer's issue"
                    },
                    "user_email": {
                        "type": "string",
                        "description": "Customer's email address"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "normal", "high", "urgent"],
                        "description": "Priority level of the ticket"
                    }
                },
                "required": ["summary", "user_email"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_order_status",
            "description": "Get the current status of a customer order",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID to look up (e.g., A1234, B5678)"
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reset_password",
            "description": "Initiate password reset for a user account",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "User's email address for password reset"
                    }
                },
                "required": ["email"]
            }
        }
    }
]

# Tool function registry for execution
TOOL_FUNCTIONS = {
    "create_ticket": create_ticket,
    "fetch_order_status": fetch_order_status,
    "reset_password": reset_password,
}

# ------------------ Main Orchestrator ------------------
@dataclass
class SupportResult:
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    final_response: str
    feature_flags: Dict[str, Any]

class SupportOrchestrator:
    def __init__(self):
        self.system_message = """You are a helpful customer support assistant. 
        You have access to tools to help customers with their inquiries:
        - Create support tickets for general issues
        - Look up order status and shipping information  
        - Initiate password resets for login problems
        
        Always be friendly, helpful, and provide clear next steps to customers."""

    def _evaluate_feature_flags(self, context: Context) -> Dict[str, Any]:
        """Evaluate all feature flags for this request."""
        flags = {
            "enable_priority_routing": False,
            "max_response_length": 1000,
            "enable_enhanced_responses": False
        }
        
        if ld_client:
            with tracer.start_as_current_span("feature_flag_evaluation"):
                flags["enable_priority_routing"] = ld_client.variation("priority-routing", context, False)
                flags["max_response_length"] = ld_client.variation("max-response-length", context, 1000)
                flags["enable_enhanced_responses"] = ld_client.variation("enhanced-responses", context, False)
                
                # Add all flags as span attributes
                for key, value in flags.items():
                    trace.get_current_span().set_attribute(f"feature_flags.{key}", value)
        
        return flags

    def _execute_tool_calls(self, tool_calls) -> List[Dict[str, Any]]:
        """Execute the function calls and return results."""
        results = []
        
        with tracer.start_as_current_span("execute_tool_calls") as span:
            span.set_attribute("tool_calls.count", len(tool_calls))
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if function_name in TOOL_FUNCTIONS:
                    try:
                        result = TOOL_FUNCTIONS[function_name](**function_args)
                        results.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": json.dumps(result)
                        })
                    except Exception as e:
                        error_result = {"error": str(e), "function": function_name}
                        results.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool", 
                            "name": function_name,
                            "content": json.dumps(error_result)
                        })
                else:
                    # Unknown function fallback
                    fallback_result = {"error": f"Unknown function: {function_name}"}
                    results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(fallback_result)
                    })
            
            span.set_attribute("tool_calls.executed", len(results))
        
        return results

    def handle_request(self, user_message: str) -> SupportResult:
        """Main orchestration method using OpenAI function calling."""
        with tracer.start_as_current_span("support_orchestrator") as main_span:
            # Create LaunchDarkly context and evaluate feature flags
            ld_context = Context.builder("anonymous").build()
            feature_flags = self._evaluate_feature_flags(ld_context)
            
            main_span.set_attribute("user_message_length", len(user_message))
            
            # Prepare messages for OpenAI
            messages = [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": user_message}
            ]
            
            # Adjust system message based on feature flags
            if feature_flags["enable_enhanced_responses"]:
                messages[0]["content"] += "\n\nProvide detailed, comprehensive responses with helpful context."
            
            # Initial OpenAI call with function calling
            with tracer.start_as_current_span("openai_function_call") as call_span:
                call_span.set_attribute("openai.model", "gpt-4o-mini")
                call_span.set_attribute("openai.tools_available", len(TOOLS))
                
                response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    temperature=0.1
                )
                
                call_span.set_attribute("openai.finish_reason", response.choices[0].finish_reason)
            
            # Process tool calls if any
            tool_calls = response.choices[0].message.tool_calls or []
            tool_results = []
            
            if tool_calls:
                # Apply priority routing if enabled
                if feature_flags["enable_priority_routing"] and "urgent" in user_message.lower():
                    for tool_call in tool_calls:
                        if tool_call.function.name == "create_ticket":
                            args = json.loads(tool_call.function.arguments)
                            args["priority"] = "high"
                            tool_call.function.arguments = json.dumps(args)
                
                # Execute tool calls
                tool_results = self._execute_tool_calls(tool_calls)
                
                # Add tool results to conversation and get final response
                messages.append(response.choices[0].message)
                messages.extend(tool_results)
                
                with tracer.start_as_current_span("openai_final_response"):
                    final_response = openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        temperature=0.2
                    )
                    
                    final_content = final_response.choices[0].message.content
            else:
                # No tool calls needed, use direct response
                final_content = response.choices[0].message.content
            
            # Apply response length limit if configured
            if len(final_content) > feature_flags["max_response_length"]:
                final_content = final_content[:feature_flags["max_response_length"]-3] + "..."
            
            main_span.set_attribute("response_length", len(final_content))
            main_span.set_attribute("tool_calls_made", len(tool_calls))
            
            return SupportResult(
                tool_calls=[{
                    "function": tc.function.name,
                    "arguments": json.loads(tc.function.arguments)
                } for tc in tool_calls],
                tool_results=[json.loads(tr["content"]) for tr in tool_results],
                final_response=final_content,
                feature_flags=feature_flags
            )

# ------------------ CLI / REPL ------------------
def main():
    """Main entry point for the support orchestrator."""
    parser = argparse.ArgumentParser(
        description="Customer Support Orchestrator with OpenAI Function Calling"
    )
    parser.add_argument("--message", help="Single message to handle (non-interactive).")
    args = parser.parse_args()
    
    orchestrator = SupportOrchestrator()
    
    if args.message:
        # Single message mode
        result = orchestrator.handle_request(args.message)
        
        print("\n--- Final Response ---")
        print(result.final_response)
        
        print("\n--- Debug Information ---")
        print(f"Tool calls made: {len(result.tool_calls)}")
        for i, tool_call in enumerate(result.tool_calls, 1):
            print(f"  {i}. {tool_call['function']} with args: {tool_call['arguments']}")
        
        print(f"Feature flags: {result.feature_flags}")
        print("LLM backend: OpenAI with function calling")
        return
    
    # Interactive mode
    print("🤖 Customer Support Orchestrator")
    print("Using OpenAI function calling with LaunchDarkly feature flags")
    print("Type 'exit' or 'quit' to end the session\n")
    
    while True:
        try:
            user_input = input("Customer: ").strip()
            if not user_input:
                continue
                
            if user_input.lower() in {"exit", "quit", "bye"}:
                print("👋 Goodbye!")
                break
                
            result = orchestrator.handle_request(user_input)
            print(f"\nSupport Agent: {result.final_response}")
            
            # Show tool usage if any
            if result.tool_calls:
                tool_names = [tc["function"] for tc in result.tool_calls]
                print(f"📝 (Used tools: {', '.join(tool_names)})")
            
            print()  # Empty line for readability
            
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Please try again.\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(130)