# Local Lakehouse Setup Runbook

**Complete guide for setting up a free, open-source lakehouse running entirely locally (no cloud required) for datasets under 100 GB**

## 🎯 Overview

This runbook provides step-by-step instructions to set up a fully functional lakehouse on your local machine using only free, open-source tools. Perfect for:

- Learning lakehouse architecture
- Development and testing
- Small-scale data projects (<100 GB)
- Privacy-sensitive use cases requiring local-only data processing
- Cost-conscious projects avoiding cloud expenses

## 📋 Prerequisites

### System Requirements

- **OS**: Linux, macOS, or Windows (with WSL2 recommended)
- **RAM**: 8 GB minimum, 16 GB recommended
- **Storage**: 150 GB free space (50 GB for tools + 100 GB for data)
- **CPU**: 4 cores minimum, 8+ cores recommended

### Software Requirements

- Docker Desktop (or Docker Engine + Docker Compose)
- Python 3.8 or higher
- Git
- Text editor (VS Code, vim, etc.)

## 🏗️ Architecture Stack

This runbook uses the following **100% free and open-source** tools:

| Component | Tool | Purpose |
|-----------|------|---------|
| **Data Processing** | DuckDB | Lightweight analytical database (no server needed) |
| **Storage Format** | Parquet | Columnar storage format |
| **Object Storage** | MinIO | S3-compatible local object storage |
| **Orchestration** | Python scripts | Simple, dependency-free orchestration |
| **Metadata/Catalog** | Unity Catalog (local) | Data governance and lineage |
| **Monitoring** | Prometheus + Grafana | Metrics and dashboards |
| **Notebooks** | Jupyter | Interactive data exploration |

## 📖 Step-by-Step Setup

### Step 1: Clone the Repository

```bash
# Clone the lakehouse template
git clone https://github.com/towenwolf/lakehouse-template.git
cd lakehouse-template

# Create a working directory for your local lakehouse
mkdir -p ~/local-lakehouse
cd ~/local-lakehouse
```

### Step 2: Set Up Directory Structure

```bash
# Create data directories
mkdir -p data/{bronze,silver,gold,raw}
mkdir -p data/minio-storage
mkdir -p logs
mkdir -p notebooks
mkdir -p config

# Set permissions
chmod -R 755 data/ logs/ notebooks/

echo "✓ Directory structure created"
```

### Step 3: Install Python Dependencies

```bash
# Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install core dependencies (all free and open-source)
pip install --upgrade pip
pip install duckdb pandas pyarrow jupyter prometheus-client pyyaml

# Verify installations
python3 -c "import duckdb; print(f'DuckDB version: {duckdb.__version__}')"
python3 -c "import pandas; print(f'Pandas version: {pandas.__version__}')"
python3 -c "import pyarrow; print(f'PyArrow version: {pyarrow.__version__}')"

echo "✓ Python dependencies installed"
```

### Step 4: Set Up Local Object Storage (MinIO)

Create a `docker-compose-local.yml` file:

```bash
cat > docker-compose-local.yml << 'EOF'
version: '3.8'

services:
  # MinIO - S3-compatible local object storage
  minio:
    image: minio/minio:latest
    container_name: local-lakehouse-minio
    ports:
      - "9000:9000"      # API endpoint
      - "9001:9001"      # Web Console
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - ./data/minio-storage:/data
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  # Prometheus - Metrics collection
  prometheus:
    image: prom/prometheus:latest
    container_name: local-lakehouse-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  # Grafana - Visualization
  grafana:
    image: grafana/grafana:latest
    container_name: local-lakehouse-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus

  # Jupyter - Interactive notebooks
  jupyter:
    image: jupyter/datascience-notebook:latest
    container_name: local-lakehouse-jupyter
    ports:
      - "8888:8888"
    environment:
      JUPYTER_ENABLE_LAB: "yes"
      JUPYTER_TOKEN: "lakehouse"
    volumes:
      - ./notebooks:/home/jovyan/work
      - ./data:/home/jovyan/data
      - ./pipelines:/home/jovyan/pipelines

volumes:
  prometheus_data:
  grafana_data:

networks:
  default:
    name: local-lakehouse-network
EOF

echo "✓ Docker Compose configuration created"
```

Create a minimal Prometheus configuration:

```bash
mkdir -p config

cat > config/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'lakehouse-metrics'
    static_configs:
      - targets: ['host.docker.internal:8000']
EOF

echo "✓ Prometheus configuration created"
```

