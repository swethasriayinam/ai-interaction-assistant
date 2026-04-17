from typing import TypedDict, Annotated, Sequence
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import operator
from tools import tools_list
from dotenv import load_dotenv

load_dotenv()

# 1. Define the State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# 2. Setup the Prompt and Model
prompt_template = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a professional CRM assistant. "
        "When a user describes a meeting or asks to update records, you MUST use the appropriate tool. "
        "CRITICAL: DO NOT write text like {{function=...}} or <function>...</function> in your response. "
        "Just execute the tool call internally. "
        "Once the tool is finished, confirm the action to the user in a friendly way."
    )),
    MessagesPlaceholder(variable_name="messages"),
])

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
# We bind the tools to the LLM here
model = prompt_template | llm.bind_tools(tools_list)

# 3. Define Node Functions
async def call_model(state: AgentState):
    # We bind the tools and call the LLM directly with the message list
    # This stops the LLM from 'hallucinating' a success message before the tool runs
    response = await llm.bind_tools(tools_list).ainvoke(state["messages"])
    return {"messages": [response]}

def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    # If the LLM generated tool calls, go to the tools node
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    # Otherwise, stop
    return END

# 4. Build the Graph
workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools_list))

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

# 5. Compile
app_agent = workflow.compile()