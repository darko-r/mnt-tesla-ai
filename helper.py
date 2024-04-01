from openai import OpenAI
from prompts import sql_prompt, system_prompt
from langchain_openai import ChatOpenAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.chat_message_histories import ChatMessageHistory

"""
TODO
    done - copy all from langchian here
    done - integrade cond_parser 
    done - integrate classifier
    done - write get_file_name
    
    - parse and print citation
    - history
    - adding additional tools
    - supervisor agent
    - normal chat
    
    not_needed - search branch
    not_needed - asst_summary -> id_summary
    not_needed - try/catch around response generation
    not_needed - chrono sort output
    not_needed - count output
    not_needed - multiple count
"""
client = OpenAI()

gpt_3_5 = "gpt-3.5-turbo"
gpt_4 = "gpt-4-turbo-preview"

db = SQLDatabase.from_uri("sqlite:///metadata.db")
llm = ChatOpenAI(model=gpt_4, temperature=0)
prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])
sql_agent = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True, top_k=200, prompt=prompt_template)
message_history = ChatMessageHistory()
agent_with_chat_history = RunnableWithMessageHistory(
    sql_agent,
    lambda session_id: message_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)

def get_response(prompt: str) -> str:
    return agent_with_chat_history.invoke({"input": sql_prompt.format(prompt)}, config={"configurable": {"session_id": "<foo>"}})['output']
