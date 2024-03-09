from openai import OpenAI
client = OpenAI()
import time
from typing import List
import json
import operator
import re
import datetime
import dateparser

"""
TODO
    done - copy all from langchian here
    done - integrade cond_parser 
    done - integrate classifier
    - write final_ret
    done - write get_file_name
    - search branch
    - LangChain tidy-up
    - parse and print citation
    - chrono sort output
    - count output
    - multiple count
"""

metadata_assistant = 'asst_W6n8gUPfbDE93aeShi0UA1MC'

condition_parse_prompt = """
Taking into account the possible keys and their possible values, definitions of allowed output functions and the following example convert text prompt to condition string. Respond only with the conditions string, nothing else. Disregard all parts of the string that are not the following 5 types. Disregard requests for chronological sorting, consider date only if it is needed for file listing:

Keys and values:
	- id: int
	- date: date
	- title: string
	- type: string (lecture, article or patent)
	- source (Sources are for article publishers, all articles are writter by Nikola Tesla so no need to make a condition for that)

Allowed functions:
	- COUNT: Number of elements of some condition
	- <,>,==,!=,AND,OR: Logical operators

Examples:
	- "How many lectures did Nikola Tesla write between 1895 and 1905?" -> "COUNT("type"=="lecture" AND "date">"1895" AND "date"<"1905")"
	- "can you give me the list of articles, patents and lectures of Nikola Tesla"  -> "("type"=="lecture" OR "type"=="article" OR "type"=="patent")"
	
Prompt: {0}
"""

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

valid_fields = ['id', 'title', 'date', 'type', 'source']
ops = {
    "AND": operator.and_,
    "OR": operator.or_,
    "==": operator.eq,
    "!=": operator.ne,
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge 
}
prior = {
    "AND": 1,
    "OR": 1,
    "==": 0,
    "!=": 0,
    "<": 0,
    "<=": 0,
    ">": 0,
    ">=": 0
}

def strip1(s: str) -> str:
    return s.strip().strip('"').strip('\'').strip(')').strip('(').strip('"').strip('\'')

def get_ops(string):
    search_chars = ['AND', 'OR', '>', '<', '==', '!=']

    indexes = []

    for char in search_chars:
        index = string.find(char)
        while index != -1:
            indexes.append({char: index})
            index = string.find(char, index + 1)

    return indexes

def get_elements(string):
    elements_ = re.split('AND|OR|>|<|==|!=', string)
    indexes = []
    
    for e in [strip1(e) for e in elements_]:
        index = string.find(e)
        while index != -1:
            if {e: index} not in indexes:
                indexes.append({e: index})
            index = string.find(e, index + 1)

    return indexes

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

class json_entry():
    dict_: dict

    def __init__(self, d: dict) -> None:
        self.dict_ = d

    def condition(self, condition: str) -> bool:
        """
            Returns bool for dict based on given condition.

            Conditions are expected to be in form: "key1"=="value1" AND "key1">"value2 OR "key3"!="value3""
        """
        operations = get_ops(condition)
        elements = get_elements(condition)
        l = sorted(operations + elements, key=lambda e: list(e.values())[0])
        l = [list(e.keys())[0] for e in l]
        maxPrior = 1
        old_l = None
        for priorMode in range(maxPrior+1):
            while True:
                old_l = l.copy()
                for ind, element in enumerate(l):
                    if element in ops:
                        priorLev = prior[element]
                        if priorLev <= priorMode:
                            element_prev = l[ind-1]
                            element_next = l[ind+1]
                            assert element_prev not in ops, f"invalid operation: {element_prev} {element} {element_next}"
                            assert element_next not in ops, f"invalid operation: {element_prev} {element} {element_next}"
                            res = self.fun(element_prev, element, element_next)
                            ind = l.index(element_prev)
                            l.remove(element_prev)
                            l.remove(element_next)
                            l.remove(element)
                            l.insert(ind, res)
                if old_l == l:
                    break
        return l[0]
    
    # TODO (JAKSA) tidy up pls
    def fun(self, value1, op, value2) -> bool:
        if isinstance(value1, bool) and isinstance(value2, bool):
            return ops[op](value1, value2)
        bools = False
        if value1 == "True":
            bools = True
            value1 = True
        elif value1 == "False":
            bools = True
            value1 = False
        if value2 == "True":
            bools = True
            value2 = True
        elif value2 == "False":
            bools = True
            value2 = False
        
        if bools:
            return ops[op](value1, value2)
        if value1 in valid_fields:
            key = value1
            value = value2
        elif value2 in valid_fields:
            key = value2
            value = value1
        else:
            raise RuntimeError(f"invalid fun {value1} {op} {value2}")
        if key == 'date':
            dict_value = datetime.datetime.strptime(self.dict_[key], '%Y-%m-%d')
            value = dateparser.parse(value)
        else:
            dict_value = self.dict_[key]
        if not dict_value:
            return False
        return ops[op](dict_value, value)


class json_entry_list():
    list_: List[json_entry]

    def __init__(self, path: str) -> None:
        self.list_ = [json_entry(e) for e in json.load(open(path))]

    def fetch(self, condition: str) -> List[str]:
        return [e.dict_['title'] for e in self.list_ if e.condition(condition)]

    def count(self, condition: str) -> int:
        return len(self.fetch(condition))

def classify(prompt: str) -> str:
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": classifier_prompt.format(prompt)}
        ]
    )
    return strip1(completion.choices[0].message.content)

def parse_condition(prompt: str) -> str:
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": condition_parse_prompt.format(prompt)}
        ]
    )
    return strip1(completion.choices[0].message.content)