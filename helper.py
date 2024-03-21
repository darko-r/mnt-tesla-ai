from openai import OpenAI
import time
from typing import List, Optional, Union
import re
from langchain_openai import ChatOpenAI
from enum import Enum
from prompts import classifier_prompt
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI


"""
TODO
    done - copy all from langchian here
    done - integrade cond_parser 
    done - integrate classifier
    done - write get_file_name
    - try/catch around response generation
    - search branch
    - parse and print citation
    - chrono sort output
    - count output
    - multiple count
    - history?
    - asst_summary -> id_summary
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
sql_agent = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True, top_k=200)

def get_response(prompt: str) -> str:
    prompt_class = classify(prompt)
    print(f"Classified prompt {prompt} as {prompt_class.value}")
    if prompt_class == PromptClass.LOGIC:
        result = sql_agent.invoke({"input": prompt})['output']
        if not result:
            return "Sorry, no documents match your description."
        else:
            return f"Of course, here is a list of found documents that match your description: \n{', '.join(map(str, [r['title'] for r in result])) }"
    elif prompt_class == PromptClass.SUMMARIZE:
        title = prompt.lower().split('"')[1::2][0]
        print(f"looking for {title} summary")
        ret = [d for d in agent_exec.tools[0].data if d['title'].lower() == title]
        return [a_s for a_s in asst_summary if a_s['assistant_id'] == ret[0]["assistant_OAI_id"]][0]['summary'] if ret else "Was not able to find the file specified."
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
    