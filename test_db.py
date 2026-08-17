from database.db import init_db
from database.subscribers import (
    add_subscriber,
    remove_subscriber,
    get_subscribers
)

init_db()

print("Adding emails")

print(add_subscriber("test1@gmail.com"))
print(add_subscriber("test2@gmail.com"))
print(add_subscriber("test1@gmail.com"))  # duplicate

print("\nSubscriber list")

print(get_subscribers())

print("\nRemoving")

print(remove_subscriber("test1@gmail.com"))

print("\nList after removal")

print(get_subscribers())