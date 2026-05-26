import boto3
import pandas as pd
import io
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

SOURCE_BUCKET = 'manish-etl-raw-data'
DESTINATION_BUCKET = 'manish-etl-processed-data'

def lambda_handler(event, context):
    try:
        # Get the uploaded file name
        record = event['Records'][0]
        file_name = record['s3']['object']['key']
        
        logger.info(f"Processing file: {file_name}")
        
        # Read CSV from S3
        response = s3.get_object(Bucket=SOURCE_BUCKET, Key=file_name)
        df = pd.read_csv(io.BytesIO(response['Body'].read()))
        
        logger.info(f"Original shape: {df.shape}")
        
        # Clean: remove null rows
        df = df.dropna()
        
        # Transform: add processed_date column
        df['processed_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        logger.info(f"Processed shape: {df.shape}")
        
        # Save cleaned CSV to destination bucket
        output_buffer = io.StringIO()
        df.to_csv(output_buffer, index=False)
        
        output_key = f"processed_{file_name}"
        
        s3.put_object(
            Bucket=DESTINATION_BUCKET,
            Key=output_key,
            Body=output_buffer.getvalue()
        )
        
        logger.info(f"Successfully saved {output_key} to {DESTINATION_BUCKET}")
        
        return {
            'statusCode': 200,
            'body': f'ETL complete! {output_key} saved to {DESTINATION_BUCKET}'
        }
        
    except Exception as e:
        logger.error(f"ETL failed: {str(e)}")
        raise e