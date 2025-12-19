import mysql.connector as sql
import pandas as pd
import sqlalchemy as sa

# Replace with your MySQL credentials
db_host = 'localhost'
db_port = 3306
db_user = 'root'
db_password = 'test_root'
db_name = 'academicworld'

# Create a connection string
connection_string = f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Create an engine (using SQLAlchemy)
engine = sa.create_engine(connection_string)

# create index if not exist
connection = engine.connect()
def index_exists():
    check_index_query = """
    SELECT 1
    FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = 'academicworld' 
    AND TABLE_NAME = 'keyword' 
    AND INDEX_NAME = 'idx_keyword_name';
    """
    result = connection.execute(sa.text(check_index_query))
    if result.fetchone() is not None:
        return True
    else:
        return False

if index_exists() == False:
    connection.execute(sa.text("CREATE INDEX idx_keyword_name ON keyword(name);"))
    connection.commit()

def get_data(query):
    df = pd.read_sql(query, engine)
    return df

def get_top_keywords(top_n=5):
    return get_data(f"""
        SELECT k.name AS keyword, COUNT(DISTINCT pk.publication_id) AS popularity
        FROM publication_keyword pk
        JOIN publication p ON pk.publication_id = p.ID
        JOIN keyword k ON pk.keyword_id = k.id
        WHERE p.year >= '2012'
        GROUP BY k.name
        ORDER BY popularity DESC
        LIMIT {top_n};
    """)

def get_all_keywords():
    return get_data("SELECT name FROM keyword ORDER BY name;")

# def get_keyword_trend(keywords):
#     formatted = ','.join(f"'{kw}'" for kw in keywords)
#     query = f"""
#         SELECT 
#             k.name AS keyword,
#             p.year,
#             COUNT(DISTINCT p.ID) AS publication_count
#         FROM publication_keyword pk
#         JOIN keyword k ON pk.keyword_id = k.id
#         JOIN publication p ON pk.publication_id = p.ID
#         WHERE k.name IN ({formatted})
#         GROUP BY k.name, p.year
#         ORDER BY k.name, p.year;
#     """
#     return get_data(query)

def get_top_faculty_by_keyword(selected_keyword):
    query = f"""
        SELECT f.id, f.name, f.photo_url, u.name AS university, f.position, f.research_interest, f.email, f.phone,
               SUM(p.num_citations) AS total_citations
        FROM faculty f
        JOIN faculty_publication fp ON f.id = fp.faculty_id
        JOIN publication p ON fp.publication_Id = p.ID
        JOIN publication_keyword pk ON p.ID = pk.publication_id
        JOIN keyword k ON pk.keyword_id = k.id
        JOIN university u ON f.university_id = u.id
        WHERE k.name = '{selected_keyword}'
        GROUP BY f.id
        ORDER BY total_citations DESC
        LIMIT 5;
    """
    return get_data(query)

def update_professor_photo(professor_id, photo_url):
    update_query = """
        UPDATE faculty
        SET photo_url = :photo_url
        WHERE id = :professor_id
    """
    with engine.connect() as connection:
        connection.execute(sa.text(update_query), {
            "photo_url": photo_url,
            "professor_id": professor_id
        })

def get_faculty_by_id(faculty_id):
    """Get faculty information by ID"""
    query = f"""
    SELECT f.id, f.name, f.position, f.email, f.phone, f.photo_url, 
           u.name as university
    FROM faculty f
    JOIN university u ON f.university_id = u.id
    WHERE f.id = {faculty_id}
    """
    
    result_df = get_data(query)
    if result_df.empty:
        return None
    return result_df.iloc[0].to_dict()

def get_mysql_connection():
    """Create and return a direct MySQL connection"""
    conn = sql.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name
    )
    return conn

def update_faculty_photo_url(faculty_id, new_photo_url):
    """Update the photo URL for a faculty member"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        query = "UPDATE faculty SET photo_url = %s WHERE id = %s"
        cursor.execute(query, (new_photo_url, faculty_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error updating faculty photo URL: {e}")
        return False