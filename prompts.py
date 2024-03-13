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

# Revisit if possible?
count_prompt = """
Your task is to classify whether a given prompt requires counting elements of a certain list. List will be provided by another tool so no need to worry about that. Just output "1" if some sort of counting should be done and "0" if not. If a prompt asks for a list of documents but not the number of documents answer "0". Take the following examples:
	- How many articles did Nikola Tesla file publish in New York Times? -> 1
	- What did Nikola Tesla think about life on Mars? -> 0
	- Summarize patent 505 -> 0
    - can you give me the list of articles, patents and lectures of Nikola Tesla -> 0
    - can you list Nikola Tesla lectures chronologically -> 0
    - how many patent was issued by Nikola Tesla? -> 1
    - how many lectures and articles were issued by Nikola Tesla between 1901 and 1905? -> 1
    - list best Nikola Tesla articles -> 0
    - List Nikola Tesla lectures after 1901 -> 0
    - How many patents did Nikola Tesla file before 1905 -> 1

Prompt: {0}

Make sure to only answer with "1" if counting is needed or "0" if not.
"""
