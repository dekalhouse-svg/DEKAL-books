from database import get_db

def row_to_dict(row):
    if not row:
        return None
    return dict(row)

def get_books(query="", category="", sort="recent", page=1, per_page=12):
    conn = get_db()
    where = []
    params = []

    if query:
        where.append("(LOWER(title) LIKE ? OR LOWER(author) LIKE ? OR LOWER(description) LIKE ? OR LOWER(category) LIKE ?)")
        q = f"%{query.lower()}%"
        params.extend([q, q, q, q])
    if category and category != "Tous":
        where.append("category = ?")
        params.append(category)

    where_sql = " WHERE " + " AND ".join(where) if where else ""
    order = {
        "recent": "created_at DESC, id DESC",
        "downloads": "downloads DESC, created_at DESC",
        "az": "LOWER(title) ASC, id ASC"
    }.get(sort, "created_at DESC, id DESC")

    total = conn.execute(f"SELECT COUNT(*) FROM books{where_sql}", params).fetchone()[0]
    offset = (page - 1) * per_page
    rows = conn.execute(
        f"SELECT * FROM books{where_sql} ORDER BY {order} LIMIT ? OFFSET ?",
        params + [per_page, offset]
    ).fetchall()
    conn.close()

    return {
        "items": [row_to_dict(r) for r in rows],
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": (total + per_page - 1) // per_page
    }

def get_book(book_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    conn.close()
    return row_to_dict(row)

def create_book(title, author, description, category, filename, filesize):
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO books(title, author, description, category, filename, filesize)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (title, author, description, category, filename, filesize))
    conn.commit()
    book_id = cur.lastrowid
    conn.close()
    return get_book(book_id)

def update_book(book_id, title, author, description, category, filename, filesize):
    conn = get_db()
    conn.execute("""
        UPDATE books
        SET title=?, author=?, description=?, category=?, filename=?, filesize=?
        WHERE id=?
    """, (title, author, description, category, filename, filesize, book_id))
    conn.commit()
    conn.close()
    return get_book(book_id)

def delete_book(book_id):
    conn = get_db()
    cur = conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted

def increment_downloads(book_id):
    conn = get_db()
    conn.execute("UPDATE books SET downloads = downloads + 1 WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
