provider "aws" {
  region = var.aws_region
}

# S3 buckets for raw, cleaned, and curated data
resource "aws_s3_bucket" "data_lake_bucket" {
  for_each = toset(["raw", "cleaned", "curated"])
  bucket   = "${var.project_name}-${each.key}-${var.environment}"

  tags = {
    Environment = var.environment
    Layer      = each.key
  }
}

# Enable versioning for all buckets
resource "aws_s3_bucket_versioning" "bucket_versioning" {
  for_each = aws_s3_bucket.data_lake_bucket
  bucket   = each.value.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# Glue Catalog Database
resource "aws_glue_catalog_database" "data_catalog" {
  name = "${var.project_name}_catalog_${var.environment}"
}

# IAM role for Glue
resource "aws_iam_role" "glue_role" {
  name = "${var.project_name}-glue-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })
}

# Attach AWS managed policy for Glue
resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# S3 access policy for Glue
resource "aws_iam_role_policy" "glue_s3_policy" {
  name = "glue_s3_policy"
  role = aws_iam_role.glue_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = concat(
          [for bucket in aws_s3_bucket.data_lake_bucket : bucket.arn],
          [for bucket in aws_s3_bucket.data_lake_bucket : "${bucket.arn}/*"]
        )
      }
    ]
  })
}

# Athena Workgroup
resource "aws_athena_workgroup" "main" {
  name = "${var.project_name}_workgroup_${var.environment}"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.data_lake_bucket["curated"].bucket}/athena-results/"
    }
  }
}

# Lambda role for processing uploaded files
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-processor-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Lambda basic execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# S3 access policy for Lambda
resource "aws_iam_role_policy" "lambda_s3_policy" {
  name = "lambda_s3_policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_lake_bucket["raw"].arn,
          "${aws_s3_bucket.data_lake_bucket["raw"].arn}/*",
          aws_s3_bucket.data_lake_bucket["cleaned"].arn,
          "${aws_s3_bucket.data_lake_bucket["cleaned"].arn}/*"
        ]
      }
    ]
  })
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/aws/lambda/${var.project_name}-process-upload"
  retention_in_days = 14

  tags = {
    Environment = var.environment
    Function    = "process-upload"
  }
}

# Lambda function for processing uploaded files
resource "aws_lambda_function" "process_upload" {
  filename         = "lambda/process_upload.zip"
  function_name    = "${var.project_name}-process-upload"
  role            = aws_iam_role.lambda_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      CLEANED_BUCKET = aws_s3_bucket.data_lake_bucket["cleaned"].id
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda_log_group]
}

# S3 bucket notification for raw bucket
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.data_lake_bucket["raw"].id

  lambda_function {
    lambda_function_arn = aws_lambda_function.process_upload.arn
    events              = ["s3:ObjectCreated:*"]
  }
}

# Lambda permission to allow S3 to invoke the function
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.process_upload.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.data_lake_bucket["raw"].arn
}

# Glue Crawler IAM Role
resource "aws_iam_role" "glue_crawler_role" {
  name = "${var.project_name}-glue-crawler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })
}

# Attach AWS managed policy for Glue service
resource "aws_iam_role_policy_attachment" "glue_crawler_service" {
  role       = aws_iam_role.glue_crawler_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# S3 access policy for Glue Crawler
resource "aws_iam_role_policy" "glue_crawler_s3_policy" {
  name = "glue_crawler_s3_policy"
  role = aws_iam_role.glue_crawler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_lake_bucket["raw"].arn,
          "${aws_s3_bucket.data_lake_bucket["raw"].arn}/*"
        ]
      }
    ]
  })
}

# Glue Crawler for raw data
resource "aws_glue_crawler" "raw_data_crawler" {
  database_name = aws_glue_catalog_database.data_catalog.name
  name          = "${var.project_name}-raw-data-crawler"
  role          = aws_iam_role.glue_crawler_role.arn

  s3_target {
    path = "s3://${aws_s3_bucket.data_lake_bucket["raw"].id}"
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
    }
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
  })

  schedule = "cron(* * * * ? *)" # Run every minute
}

# Alternative approach: Let's use AWS Lambda to trigger the crawler instead
resource "aws_lambda_function" "trigger_crawler" {
  filename         = "lambda/trigger_crawler.zip"
  function_name    = "${var.project_name}-trigger-crawler"
  role            = aws_iam_role.lambda_crawler_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 60

  environment {
    variables = {
      CRAWLER_NAME = aws_glue_crawler.raw_data_crawler.name
    }
  }
}

# IAM role for the crawler trigger Lambda
resource "aws_iam_role" "lambda_crawler_role" {
  name = "${var.project_name}-lambda-crawler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Lambda permissions to start Glue crawler
resource "aws_iam_role_policy" "lambda_start_crawler" {
  name = "lambda_start_crawler"
  role = aws_iam_role.lambda_crawler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "glue:StartCrawler"
        ]
        Resource = [
          "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:crawler/${aws_glue_crawler.raw_data_crawler.name}"
        ]
      }
    ]
  })
}

# CloudWatch Logs policy for Lambda
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_crawler_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# EventBridge rule to trigger Lambda
resource "aws_cloudwatch_event_rule" "trigger_lambda" {
  name                = "${var.project_name}-trigger-lambda"
  description         = "Trigger Lambda to start Glue Crawler"
  schedule_expression = "rate(1 minute)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.trigger_lambda.name
  target_id = "TriggerCrawlerLambda"
  arn       = aws_lambda_function.trigger_crawler.arn
}