### Step 5: Start the Local Infrastructure

```bash
# Start all services
docker-compose -f docker-compose-local.yml up -d

# Wait for services to be ready
sleep 10

# Check status
docker-compose -f docker-compose-local.yml ps

# Verify MinIO is accessible
curl -I http://localhost:9001

echo "✓ Infrastructure services started"
```

**Access Points:**
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- Jupyter: http://localhost:8888 (token: lakehouse)

### Step 6: Configure MinIO Buckets

```bash
# Install MinIO client (optional, for CLI management)
# On Linux:
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
sudo mv mc /usr/local/bin/

# On macOS:
# brew install minio/stable/mc

# Configure MinIO client
mc alias set local http://localhost:9000 minioadmin minioadmin

# Create buckets for each layer
mc mb local/bronze
mc mb local/silver
mc mb local/gold

# Verify buckets
mc ls local

echo "✓ MinIO buckets created"
```

Alternatively, use the MinIO web console (http://localhost:9001) to create buckets manually.

### Step 7: Copy the Governance Module

```bash
# Copy the Unity Catalog governance module from the template
cp -r ../lakehouse-template/governance ./
cp -r ../lakehouse-template/pipelines ./

echo "✓ Governance and pipeline modules copied"
```

### Step 8: Create a Local Lakehouse Pipeline Using DuckDB

Create `pipelines/local_duckdb_pipeline.py`:

```bash
cat > pipelines/local_duckdb_pipeline.py << 'EOF'
"""
Local Lakehouse Pipeline using DuckDB
A lightweight, serverless pipeline for local data processing
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime
import json


class LocalDuckDBPipeline:
    """Lakehouse pipeline using DuckDB for local processing"""
    
    def __init__(self, base_path="data"):
        self.base_path = Path(base_path)
        self.bronze_path = self.base_path / "bronze"
        self.silver_path = self.base_path / "silver"
        self.gold_path = self.base_path / "gold"
        
        # Ensure directories exist
        for path in [self.bronze_path, self.silver_path, self.gold_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Initialize DuckDB connection (in-memory, can persist if needed)
        self.conn = duckdb.connect(database=':memory:')
        
    def ingest_to_bronze(self, source_file, table_name):
        """Ingest raw CSV data to bronze layer as Parquet"""
        print(f"[BRONZE] Ingesting {source_file} -> {table_name}")
        
        # Read CSV with DuckDB
        df = self.conn.execute(f"""
            SELECT *, 
                   '{datetime.now().isoformat()}' as _ingestion_timestamp,
                   '{source_file}' as _source_file
            FROM read_csv_auto('{source_file}')
        """).df()
        
        # Write to Parquet in bronze layer
        output_path = self.bronze_path / f"{table_name}.parquet"
        df.to_parquet(output_path, index=False)
        
        print(f"[BRONZE] ✓ Ingested {len(df)} records to {output_path}")
        return output_path
    
    def transform_to_silver(self, table_name):
        """Transform bronze data to silver layer with cleaning"""
        print(f"[SILVER] Transforming {table_name}")
        
        bronze_path = self.bronze_path / f"{table_name}.parquet"
        
        # Read from bronze and apply transformations
        df = self.conn.execute(f"""
            SELECT DISTINCT *
            FROM read_parquet('{bronze_path}')
            WHERE 1=1  -- Add your data quality filters here
        """).df()
        
        # Additional cleaning (example)
        df = df.dropna()  # Remove rows with any null values
        
        # Write to silver layer
        output_path = self.silver_path / f"{table_name}.parquet"
        df.to_parquet(output_path, index=False)
        
        print(f"[SILVER] ✓ Processed {len(df)} clean records to {output_path}")
        return output_path
    
    def aggregate_to_gold(self, table_name, group_by_col, agg_name):
        """Aggregate silver data to gold layer"""
        print(f"[GOLD] Aggregating {table_name} by {group_by_col}")
        
        silver_path = self.silver_path / f"{table_name}.parquet"
        
        # Perform aggregation
        df = self.conn.execute(f"""
            SELECT 
                {group_by_col},
                COUNT(*) as total_count,
                '{datetime.now().isoformat()}' as _computed_timestamp
            FROM read_parquet('{silver_path}')
            GROUP BY {group_by_col}
            ORDER BY total_count DESC
        """).df()
        
        # Write to gold layer
        output_path = self.gold_path / f"{agg_name}.parquet"
        df.to_parquet(output_path, index=False)
        
        print(f"[GOLD] ✓ Created {len(df)} aggregates in {output_path}")
        return output_path
    
    def query_gold(self, table_name):
        """Query data from gold layer"""
        gold_path = self.gold_path / f"{table_name}.parquet"
        return self.conn.execute(f"SELECT * FROM read_parquet('{gold_path}')").df()
    
    def close(self):
        """Close DuckDB connection"""
        self.conn.close()


if __name__ == "__main__":
    print("="*70)
    print("Local Lakehouse Pipeline with DuckDB")
    print("="*70)
    
    # Initialize pipeline
    pipeline = LocalDuckDBPipeline()
    
    # Example: Process customer data
    # Create sample data first
    sample_data_path = Path("data/raw/sample_customers.csv")
    sample_data_path.parent.mkdir(exist_ok=True)
    
    if not sample_data_path.exists():
        # Create sample data
        import csv
        with open(sample_data_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['customer_id', 'name', 'email', 'region', 'signup_date'])
            writer.writerows([
                [1, 'Alice Johnson', 'alice@example.com', 'North', '2024-01-15'],
                [2, 'Bob Smith', 'bob@example.com', 'South', '2024-01-16'],
                [3, 'Carol White', 'carol@example.com', 'East', '2024-01-17'],
                [4, 'David Brown', 'david@example.com', 'North', '2024-01-18'],
                [5, 'Eve Davis', 'eve@example.com', 'West', '2024-01-19'],
                [6, 'Frank Miller', 'frank@example.com', 'South', '2024-01-20'],
                [7, 'Grace Wilson', 'grace@example.com', 'North', '2024-01-21'],
                [8, 'Henry Moore', 'henry@example.com', 'East', '2024-01-22'],
            ])
        print(f"Created sample data at {sample_data_path}")
    
    # Run the pipeline
    try:
        # Bronze layer
        pipeline.ingest_to_bronze("data/raw/sample_customers.csv", "customers")
        
        # Silver layer
        pipeline.transform_to_silver("customers")
        
        # Gold layer
        pipeline.aggregate_to_gold("customers", "region", "customers_by_region")
        
        # Query results
        print("\n" + "="*70)
        print("GOLD LAYER RESULTS")
        print("="*70)
        results = pipeline.query_gold("customers_by_region")
        print(results)
        
        print("\n" + "="*70)
        print("✓ Pipeline completed successfully!")
        print("="*70)
        
    finally:
        pipeline.close()
EOF

echo "✓ DuckDB pipeline created"
```

### Step 9: Run Your First Local Pipeline

```bash
# Activate virtual environment if not already active
source venv/bin/activate

# Run the pipeline
python3 pipelines/local_duckdb_pipeline.py

# Verify the results
ls -lh data/bronze/
ls -lh data/silver/
ls -lh data/gold/

echo "✓ First pipeline executed successfully"
```

### Step 10: Set Up Governance with Unity Catalog

```bash
# Run the governed pipeline (uses the Unity Catalog from the template)
python3 pipelines/governed_pipeline.py

# Explore the catalog
python3 governance/catalog_cli.py summary
python3 governance/catalog_cli.py describe silver customers
python3 governance/catalog_cli.py lineage gold customers_by_region

echo "✓ Governance tracking enabled"
```

### Step 11: Create a Jupyter Notebook for Interactive Analysis

Create `notebooks/lakehouse_analysis.ipynb` (or use Jupyter web interface):

Access Jupyter at http://localhost:8888 (token: lakehouse) and create a new notebook with:

```python
# Lakehouse Analysis Notebook
import duckdb
import pandas as pd
import matplotlib.pyplot as plt

# Connect to DuckDB
conn = duckdb.connect(database=':memory:')

# Query gold layer data
df = conn.execute("""
    SELECT * FROM read_parquet('/home/jovyan/data/gold/customers_by_region.parquet')
""").df()

# Display results
print("Customer Distribution by Region:")
print(df)

# Visualize
df.plot(x='region', y='total_count', kind='bar', title='Customers by Region')
plt.ylabel('Number of Customers')
plt.tight_layout()
plt.show()

conn.close()
```

### Step 12: Add Data Quality Monitoring

Create `pipelines/data_quality_check.py`:

```bash
cat > pipelines/data_quality_check.py << 'EOF'
"""
Data Quality Monitoring for Local Lakehouse
"""

import duckdb
from pathlib import Path
from datetime import datetime
import json


def check_data_quality(layer, table_name, base_path="data"):
    """Run data quality checks on a specific table"""
    
    conn = duckdb.connect(database=':memory:')
    file_path = Path(base_path) / layer / f"{table_name}.parquet"
    
    if not file_path.exists():
        print(f"✗ Table {table_name} not found in {layer} layer")
        return None
    
    # Run quality checks
    results = {
        'layer': layer,
        'table': table_name,
        'timestamp': datetime.now().isoformat(),
        'checks': {}
    }
    
    # Row count
    row_count = conn.execute(f"SELECT COUNT(*) FROM read_parquet('{file_path}')").fetchone()[0]
    results['checks']['row_count'] = row_count
    
    # Null checks
    columns = conn.execute(f"DESCRIBE SELECT * FROM read_parquet('{file_path}')").df()
    for col in columns['column_name']:
        null_count = conn.execute(f"""
            SELECT COUNT(*) FROM read_parquet('{file_path}') WHERE {col} IS NULL
        """).fetchone()[0]
        results['checks'][f'{col}_nulls'] = null_count
    
    # File size
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    results['checks']['file_size_mb'] = round(file_size_mb, 2)
    
    conn.close()
    
    # Print results
    print(f"\n{'='*60}")
    print(f"Data Quality Report: {layer}.{table_name}")
    print(f"{'='*60}")
    print(f"Total Rows: {row_count}")
    print(f"File Size: {file_size_mb:.2f} MB")
    print(f"\nNull Counts:")
    for key, value in results['checks'].items():
        if key.endswith('_nulls'):
            col_name = key.replace('_nulls', '')
            print(f"  {col_name}: {value}")
    print(f"{'='*60}\n")
    
    return results


if __name__ == "__main__":
    # Check quality of all layers
    layers = ['bronze', 'silver', 'gold']
    
    for layer in layers:
        layer_path = Path("data") / layer
        if layer_path.exists():
            for parquet_file in layer_path.glob("*.parquet"):
                table_name = parquet_file.stem
                check_data_quality(layer, table_name)
EOF

echo "✓ Data quality monitoring script created"
```

Run the quality checks:

```bash
python3 pipelines/data_quality_check.py
```

## 🔧 Configuration and Optimization

### DuckDB Configuration for Better Performance

Create `config/duckdb_config.py`:

```python
import duckdb

def get_optimized_connection():
    """Get a DuckDB connection with optimized settings"""
    conn = duckdb.connect(database=':memory:')
    
    # Set memory limit (adjust based on your system)
    conn.execute("SET memory_limit='4GB'")
    
    # Set thread count (adjust based on your CPU cores)
    conn.execute("SET threads=4")
    
    # Enable query progress
    conn.execute("SET enable_progress_bar=true")
    
    return conn
```

### Data Retention Policy

Create `scripts/cleanup_old_data.sh`:

```bash
cat > scripts/cleanup_old_data.sh << 'EOF'
#!/bin/bash
# Cleanup old data files (keep last 30 days)

BASE_PATH="data"
DAYS_TO_KEEP=30

echo "Cleaning up data older than ${DAYS_TO_KEEP} days..."

# Find and remove old files
find ${BASE_PATH}/bronze -name "*.parquet" -mtime +${DAYS_TO_KEEP} -delete
find ${BASE_PATH}/silver -name "*.parquet" -mtime +${DAYS_TO_KEEP} -delete
find ${BASE_PATH}/gold -name "*.parquet" -mtime +${DAYS_TO_KEEP} -delete

echo "✓ Cleanup completed"
EOF

chmod +x scripts/cleanup_old_data.sh
```

## 📊 Monitoring and Observability

### Export Metrics to Prometheus

Create `pipelines/metrics_exporter.py`:

```bash
cat > pipelines/metrics_exporter.py << 'EOF'
"""
Prometheus metrics exporter for lakehouse pipelines
"""

from prometheus_client import start_http_server, Counter, Gauge, Histogram
import time
from pathlib import Path

# Define metrics
records_processed = Counter(
    'lakehouse_records_processed_total',
    'Total number of records processed',
    ['layer', 'table']
)

layer_file_size = Gauge(
    'lakehouse_layer_file_size_bytes',
    'File size in bytes',
    ['layer', 'table']
)

processing_duration = Histogram(
    'lakehouse_processing_duration_seconds',
    'Time spent processing data',
    ['layer', 'operation']
)


def update_metrics(base_path="data"):
    """Update metrics from current data state"""
    for layer in ['bronze', 'silver', 'gold']:
        layer_path = Path(base_path) / layer
        if layer_path.exists():
            for file in layer_path.glob("*.parquet"):
                table_name = file.stem
                file_size = file.stat().st_size
                layer_file_size.labels(layer=layer, table=table_name).set(file_size)


if __name__ == "__main__":
    # Start metrics server on port 8000
    start_http_server(8000)
    print("Metrics server started on http://localhost:8000")
    
    # Update metrics every 30 seconds
    while True:
        update_metrics()
        time.sleep(30)
EOF
```

Run the metrics exporter in the background:

```bash
# In a separate terminal or use tmux/screen
source venv/bin/activate
python3 pipelines/metrics_exporter.py &
```

## 🚀 Advanced Use Cases

### Incremental Data Processing

Create `pipelines/incremental_pipeline.py`:

```python
"""
Incremental processing pipeline using DuckDB
Only processes new data since last run
"""

import duckdb
from pathlib import Path
from datetime import datetime
import json


class IncrementalPipeline:
    def __init__(self, base_path="data"):
        self.base_path = Path(base_path)
        self.state_file = self.base_path / "pipeline_state.json"
        self.conn = duckdb.connect(database=':memory:')
    
    def get_last_processed_timestamp(self, table_name):
        """Get the last processed timestamp for a table"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                return state.get(table_name, '1970-01-01T00:00:00')
        return '1970-01-01T00:00:00'
    
    def update_processed_timestamp(self, table_name, timestamp):
        """Update the last processed timestamp"""
        state = {}
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                state = json.load(f)
        
        state[table_name] = timestamp
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def process_incremental(self, table_name):
        """Process only new records since last run"""
        last_timestamp = self.get_last_processed_timestamp(table_name)
        current_timestamp = datetime.now().isoformat()
        
        bronze_path = self.base_path / "bronze" / f"{table_name}.parquet"
        silver_path = self.base_path / "silver" / f"{table_name}.parquet"
        
        # Read only new records
        new_records = self.conn.execute(f"""
            SELECT *
            FROM read_parquet('{bronze_path}')
            WHERE _ingestion_timestamp > '{last_timestamp}'
        """).df()
        
        if len(new_records) > 0:
            print(f"Processing {len(new_records)} new records...")
            
            # Append to silver layer
            if silver_path.exists():
                existing_df = self.conn.execute(f"""
                    SELECT * FROM read_parquet('{silver_path}')
                """).df()
                combined_df = pd.concat([existing_df, new_records])
            else:
                combined_df = new_records
            
            combined_df.to_parquet(silver_path, index=False)
            self.update_processed_timestamp(table_name, current_timestamp)
            print(f"✓ Processed and appended {len(new_records)} records")
        else:
            print("No new records to process")
    
    def close(self):
        self.conn.close()
```

### Query Optimization Tips

```python
# Use columnar filtering in DuckDB for better performance
df = conn.execute("""
    SELECT col1, col2  -- Only select needed columns
    FROM read_parquet('data/silver/large_table.parquet')
    WHERE date >= '2024-01-01'  -- Push down filters
    LIMIT 1000  -- Limit results when testing
""").df()

# Use partitioning for large datasets
# Partition by date/region for better performance
df.to_parquet('data/gold/sales.parquet', partition_cols=['region', 'date'])
```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. Out of Memory Errors

```bash
# Reduce DuckDB memory limit
conn.execute("SET memory_limit='2GB'")

# Process data in chunks
chunk_size = 10000
for chunk in pd.read_csv('large_file.csv', chunksize=chunk_size):
    process_chunk(chunk)
```

#### 2. Docker Container Issues

```bash
# Check container logs
docker-compose -f docker-compose-local.yml logs minio
docker-compose -f docker-compose-local.yml logs prometheus

# Restart services
docker-compose -f docker-compose-local.yml restart

# Clean up and restart
docker-compose -f docker-compose-local.yml down
docker-compose -f docker-compose-local.yml up -d
```

#### 3. Disk Space Issues

```bash
# Check disk usage
du -sh data/*

# Run cleanup script
./scripts/cleanup_old_data.sh

# Compress old data
gzip data/bronze/*.parquet
```

#### 4. Performance Issues

```bash
# Monitor system resources
htop  # or top on macOS

# Check DuckDB query plan
conn.execute("EXPLAIN SELECT * FROM ...").show()

# Add indexes (if using persistent DuckDB)
conn.execute("CREATE INDEX idx_date ON my_table(date)")
```

## 📈 Scaling Considerations

### When to Consider Upgrading

Your local lakehouse should work well for datasets under 100 GB. Consider upgrading if:

- Data volume exceeds 100 GB consistently
- Processing time becomes unacceptable (>1 hour)
- Need for concurrent users/queries increases
- Require high availability and disaster recovery
- Need advanced features like streaming

### Migration Path

1. **Local → Local Cluster**: Add more machines with distributed DuckDB
2. **Local → Cloud Hybrid**: Use MinIO as S3 gateway to cloud
3. **Local → Full Cloud**: Migrate to Databricks, Snowflake, or cloud lakehouse

## 🧪 Testing Your Setup

Run the complete test suite:

```bash
# Test basic pipeline
python3 pipelines/local_duckdb_pipeline.py

# Test data quality
python3 pipelines/data_quality_check.py

# Test governance
python3 pipelines/governed_pipeline.py
python3 governance/catalog_cli.py summary

# Verify monitoring
curl http://localhost:8000  # Metrics endpoint
curl http://localhost:9090  # Prometheus
curl http://localhost:3000  # Grafana

echo "✓ All tests passed!"
```

## 📚 Additional Resources

### DuckDB Resources
- [DuckDB Documentation](https://duckdb.org/docs/)
- [DuckDB SQL Reference](https://duckdb.org/docs/sql/introduction)
- [DuckDB Performance Guide](https://duckdb.org/docs/guides/performance/overview)

### MinIO Resources
- [MinIO Documentation](https://min.io/docs/minio/linux/index.html)
- [MinIO Client Guide](https://min.io/docs/minio/linux/reference/minio-mc.html)

### Parquet Resources
- [Apache Parquet Documentation](https://parquet.apache.org/docs/)
- [Parquet Performance Best Practices](https://parquet.apache.org/docs/file-format/configurations/)

## 📝 Checklist

Use this checklist to track your setup progress:

- [ ] System requirements verified
- [ ] Docker installed and running
- [ ] Python 3.8+ installed
- [ ] Directory structure created
- [ ] Python dependencies installed
- [ ] Docker Compose services started
- [ ] MinIO buckets created
- [ ] Sample pipeline executed successfully
- [ ] Governance tracking tested
- [ ] Jupyter notebook created
- [ ] Monitoring dashboards accessible
- [ ] Data quality checks running
- [ ] Metrics exporter configured
- [ ] Backup strategy documented

## 🎉 Next Steps

Congratulations! You now have a fully functional local lakehouse. Here's what to do next:

1. **Start Small**: Begin with a simple dataset and run it through Bronze → Silver → Gold
2. **Explore Jupyter**: Use notebooks for interactive data exploration
3. **Monitor Everything**: Check Grafana dashboards regularly
4. **Iterate**: Improve data quality rules and transformations
5. **Document**: Keep your data dictionary and pipeline docs up to date
6. **Learn**: Study DuckDB query optimization and Parquet best practices
7. **Share**: Share your lakehouse setup with your team

## 💡 Tips for Success

1. **Start Simple**: Don't over-engineer. Begin with basic pipelines and add complexity as needed.
2. **Monitor Early**: Set up monitoring from day one to understand your data patterns.
3. **Version Control**: Keep all scripts and configurations in Git.
4. **Document Everything**: Future you will thank present you for good documentation.
5. **Test Incrementally**: Test each layer (Bronze → Silver → Gold) independently.
6. **Backup Regularly**: Even local data needs backups. Use MinIO versioning or external drives.
7. **Stay Organized**: Use consistent naming conventions and directory structures.

## 🔐 Security Considerations

Even for local setups:

1. **Change Default Passwords**: Update MinIO, Grafana credentials immediately
2. **Use Environment Variables**: Never hardcode credentials in scripts
3. **Restrict Network Access**: Use firewall rules if exposing services
4. **Encrypt Sensitive Data**: Use encryption for PII even locally
5. **Regular Updates**: Keep Docker images and Python packages updated

## 🆘 Getting Help

If you run into issues:

1. Check the troubleshooting section above
2. Review Docker and DuckDB logs
3. Search DuckDB GitHub issues
4. Ask on the lakehouse-template GitHub discussions
5. Consult the official documentation for each tool

---

**Built with ❤️ using 100% free and open-source tools**

Happy data engineering! 🚀
