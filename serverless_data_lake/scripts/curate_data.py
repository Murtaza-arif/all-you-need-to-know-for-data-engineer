import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.functions import col, avg, count, sum, min, max, round

# Initialize Glue context
args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'raw_database',
    'raw_table',
    'curated_bucket'
])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read source data
employees_df = glueContext.create_dynamic_frame.from_catalog(
    database=args['raw_database'],
    table_name=args['raw_table'],
    push_down_predicate="partition_0 = 'employees'"
).toDF()

departments_df = glueContext.create_dynamic_frame.from_catalog(
    database=args['raw_database'],
    table_name=args['raw_table'],
    push_down_predicate="partition_0 = 'departments'"
).toDF()

# Create department summary
department_summary = departments_df.join(
    employees_df.groupBy('department').agg(
        count('*').alias('employee_count'),
        round(avg('salary'), 2).alias('avg_salary'),
        sum('salary').alias('total_salary_cost')
    ),
    departments_df.department_name == employees_df.department,
    'left'
).select(
    'department_name',
    'location',
    'budget',
    'employee_count',
    'avg_salary',
    'total_salary_cost',
    round((col('budget') - col('total_salary_cost')), 2).alias('budget_remaining'),
    round((col('total_salary_cost') / col('budget') * 100), 2).alias('budget_utilization_percent')
)

# Create employee summary
employee_summary = employees_df.join(
    departments_df,
    employees_df.department == departments_df.department_name
).select(
    'employee_id',
    'first_name',
    'last_name',
    'email',
    'department',
    'location',
    'salary',
    'hire_date'
)

# Convert to Glue DynamicFrames
department_summary_dynamic = DynamicFrame.fromDF(department_summary, glueContext, "department_summary")
employee_summary_dynamic = DynamicFrame.fromDF(employee_summary, glueContext, "employee_summary")

# Write curated data in Parquet format
glueContext.write_dynamic_frame.from_options(
    frame=department_summary_dynamic,
    connection_type="s3",
    connection_options={
        "path": f"s3://{args['curated_bucket']}/data/department_summary/",
        "partitionKeys": []
    },
    format="parquet"
)

glueContext.write_dynamic_frame.from_options(
    frame=employee_summary_dynamic,
    connection_type="s3",
    connection_options={
        "path": f"s3://{args['curated_bucket']}/data/employee_summary/",
        "partitionKeys": []
    },
    format="parquet"
)

job.commit()
