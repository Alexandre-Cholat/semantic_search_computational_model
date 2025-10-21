from google.cloud import storage
import os

# Replace with your bucket name


def upload_csvs_to_gcs(local_directory):
    bucket_name = "semantic-search-475516-experiment-data"
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    for filename in os.listdir(local_directory):
        if filename.endswith(".csv"):
            blob = bucket.blob(f"raw/{filename}")
            blob.upload_from_filename(os.path.join(local_directory, filename))
            print(f"Uploaded {filename} to GCS.")

upload_csvs_to_gcs("path/to/your/csvs")
