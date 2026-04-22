from database.db import init_db
from database.subscribers import (
    add_subscriber,
    remove_subscriber,
    get_subscribers
)

init_db()

print("Dodawanie maili")

print(add_subscriber("test1@gmail.com"))
print(add_subscriber("test2@gmail.com"))
print(add_subscriber("test1@gmail.com"))  # duplikat

print("\nLista subskrybentów")

print(get_subscribers())

print("\nUsuwanie")

print(remove_subscriber("test1@gmail.com"))

print("\nLista po usunięciu")

print(get_subscribers())