# Allow EventBridge to invoke Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.trigger_crawler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.trigger_lambda.arn
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# Glue ETL Job for curating data
resource "aws_glue_job" "curate_data" {
  name         = "${var.project_name}-curate-data"
  role_arn     = aws_iam_role.glue_role.arn
  glue_version = "4.0"
  
  command {
    script_location = "s3://${aws_s3_bucket.data_lake_bucket["curated"].id}/scripts/curate_data.py"
    python_version  = "3"
  }

  default_arguments = {
    "--enable-metrics"                = "true"
    "--enable-spark-ui"              = "true"
    "--spark-event-logs-path"        = "s3://${aws_s3_bucket.data_lake_bucket["curated"].id}/spark-logs/"
    "--enable-job-insights"          = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--job-language"                 = "python"
    "--TempDir"                      = "s3://${aws_s3_bucket.data_lake_bucket["curated"].id}/temporary/"
    "--job-bookmark-option"          = "job-bookmark-enable"
    
    "--raw_database"                 = aws_glue_catalog_database.data_catalog.name
    "--raw_table"                    = "demo_john_doe_data_lake_raw_dev"
    "--curated_bucket"               = aws_s3_bucket.data_lake_bucket["curated"].id
  }

  execution_property {
    max_concurrent_runs = 1
  }
}

# Create a new database for curated data
resource "aws_glue_catalog_database" "curated_catalog" {
  name = "${var.project_name}_curated_catalog_${var.environment}"
}

# Glue Crawler for curated data
resource "aws_glue_crawler" "curated_data_crawler" {
  name          = "${var.project_name}-curated-data-crawler"
  database_name = aws_glue_catalog_database.curated_catalog.name
  role          = aws_iam_role.glue_crawler_role.arn
  description   = "Crawler to catalog curated data in S3"

  s3_target {
    path = "s3://${aws_s3_bucket.data_lake_bucket["curated"].id}/data/"
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  configuration = jsonencode({
    Version = 1.0
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
  })
}

# EventBridge rule to trigger the Glue job after crawler completion
resource "aws_cloudwatch_event_rule" "trigger_curate_job" {
  name                = "${var.project_name}-trigger-curate-job"
  description         = "Trigger curate job when raw data crawler completes"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "curate_job_target" {
  rule      = aws_cloudwatch_event_rule.trigger_curate_job.name
  target_id = "TriggerCurateJob"
  arn       = aws_glue_job.curate_data.arn
  role_arn  = aws_iam_role.glue_role.arn
}

# Athena Named Queries
resource "aws_athena_named_query" "top_employees_by_salary" {
  name        = "${var.project_name}-top-employees-by-salary"
  description = "Lists top 5 employees by salary with their department information"
  database    = aws_glue_catalog_database.data_catalog.name
  workgroup   = aws_athena_workgroup.main.name
  query       = <<-EOT
    SELECT first_name, last_name, department, salary 
    FROM ${aws_glue_catalog_database.data_catalog.name}.demo_john_doe_data_lake_raw_dev 
    WHERE partition_0='employees' 
    ORDER BY salary DESC 
    LIMIT 5;
  EOT
}

resource "aws_athena_named_query" "employee_department_details" {
  name        = "${var.project_name}-employee-department-details"
  description = "Joins employee and department data to show detailed information"
  database    = aws_glue_catalog_database.data_catalog.name
  workgroup   = aws_athena_workgroup.main.name
  query       = <<-EOT
    SELECT 
      e.first_name, 
      e.last_name, 
      e.department, 
      d.department_name, 
      d.location, 
      e.salary 
    FROM ${aws_glue_catalog_database.data_catalog.name}.demo_john_doe_data_lake_raw_dev e 
    JOIN ${aws_glue_catalog_database.data_catalog.name}.demo_john_doe_data_lake_raw_dev d 
      ON e.department = d.department_name 
    WHERE e.partition_0='employees' 
      AND d.partition_0='departments' 
    ORDER BY e.salary DESC 
    LIMIT 5;
  EOT
}

resource "aws_athena_named_query" "department_budgets" {
  name        = "${var.project_name}-department-budgets"
  description = "Shows department budgets and locations sorted by budget"
  database    = aws_glue_catalog_database.data_catalog.name
  workgroup   = aws_athena_workgroup.main.name
  query       = <<-EOT
    SELECT department_name, location, budget 
    FROM ${aws_glue_catalog_database.data_catalog.name}.demo_john_doe_data_lake_raw_dev 
    WHERE partition_0='departments' 
    ORDER BY budget DESC;
  EOT
}

resource "aws_athena_named_query" "department_salary_stats" {
  name        = "${var.project_name}-department-salary-stats"
  description = "Calculates salary statistics by department"
  database    = aws_glue_catalog_database.data_catalog.name
  workgroup   = aws_athena_workgroup.main.name
  query       = <<-EOT
    SELECT 
      e.department,
      d.location,
      COUNT(*) as employee_count,
      AVG(e.salary) as avg_salary,
      MIN(e.salary) as min_salary,
      MAX(e.salary) as max_salary,
      SUM(e.salary) as total_salary_cost,
      d.budget,
      (d.budget - SUM(e.salary)) as budget_remaining
    FROM ${aws_glue_catalog_database.data_catalog.name}.demo_john_doe_data_lake_raw_dev e
    JOIN ${aws_glue_catalog_database.data_catalog.name}.demo_john_doe_data_lake_raw_dev d
      ON e.department = d.department_name
    WHERE e.partition_0='employees'
      AND d.partition_0='departments'
    GROUP BY e.department, d.location, d.budget
    ORDER BY total_salary_cost DESC;
  EOT
}
