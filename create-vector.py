from glob import glob

import chromadb

client = chromadb.PersistentClient(path="./chroma/")
try:
    client.delete_collection(name='concepts')
    print("Deleted existing collection 'concepts'")
except Exception:
    pass

collection = client.create_collection(name='concepts')
print("Created new collection 'concepts'")

md_files = glob("./concepts/*.md")
content = []
ids = []
for f in md_files:
    with open(f, 'r') as file:
        content.append(file.read())
        ids.append(f)

collection.add(
    documents=content,
    ids=ids,
)

print(f"Added {len(content)} documents to the collection")
