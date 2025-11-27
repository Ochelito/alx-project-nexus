from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")         
key = os.getenv("SUPABASE_ANON_KEY")    

supabase = create_client(url, key)

# Example: fetch all movies
movies = supabase.table("movies").select("*").execute()
print(movies.data)

# Insert a test movie
inserted = supabase.table("movies").insert({
    "title": "Inception",
    "description": "A mind-bending thriller by Christopher Nolan.",
    "release_year": 2010,
    "genre": "Sci-Fi"
}).execute()

print("Inserted:", inserted.data)
