import operator
import functools
from typing import Annotated, Sequence, TypedDict

from prompts import sql_prompt, llm_prompt, base_supervisor_system_prompt, \
    supervisor_system_prompt

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain.agents.agent import AgentExecutor, RunnableMultiActionAgent
from langchain.agents import create_openai_tools_agent
from langchain.chains import LLMChain
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langgraph.graph import StateGraph, END

"""
TODO
    done - copy all from langchian here
    done - integrade cond_parser 
    done - integrate classifier
    done - write get_file_name
    done - supervisor agent
    done - normal chat
    
    - parse and print citation
    - history
    - RAG agent
    
    not_needed - adding additional tools
    not_needed - search branch
    not_needed - asst_summary -> id_summary
    not_needed - try/catch around response generation
    not_needed - chrono sort output
    not_needed - count output
    not_needed - multiple count
"""

from langchain_openai import ChatOpenAI
import os
gpt_3_5 = "gpt-3.5-turbo"
gpt_4 = "gpt-4-turbo-preview"

llm3 = ChatOpenAI(model=gpt_3_5, temperature=0)
llm4 = ChatOpenAI(model=gpt_4, temperature=0)
llm = ChatOpenAI(model=gpt_3_5, temperature=0)

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "Multi-agent Collaboration app"


# sql agent
db = SQLDatabase.from_uri("sqlite:///metadata.db")
prompt_template = ChatPromptTemplate.from_messages([
    ("system", sql_prompt),
    MessagesPlaceholder(variable_name="messages"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])
tools = tools = SQLDatabaseToolkit(llm=llm, db=db).get_tools()
agent = RunnableMultiActionAgent(
    runnable=create_openai_tools_agent(llm, tools, prompt_template),
    input_keys_arg=["messages"],
    return_keys_arg=["output"],
)
sql_agent_executor = AgentExecutor(
    name="SQL Agent Executor",
    agent=agent,
    tools=tools,
    callback_manager=None,
    verbose=True,
    max_iterations=15,
    max_execution_time=None,
    early_stopping_method="force",
)


# llm "agent"
class CustomOutputParser(BaseOutputParser):
    def parse(self, output):
        return {'output': output}
output_parser = CustomOutputParser()
prompt_template = ChatPromptTemplate.from_messages([
    ("system", llm_prompt),
    MessagesPlaceholder(variable_name="messages"),
])
simple_llm_chain = LLMChain(
    llm=llm3,
    prompt=prompt_template,
    output_parser=output_parser
)


# supervisor agent
members = ["SQL", "CHAT"]
options = ["FINISH"] + members
function_def = {
    "name": "route",
    "description": "Select the next role.",
    "parameters": {
        "title": "routeSchema",
        "type": "object",
        "properties": {
            "next": {
                "title": "Next",
                "anyOf": [
                    {"enum": options},
                ],
            }
        },
        "required": ["next"],
    },
}
prompt = ChatPromptTemplate.from_messages([
    ("system", base_supervisor_system_prompt.format(members=members)),
    MessagesPlaceholder(variable_name="messages"),
    ("system", supervisor_system_prompt.format(options=options)),
]).partial(options=str(options), members=", ".join(members))
supervisor_chain = (
    prompt
    | llm4.bind_functions(functions=[function_def], function_call="route")
    | JsonOutputFunctionsParser()
)

# graph definition
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str
def agent_node(state, agent, name):
    result = agent.invoke(state)
    print(name, result)
    if 'text' in result:
        return {"messages": [HumanMessage(content=result['text']["output"], name=name)]}
    return {"messages": [HumanMessage(content=result["output"], name=name)]}
sql_node = functools.partial(agent_node, agent=sql_agent_executor, name="SQL")
chat_node = functools.partial(agent_node, agent=simple_llm_chain, name="CHAT")
workflow = StateGraph(AgentState)
workflow.add_node("SQL", sql_node)
workflow.add_node("CHAT", chat_node)
workflow.add_node("supervisor", supervisor_chain)
for member in members:
    workflow.add_edge(member, "supervisor")
conditional_map = {k: k for k in members}
conditional_map["FINISH"] = END
workflow.add_conditional_edges("supervisor", lambda x: x["next"], conditional_map)
workflow.set_entry_point("supervisor")
graph = workflow.compile()

# function to get response
def get_response(prompt: str) -> str:
    o = graph.invoke({"messages": [HumanMessage(content=prompt)]})
    return o['messages'][-1].content
    # return agent_with_chat_history.invoke({"input": sql_prompt.format(prompt)}, config={"configurable": {"session_id": "<foo>"}})['output']
