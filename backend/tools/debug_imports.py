try:
    from langchain.retrievers.multi_query import MultiQueryRetriever
    print("found in langchain.retrievers.multi_query")
except ImportError:
    pass

try:
    from langchain_community.retrievers import MultiQueryRetriever
    print("found in langchain_community.retrievers")
except ImportError:
    pass
