output "s3_bucket_names" {
  description = "Names of the created S3 buckets"
  value = {
    for k, v in aws_s3_bucket.data_lake_bucket : k => v.bucket
  }
}

output "glue_catalog_database_name" {
  description = "Name of the Glue catalog database"
  value       = aws_glue_catalog_database.data_catalog.name
}

output "athena_workgroup_name" {
  description = "Name of the Athena workgroup"
  value       = aws_athena_workgroup.main.name
}
