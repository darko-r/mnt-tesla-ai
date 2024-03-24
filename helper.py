from openai import OpenAI
import time
from typing import List
import re
from enum import Enum
from prompts import classifier_prompt, sql_prompt
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder



"""
TODO
    done - copy all from langchian here
    done - integrade cond_parser 
    done - integrate classifier
    done - write get_file_name
    not_needed - try/catch around response generation
    - search branch
    - parse and print citation
    not_needed - chrono sort output
    not_needed - count output
    not_needed - multiple count
    - history?
    not_needed - asst_summary -> id_summary
"""
client = OpenAI()

gpt_3_5 = "gpt-3.5-turbo"
gpt_4 = "gpt-4-turbo-preview"

class PromptClass(Enum):
    LOGIC = "logic"
    SUMMARIZE = "summarize"
    SEARCH = "search"

def all_assistants() -> List[str]:
    all_assistants = []
    first_assistants = client.beta.assistants.list(
            order="desc",
            limit=100
        )
    all_assistants.extend(first_assistants.data)
    after_assistant = first_assistants.data[0].id
    while True:
        assistants = client.beta.assistants.list(
            order="desc",
            limit=100,
            after=after_assistant
        )
        all_assistants.extend(assistants.data)
        if len(assistants.data) < 100:
            break
        after_assistant = assistants.data[-1].id
        time.sleep(1)
    return all_assistants

def classify(prompt: str) -> PromptClass:
    completion = client.chat.completions.create(
        model=gpt_4,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": classifier_prompt.format(prompt)}
        ]
    )
    output = completion.choices[0].message.content.lower()
    if "logic" in output:
        return PromptClass.LOGIC
    elif "summarize" in output:
        return PromptClass.SUMMARIZE
    return PromptClass.SEARCH

db = SQLDatabase.from_uri("sqlite:///metadata.db")
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
                """
                You have a single table called metadata that contains entries of files by Nikola Tesla, columns of interest are: 'index', 'id', 'title', 'date', 'type', 'source', 'register_num', 'summary'.
                Nikola Tesla is the author of all entries, so he should not be used in queries, or to parse titles.
                Source is available only for articles, and is the publisher of the article.
                Register_num is available only for patents.
                Type can be 'lecture', 'article', or 'patent'.
                """
        ),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)
sql_agent = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True, top_k=200, prompt=prompt_template)
message_history = ChatMessageHistory()
agent_with_chat_history = RunnableWithMessageHistory(
    sql_agent,
    lambda session_id: message_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)

def get_response(prompt: str) -> str:
    #   prompt_class = classify(prompt)
    # print(f"Classified prompt {prompt} as {prompt_class.value}")
    return agent_with_chat_history.invoke({"input": sql_prompt.format(prompt)}, config={"configurable": {"session_id": "<foo>"}})['output']
    if prompt_class == PromptClass.LOGIC:
        return sql_agent.invoke({"input": sql_prompt.format(prompt)}, config={"configurable": {"session_id": "<foo>"}})['output']
    else:
        file_assistants = all_assistants()
        for assistant in (a.id for a in file_assistants):
            print(f"Starting search for assistant {assistant}")
            thread = client.beta.threads.create()
            run = client.beta.threads.runs.create(
                thread_id = thread.id,
                assistant_id = assistant
            )
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )

            while run.status != "completed":
                run = client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                time.sleep(1)
            
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            last_msg = max(messages.data, key = lambda x: x.created_at)
            assistant_response = re.sub('【.*】', '', last_msg.content[0].text.value)
            if assistant_response != "I'm sorry, I don't know the answer.":
                print(f"Found response with assistant {assistant}")
                response = assistant_response
                break
    