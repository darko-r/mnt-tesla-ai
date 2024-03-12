from openai import OpenAI
client = OpenAI()
import time
from typing import List, Optional
import re
import datetime
import dateparser
from langchain.tools import BaseTool
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
import json

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

metadata_assistant = 'asst_W6n8gUPfbDE93aeShi0UA1MC'

classifier_prompt = """
Your task is to classify prompts to one of three categories, respond only with "Logic" or "Summarize" or "Search", based on following descriptions:

- Logic: If a prompt asks for something that can be done with logical operations on a list of dictionaries of Nikola Tesla work with fields title, type, date, source. For example count of elements with a condition, list of elements with a condition...

- Summarize: If a prompt asks for a summarization of a file.

- Search: For broader questions that ask for some interpretation of Nikola Tesla's work and prompts that do not fall in above categories.

Examples:
	- How many articles did Nikola Tesla file publish in New York Times? -> Logic
	- What did Nikola Tesla thinka bout life on Mars? -> Search
	- Summarize patent 505 -> Summarize

Prompt: {0}

Make sure to only answer with "Logic" or "Summarize" or "Search", nothing else.
"""

def strip1(s: str) -> str:
    return s.strip().strip('"').strip('\'').strip(')').strip('(').strip('"').strip('\'')

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
    return [assistant for assistant in all_assistants if assistant.id != metadata_assistant]

def classify(prompt: str) -> str:
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": classifier_prompt.format(prompt)}
        ]
    )
    return strip1(completion.choices[0].message.content)

relevant_keys = ['title', 'date', 'source', 'type', 'register_num']

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
        return [e for e in self.data if eval(parsed_condition)]

    async def _arun(
        self, tool_input: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool asynchronously."""
        self._run(tool_input)

custom_tool = TeslaToolGetDocuments(data=json.load(open(('metadata.json'))))
llm = ChatOpenAI(model="gpt-3.5-turbo-1106")
tools = [custom_tool]
prompt = hub.pull("hwchase17/react")
agent = create_react_agent(llm, tools, prompt)
agent_exec = AgentExecutor(agent=agent, tools=tools, verbose=True)