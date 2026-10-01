"""
PySpark / Enterprise Distributed ETL Reference Pipeline
--------------------------------------------------------
This reference module demonstrates big-data ETL architecture using PySpark / Spark SQL
for Fortune 100 enterprise scale datasets (matching Java/Scala/Python big-data requirements in JD).

In production:
1. Data ingested from AWS S3 (s3a://...) or Kafka stream.
2. PySpark DataFrame transformations & Window functions applied.
3. Loaded into AWS Redshift / Snowflake / Delta Lake partitions.
"""

try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, when, to_date, row_number, round as spark_round
    from pyspark.sql.window import Window
    SPARK_AVAILABLE = True
except ImportError:
    SPARK_AVAILABLE = False


def run_spark_pipeline(s3_input_path="s3a://retailpulse-landing-zone/raw_orders.csv",
                       output_delta_path="s3a://retailpulse-lakehouse/fact_sales"):
    """
    Example PySpark ETL workflow for Fortune 100 enterprise scale processing.
    """
    if not SPARK_AVAILABLE:
        print("[Spark Reference] PySpark not installed in local env. Skipping execution.")
        return None

    spark = SparkSession.builder \
        .appName("RetailPulse-Enterprise-ETL") \
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
        .getOrCreate()

    # 1. Extract raw data from S3
    df_raw = spark.read.option("header", "true").csv(s3_input_path)

    # 2. Transform & Data Quality Filtering
    df_clean = df_raw.filter(col("quantity") > 0) \
                     .filter(col("unit_price") > 0) \
                     .withColumn("order_date", to_date(col("order_date"), "yyyy-MM-dd")) \
                     .withColumn("revenue", spark_round(col("quantity") * col("unit_price") * (1 - col("discount")), 2))

    # 3. Deduplication via Window Function (ROW_NUMBER)
    window_spec = Window.partitionBy("order_id", "product_id").orderBy(col("order_date").desc())
    df_dedup = df_clean.withColumn("row_num", row_number().over(window_spec)) \
                       .filter(col("row_num") == 1) \
                       .drop("row_num")

    # 4. Load into partitioned Delta Lake / Parquet table
    df_dedup.write.format("parquet").mode("overwrite").partitionBy("category").save(output_delta_path)
    print(f"[Spark Reference] Successfully written enterprise ETL to {output_delta_path}")
    return df_dedup


if __name__ == "__main__":
    run_spark_pipeline()
