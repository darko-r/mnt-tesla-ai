from openai import OpenAI
client = OpenAI()
import time
from typing import List, Optional, Union
import re
import datetime
import dateparser
from langchain.tools import BaseTool
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
import json
from enum import Enum
from prompts import classifier_prompt, count_prompt

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
gpt_3_5 = "gpt-3.5-turbo"
gpt_4 = "gpt-4-turbo-preview"

class PromptClass(Enum):
    LOGIC = "logic"
    SUMMARIZE = "summarize"
    SEARCH = "search"

class PromptSort(Enum):
    ASC = "ascending"
    DSC = "descending"

def all_assistants():
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

def is_prompt_count(prompt: str) -> bool:
    count_substrings = ["count", "how many" "total", "number of", "quantity of", "amount of", "tally", "enumerate", "calculate", "sum of", "total number", "aggregate", "tally up", "compute", "quantify"]
    return any([s in prompt.lower() for s in count_substrings])

def is_prompt_sort(prompt: str) -> Optional[PromptSort]:
    sort_substrings = ["sort", "order", "arrange", "organize", "chronological"]
    if not any([s in prompt.lower() for s in sort_substrings]):
        return None
    return PromptSort.DSC if "descending" in prompt else PromptSort.ASC

def format_string(s):
    relevant_keys = ['title', 'date', 'source', 'type', 'register_num']
    for relevant_key in relevant_keys:
        s = s.replace(relevant_key, f"e['{relevant_key}']")

    types = ['lecture', 'article', 'patent']
    for type_ in types:
        s = s.replace(type_, f"'{type_}'")

    s = s.replace("e['date']", "datetime.datetime.strptime(e[\'date\'], \'%Y-%m-%d\')")

    def replace_four_digit_numbers(text):
        pattern = r"\b(\d{4})\b"
        return re.sub(pattern, r"dateparser.parse('\1')", text)

    return replace_four_digit_numbers(s)

results_list = []
class TeslaToolGetDocuments(BaseTool):
    name = "tesla_tool_get_documents"
    description = """
    Can be used to list all relevant Nikola Tesla document entries from a dictionary in memory based on a condition.
    All entries are about documents written by Nikola Tesla, so don't consider him a source, sources are only considered for article publishers.
    Fields that are available for search are title(str), date(str), source(str), type(str, possible values lecture, article, patent), register_num(str)
    Operations that are available for search are "or, and, ==, <=, >=, <, >, !="
    The tool takes as input a string representing conditions for search delimited with a single whitespace.
    Example tool input:
        type == lecture and date < 1905 and date > 1900
    """
    return_direct: bool = True

    data: List
    
    def _run(self, tool_input: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        parsed_condition = format_string(tool_input)
        print(parsed_condition)
        results_list = [e for e in self.data if eval(parsed_condition)]
        return results_list

    async def _arun(
        self, tool_input: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool asynchronously."""
        self._run(tool_input)

custom_tool = TeslaToolGetDocuments(data=json.load(open(('metadata.json'))))
llm = ChatOpenAI(model=gpt_4)
tools = [custom_tool]
prompt = hub.pull("hwchase17/react")
agent = create_react_agent(llm, tools, prompt)
agent_exec = AgentExecutor(agent=agent, tools=tools, verbose=True)
asst_summary = json.load(open('assistant_summary.json'))

def get_response(prompt: str) -> str:
    prompt_class = classify(prompt)
    print(f"Classified prompt {prompt} as {prompt_class.value}")
    if prompt_class == PromptClass.LOGIC:
        result = agent_exec.invoke({"input": prompt})['output']
        if not result:
            return "Sorry, no documents match your description."
        if is_prompt_count(prompt):
            result = result[0:10]
            return f"Certainly, {len(result)} documents match your description. Here are some of them: {', '.join(map(str, [r['title'] for r in result]))}"
        elif is_prompt_sort(prompt):
            return f"Of course, here is a list of found documents that match your description in chronological order: \n{', '.join(map(str, [r['title'] for r in result])) }" 
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
    