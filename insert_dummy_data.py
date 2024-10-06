import random
from faker import Faker
import psycopg2

# Initialize Faker
fake = Faker()

# Establish a connection to the transactional database
conn_transactional = psycopg2.connect(
    host="localhost",
    port="5433",
    database="transactional_db",
    user="user",
    password="password"
)
cur_transactional = conn_transactional.cursor()

# Begin transaction
conn_transactional.autocommit = False

try:
    # Define the number of dummy records to create
    num_users = 100
    num_authors = 50
    num_books = 200
    num_reviews = 300
    num_orders = 150

    # Insert dummy users and keep track of user IDs
    user_ids = []
    for _ in range(num_users):
        cur_transactional.execute(
            "INSERT INTO users (user_name, email, wallet_balance, phone_number, address) VALUES (%s, %s, %s, %s, %s) RETURNING user_id",
            (fake.name()[:50], fake.email()[:50], random.uniform(10.0, 500.0), fake.phone_number()[:20], fake.address()[:100])
        )
        user_ids.append(cur_transactional.fetchone()[0])  # Store the generated user ID

    # Insert dummy authors and keep track of author IDs
    author_ids = []
    for _ in range(num_authors):
        cur_transactional.execute(
            "INSERT INTO authors (author_name, email, nationality) VALUES (%s, %s, %s) RETURNING author_id",
            (fake.name()[:50], fake.email()[:50], fake.country()[:50])
        )
        author_ids.append(cur_transactional.fetchone()[0])  # Store the generated author ID

    # Insert dummy books and their associations with authors
    book_ids = []  # To keep track of book IDs for later use
    for _ in range(num_books):
        # Insert into books
        cur_transactional.execute(
            "INSERT INTO books (title, publish_date, isbn, genre, price) VALUES (%s, %s, %s, %s, %s) RETURNING book_id",
            (fake.sentence(nb_words=4)[:100], fake.date(), fake.isbn13(), fake.word()[:50], random.uniform(5.0, 50.0))
        )
        book_id = cur_transactional.fetchone()[0]
        book_ids.append(book_id)  # Store the generated book ID
        
        # Associate the book with a random existing author
        cur_transactional.execute(
            "INSERT INTO book_author (book_id, author_id) VALUES (%s, %s)",
            (book_id, random.choice(author_ids))
        )

    # Insert dummy reviews
    for _ in range(num_reviews):
        user_id = random.choice(user_ids)
        book_id = random.choice(book_ids)
        cur_transactional.execute(
            "INSERT INTO reviews (user_id, book_id, rate, review_text, review_date) VALUES (%s, %s, %s, %s, %s)",
            (user_id, book_id, random.randint(1, 5), fake.text(), fake.date())
        )

    # Insert dummy orders
    for _ in range(num_orders):
        user_id = random.choice(user_ids)
        cur_transactional.execute(
            "INSERT INTO orders (user_id, order_date, total_amount, order_created, order_completed) VALUES (%s, %s, %s, %s, %s) RETURNING order_id",
            (user_id, fake.date(), random.uniform(10.0, 500.0), fake.date(), fake.date())
        )

        order_id = cur_transactional.fetchone()[0]

        # Insert dummy order items (order_book)
        for _ in range(random.randint(1, 3)):  # Random number of books per order
            cur_transactional.execute(
                "INSERT INTO order_book (order_id, book_id, quantity) VALUES (%s, %s, %s)",
                (order_id, random.choice(book_ids), random.randint(1, 5))
            )

    # Commit changes to the database
    conn_transactional.commit()

except Exception as e:
    # Rollback in case of error
    conn_transactional.rollback()
    print(f"An error occurred: {e}")

finally:
    # Close the cursor and connection
    cur_transactional.close()
    conn_transactional.close()

print("Dummy data inserted successfully!")
