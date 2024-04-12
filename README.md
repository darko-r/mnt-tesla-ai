## Overview

This is an AI chat model project developed in colaboration with [the Nikola Tesla museum](https://tesla-museum.org/).

The idea of the application is to provide easier access to the information about a database of Nikola Tesla's works, articles and patents.

The whole database is currently not available for general audience.

## Models used

Current implementation uses OpenAI's
* gpt-3.5-turbo
* gpt-4-turbo-preview

But other model experimentation and testing is planned.

## Usage

Install necessary packages with:
```
pip install -r requirements
```

OpenAI API key is needed to run this app, it should be set as environemnt variable before deployment.
Run the app with:
```
streamlit app.py
```

## TODO

* OpenAI assistant RAG implementation integration
* RAG from scratch implementation
* Agent history of communication