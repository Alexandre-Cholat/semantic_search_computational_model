
import os
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- Supabase API credentials
SUPABASE_URL = "https://ixccewdnndriahpkdahc.supabase.co"  
SUPABASE_KEY = "sb_publishable_jxcouowghJLOUQiEraDlAA_rxb8dkEc"     
BUCKET_NAME = "experiments"

# --- Create client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_csvs_to_supabase(local_directory: str):
    for filename in os.listdir(local_directory):
        if filename.endswith(".csv"):
            file_path = os.path.join(local_directory, filename)
            with open(file_path, "rb") as f:
                res = supabase.storage.from_(BUCKET_NAME).upload(filename, f)
                print(f"Uploaded {filename}: {res}")

def upload_file_to_supabase(file_path: str):
    """
    Uploads a specific CSV file to Supabase Storage and inserts metadata rows into the DB.
    """
    # --- Ensure file exists ---
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    # --- Upload to Supabase Storage ---
    file_name = os.path.basename(file_path)
    print(f"Uploading {file_name} to Supabase Storage...")

    with open(file_path, "rb") as f:
        res = supabase.storage.from_(BUCKET_NAME).upload(file_name, f)
    print(f"Upload result: {res}")

    # --- Read the CSV ---
    df = pd.read_csv(file_path)

    # --- Build table entries ---
    now = datetime.utcnow().isoformat()

    records = []
    for _, row in df.iterrows():
        records.append({
            "participant_number": int(row["participant_number"]),
            "target_word": str(row["target_word"]),
            "target_word_pos": int(row["target_word_pos"]),
            "position_time_pairs": str(row["position_time_pairs"]),
            "file-name": file_name,
        })

    # --- Insert into DB ---
    print(f"Inserting {len(records)} records into Supabase table...")
    res = supabase.table("experiments").insert(records).execute()
    print("Database insert result:", res)

    print(f"✅ Successfully uploaded and logged: {file_name}")
    
# Test upload function:
#upload_file_to_supabase("results/p112-135915.csv")
