from bson import ObjectId
import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["academicworld"]
publications_collection = db["publications"]
faculty_collection = db["faculty"]

faculty_collection.create_index("name")
publications_collection.create_index([("keywords.id", pymongo.ASCENDING)])

# Function to get all keywords
def get_all_keywords():
    keywords = publications_collection.aggregate([
        {"$unwind": "$keywords"},
        {"$group": {"_id": "$keywords.name"}},
        {"$sort": {"_id": 1}}
    ])
    return [{"label": kw["_id"], "value": kw["_id"]} for kw in keywords]


def get_universities_by_keyword(keyword):
    result = faculty_collection.aggregate([
        {"$unwind": "$keywords"},
        {"$match": {"keywords.name": keyword}},
        {"$group": {
            "_id": "$affiliation.name",
            "totalCitations": {"$sum": "$numCitations"},
            "facultyCount": {"$sum": 1}
        }},
        {"$sort": {"facultyCount": -1}},
        {"$limit": 50}
    ])
    return [{"university": r["_id"], "facultyCount": r["facultyCount"] } for r in result]


# Function to get top 5 publications based on keyword
def get_top_publications(keyword):
    result = publications_collection.aggregate([
        {"$unwind": "$keywords"},
        {"$match": {"keywords.name": keyword}},
        {"$sort": {"numCitations": -1}},
        {"$limit": 50},
        {"$project": {
            "_id": 0,
            "title": 1,
            "venue": 1,
            "year": 1,
            "numCitations": 1
        }}
    ])
    return list(result)

def get_publication_by_title(title):
    return publications_collection.find_one({"title": title})

def update_publication(pub_id, new_citations):
    # Only allow positive citation numbers
    if new_citations < 0:
        return False
    publications_collection.update_one(
        {"_id": ObjectId(pub_id)},
        {"$set": {"numCitations": new_citations}}
    )

def get_publication_by_id(id_str):
    # Convert string ID to ObjectId if it's not already an ObjectId
    if isinstance(id_str, str):
        id_obj = ObjectId(id_str)
    else:
        id_obj = id_str
    # Fetch publication using the ID
    return publications_collection.find_one({"_id": id_obj})

def get_publications_for_faculty(faculty_names):
    if faculty_names:
        faculty_list = []
        for name in faculty_names.split(','):
            name_parts = name.strip().split(' ')
            if len(name_parts) == 2:
                first_name, last_name = name_parts
                # Reformat to "Last, First" (e.g., "Agouris, Peggy")
                formatted_name = f"{last_name},{first_name}"
                faculty_list.append(formatted_name)

        
        result = faculty_collection.aggregate([
            {
                "$match": {
                    "name": {"$in": faculty_list}  
                }
            }
        ])
        
        # Convert result to a list and print it
        result_list = list(result)
        
        # if not result_list:
        #     print("No results found for the given faculty names.")

        if result_list:    
            result = faculty_collection.aggregate([
                {
                    "$match": {
                        "name": {"$in": faculty_list}
                    }
                },
                {
                    "$unwind": "$publications"
                },
                {
                    "$lookup": {
                        "from": "publications",
                        "localField": "publications",
                        "foreignField": "id",
                        "as": "pub_details"
                    }
                },
                {
                    "$unwind": "$pub_details"
                },
                # {
                #     "$sort": {"pub_details.year": -1}
                # },
                {
                    "$project": {
                        "faculty": "$name",
                        "year": "$pub_details.year",
                        "title": "$pub_details.title"
                        
                    }
                }
            ])
        
        return list(result)
    return []
        