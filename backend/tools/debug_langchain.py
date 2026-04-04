import langchain
print(dir(langchain))
try:
    import langchain.retrievers
    print("langchain.retrievers aliases:", dir(langchain.retrievers))
except ImportError as e:
    print("Import error:", e)
