import functools
from typing import TypedDict
from typing import List
from collections import defaultdict

from prompts import sql_prompt, llm_prompt, base_supervisor_system_prompt, \
    supervisor_system_prompt, rag_system_prompt

from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.tools.retriever import create_retriever_tool
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.messages import HumanMessage
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
    done - patent location
    
    - parse and print citation
    - history
    - RAG agent
    - hybrid search
    - OpenAI finetune
    
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

gpt_4 = "gpt-4o"

llm = ChatOpenAI(model=gpt_4, temperature=0)

# sql agent
db = SQLDatabase.from_uri("sqlite:///metadata.db")
prompt_template = ChatPromptTemplate.from_messages([
    ("system", sql_prompt),
    MessagesPlaceholder(variable_name="messages"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])
tools = SQLDatabaseToolkit(llm=llm, db=db).get_tools()
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


# llm agent
class CustomOutputParser(BaseOutputParser):
    def parse(self, output):
        return {'output': output}
output_parser = CustomOutputParser()
prompt_template = ChatPromptTemplate.from_messages([
    ("system", llm_prompt),
    MessagesPlaceholder(variable_name="messages"),
])
simple_llm_chain = LLMChain(
    llm=llm,
    prompt=prompt_template,
    output_parser=output_parser
)


# RAG agent
# prompt = ChatPromptTemplate.from_messages([
#     ("system", rag_system_prompt),
#     MessagesPlaceholder(variable_name="messages"),
# ])
# vectorstore = Chroma(persist_directory='notebooks/db', embedding_function=OpenAIEmbeddings())
# retriever = vectorstore.as_retriever()
# question_answer_chain = create_stuff_documents_chain(llm, prompt)
# rag_chain = create_retrieval_chain(retriever, question_answer_chain)

vectorstore = Chroma(persist_directory='notebooks/db', embedding_function=OpenAIEmbeddings())
retriever = vectorstore.as_retriever()
tool = create_retriever_tool(
    retriever,
    "retrieve_docs",
    "Search and return information about Nikola Tesla works.",
)
tools = [tool]
prompt = ChatPromptTemplate.from_messages([
    ("system", rag_system_prompt),
    MessagesPlaceholder(variable_name="messages"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
    # MessagesPlaceholder(variable_name="context"),
])
agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)


# supervisor agent
members = ["SQL", "CHAT", "RAG"]
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
    | llm.bind_functions(functions=[function_def], function_call="route")
    | JsonOutputFunctionsParser()
)

# graph definition
class ConversationState(TypedDict):
    messages: List[HumanMessage]
    next: str
    session_id: str
    context: str

conversation_history = defaultdict(list)

def agent_node_with_memory(state, agent, name):
    print(name)
    result = agent.invoke(state)
    # print(name, result)
    print(name)
    if 'text' in result:
        new_message = HumanMessage(content=result['text']["output"], name=name)
    else:
        new_message = HumanMessage(content=result["output"], name=name)
    
    session_id = state.get("session_id")
    if session_id is not None:
        conversation_history[session_id].append(new_message)
    
    return {"messages": conversation_history[session_id]}

sql_node = functools.partial(agent_node_with_memory, agent=sql_agent_executor, name="SQL")
chat_node = functools.partial(agent_node_with_memory, agent=simple_llm_chain, name="CHAT")
rag_node = functools.partial(agent_node_with_memory, agent=agent_executor, name="RAG")
workflow = StateGraph(ConversationState)
workflow.add_node("SQL", sql_node)
workflow.add_node("CHAT", chat_node)
workflow.add_node("RAG", rag_node)
workflow.add_node("supervisor", supervisor_chain)
for member in members:
    workflow.add_edge(member, "supervisor")
conditional_map = {k: k for k in members}
conditional_map["FINISH"] = END
workflow.add_conditional_edges("supervisor", lambda x: x["next"], conditional_map)
workflow.set_entry_point("supervisor")
graph = workflow.compile()

# function to get response
def get_response(prompt: str, session_id: str) -> str:

    conversation_history[session_id].append(HumanMessage(content=prompt))

    state = {
        "messages": conversation_history[session_id],
        "next": "",  # Assuming some value for the next state
        "session_id": session_id,
        "context": ""
    }

    o = graph.invoke(state)
    return o['messages'][-1].content
