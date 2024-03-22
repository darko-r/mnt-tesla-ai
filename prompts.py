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

sql_prompt = """
You have a single table called metadata that contains entries of files by Nikola Tesla, columns of interest are: 'index', 'id', 'title', 'date', 'type', 'source', 'register_num', 'summary'.
Nikola Tesla is the author of all entries, so he should not be used in queries.
Source is available only for articles, and is the publisher of the article.
Register_num is available only for patents.

Based on that answer the following question: {0}
"""