/*
    Example dbt model for Silver Layer transformation
    This demonstrates a typical bronze -> silver transformation with data quality
*/

{{
  config(
    materialized='incremental',
    unique_key='customer_id',
    on_schema_change='sync_all_columns',
    tags=['silver', 'customers']
  )
}}

WITH bronze_customers AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id 
            ORDER BY ingestion_timestamp DESC
        ) AS row_num
    FROM {{ source('bronze', 'customers') }}
    
    {% if is_incremental() %}
        WHERE ingestion_timestamp > (SELECT MAX(processed_timestamp) FROM {{ this }})
    {% endif %}
),

deduplicated AS (
    SELECT
        customer_id,
        customer_name,
        email,
        phone,
        address,
        city,
        state,
        country,
        postal_code,
        registration_date,
        status,
        source_system,
        ingestion_timestamp
    FROM bronze_customers
    WHERE row_num = 1
),

cleaned AS (
    SELECT
        customer_id,
        TRIM(UPPER(customer_name)) AS customer_name,
        LOWER(TRIM(email)) AS email,
        REGEXP_REPLACE(phone, '[^0-9]', '') AS phone_normalized,
        TRIM(address) AS address,
        TRIM(city) AS city,
        UPPER(TRIM(state)) AS state,
        UPPER(TRIM(country)) AS country,
        postal_code,
        registration_date,
        CASE 
            WHEN status IN ('active', 'inactive', 'suspended') THEN status
            ELSE 'unknown'
        END AS status,
        source_system,
        ingestion_timestamp,
        CURRENT_TIMESTAMP() AS processed_timestamp,
        
        -- Data quality flags
        CASE 
            WHEN email IS NULL OR email = '' THEN 1 
            ELSE 0 
        END AS missing_email_flag,
        
        CASE 
            WHEN email NOT LIKE '%@%' THEN 1 
            ELSE 0 
        END AS invalid_email_flag,
        
        CASE 
            WHEN phone IS NULL OR LENGTH(REGEXP_REPLACE(phone, '[^0-9]', '')) < 10 THEN 1 
            ELSE 0 
        END AS invalid_phone_flag
        
    FROM deduplicated
    WHERE 
        customer_id IS NOT NULL
        AND customer_name IS NOT NULL
)

SELECT * FROM cleaned
