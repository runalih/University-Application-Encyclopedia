from neo4j import GraphDatabase
import pandas as pd

uri = "bolt://localhost:7687"
username = "neo4j"
password = "123456789"

driver = GraphDatabase.driver(uri, auth=(username, password))

try:
    driver.verify_connectivity()
    print("Connection established successfully")
except Exception as e:
    print(f"Connection failed: {e}")


    
def get_keyword_trend(keywords):
    """
    Get the trend (publication count by year) for specified keywords
    
    Args:
        keywords (list): List of keywords to get trends for
    
    Returns:
        pandas.DataFrame: DataFrame with columns [year, keyword, publication_count]
    """
    results = []
    
    with driver.session(database="academicworld") as session:
        for keyword in keywords:
            # Query to find the num of publications by year
            query = """
            MATCH (k:KEYWORD {name: $keyword})<-[:LABEL_BY]-(p:PUBLICATION)
            WHERE p.year IS NOT NULL
            RETURN p.year AS year, $keyword AS keyword, COUNT(p) AS publication_count
            ORDER BY p.year
            """
            result = session.run(query, keyword=keyword)
            
            # Process results for this keyword
            for record in result:
                year = record["year"]
                keyword_name = record["keyword"]
                count = record["publication_count"]
                results.append({
                    "year": year,
                    "keyword": keyword_name,
                    "publication_count": count
                })
    
    df = pd.DataFrame(results)
    return df
