system_prompt = """
You have a single table called metadata that contains entries of files by Nikola Tesla, columns of interest are: 'index', 'id', 'title', 'date', 'type', 'source', 'register_num', 'summary'.
Nikola Tesla is the author of all entries, so he should not be used in queries, or to parse titles.
Source is available only for articles, and is the publisher of the article.
Register_num is available only for patents.
Type can be 'lecture', 'article', or 'patent'.

"""

sql_prompt = """
You have a single table called metadata that contains entries of files by Nikola Tesla, columns of interest are: 'index', 'id', 'title', 'date', 'type', 'source', 'register_num', 'summary'.
Nikola Tesla is the author of all entries, so he should not be used in queries.
Source is available only for articles, and is the publisher of the article.
Register_num is available only for patents.

Based on that answer the following question: {0}
"""