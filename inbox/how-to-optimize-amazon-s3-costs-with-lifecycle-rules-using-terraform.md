---
title: "How to Optimize Amazon S3 Costs with Lifecycle Rules Using Terraform"
source: "https://aws.plainenglish.io/how-to-optimize-amazon-s3-costs-with-lifecycle-rules-using-terraform-ee7e36796441"
author:
  - "[[Qolbi Nurwandi]]"
published: 2026-01-03
created: 2026-02-26
description: "Learn how to optimize Amazon S3 costs using lifecycle rules and Terraform. Automate storage transitions, retention policies, and governance at scale."
tags:
  - "clippings"
---
> [!summary]
> A practical guide to automating S3 cost optimization using Terraform lifecycle rules that transition objects through storage tiers (Standard → Standard-IA → Glacier IR → Deep Archive → Delete). It presents a modular Terraform setup with built-in validations for managing retention policies across multiple environments, including cleanup of incomplete multipart uploads and noncurrent object versions.

[Sitemap](https://aws.plainenglish.io/sitemap/sitemap.xml)

Get unlimited access to the best of Medium for less than $1/week.[Become a member](https://medium.com/plans?source=upgrade_membership---post_top_nav_upsell-----------------------------------------)

[

Become a member

](https://medium.com/plans?source=upgrade_membership---post_top_nav_upsell-----------------------------------------)## [AWS in Plain English](https://aws.plainenglish.io/?source=post_page---publication_nav-35e7a49c6df5-ee7e36796441---------------------------------------)

[![AWS in Plain English](https://miro.medium.com/v2/resize:fill:76:76/1*6EeD87OMwKk-u3ncwAOhog.png)](https://aws.plainenglish.io/?source=post_page---post_publication_sidebar-35e7a49c6df5-ee7e36796441---------------------------------------)

New AWS, Cloud, and DevOps content every day. Follow to join our 3.5M+ monthly readers.

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*UTk_U3iT5dPh1--rtf5aMQ.png)

> **Prerequisites:** This guide assumes you’re familiar with Terraform basics, AWS CLI, and it is written for engineers managing production AWS environments at scale.

Most developers think creating an S3 bucket is the end of the story. Click “Create,” upload files, done. But here’s the uncomfortable truth: **your S3 bucket is silently draining your AWS budget** every single month.

In this article, I’ll show how I standardize S3 lifecycle management across multiple environments using Terraform, covering cost optimization, compliance, and guardrails that prevent costly mistakes.

## The Hidden Cost of “Set and Forget”

When you create an S3 bucket and start uploading files, everything sits in **S3 Standard** storage class by default. This is AWS’s most expensive tier, designed for frequently accessed data. But here’s the reality:

- Your application logs from 3 months ago? Probably never accessed again.
- That backup from last year? Sitting there, costing you money every day.
- Failed multipart uploads? Still consuming storage and billing.

**AWS won’t automatically optimize this for you.**

> [“When you add a Lifecycle configuration to a bucket, the configuration rules apply to both existing objects and objects that you add later. For example, if you add a Lifecycle configuration rule today with an expiration action that causes objects to expire 30 days after creation, Amazon S3 will queue for removal any existing objects that are more than 30 days old.](https://arc.net/l/quote/impkscgb)”

The key phrase here: **“when you add”,** meaning it doesn’t happen automatically. You need to be proactive.

## The Pro Approach: Lifecycle Rules

AWS explicitly recognizes common data management patterns:

> [“With S3 Lifecycle configuration rules you can tell Amazon S3 to transition objects to less-expensive storage classes, archive or delete them. For example:](https://arc.net/l/quote/mrziypdv)
>
> *➡️* [If you upload periodic logs to a bucket, your application might need them for a week or a month. After that, you might want to delete them.](https://arc.net/l/quote/mrziypdv)
>
> *➡️* [Some documents are frequently accessed for a limited period of time. After that, they are infrequently accessed. At some point, you might not need real-time access to them, but your organization or regulations might require you to archive them for a specific period. After that, you can delete them.](https://arc.net/l/quote/mrziypdv)
>
> *➡️* [You might upload some types of data to Amazon S3 primarily for archival purposes. For example, you might archive digital media, financial, and healthcare records, raw genomics sequence data, long-term database backups, and data that must be retained for regulatory compliance.”](https://arc.net/l/quote/mrziypdv)

S3 Lifecycle rules are your secret weapon for cost optimization. Instead of manually managing storage classes or letting data accumulate indefinitely, you define **automated rules** that transition objects through different storage tiers based on their age.

## My Production Setup: The Smart Conveyor Belt

Here’s the lifecycle configuration I use across all my buckets, designed to maximize cost savings while meeting compliance requirements:

**Storage Class Progression:**

```rb
S3 Standard → IA → Glacier IR → Deep Archive → Delete
     |           |            |
   30d         90d          365d
```
- **Day 0–29:** S3 Standard *(hot data, frequent access)*
- **Day 30–89:** S3 Standard-IA *(lower-cost, infrequent access)*
- **Day 90–364:** S3 Glacier Instant Retrieval *(archive with fast retrieval)*
- **Day 365–2554:** S3 Glacier Deep Archive *(long-term, lowest-cost archive)*
- **Day 2555+:** Automatic deletion *(7-year compliance met)*

**Plus the hidden cost killer:**

- Incomplete multipart uploads cleaned up after 7 days.
- Old object versions (if versioning enabled) deleted after 90 days

Now here’s the challenge. I don’t just have one bucket. **I have dozens across multiple environments (dev, staging, production)**. Each environment needs different retention policies, dev can be aggressive with 90-day deletion, but production needs 7-year compliance retention, for example.

Configuring this manually through the AWS Console for every bucket? That’s a recipe for inconsistency and human error!**The solution? Terraform!**

## Terraform Implementation: Modular Approach

Let me show you how I actually implement S3 lifecycle rules in production using a modular Terraform approach. This isn’t just theory, this is a practical setup that can be used across multiple environments.

### The Modular Structure

I organize my Terraform code using a modular approach that makes it easy to replicate across environments:

```rb
terraform-aws-starter/
├── modules/
│   └── s3/
│       ├── main.tf          # Core S3 resources
│       ├── variables.tf     # Input variables with validations
│       ├── outputs.tf       # Exported values
│       └── README.md        # Documentation
├── staging/
│   ├── main.tf              # Staging environment config
│   ├── backend.tfvars       # Backend config (gitignored)
│   ├── terraform.tfvars     # Staging-specific values
│   └── variables.tf         # Environment variables
└── production/
    ├── main.tf              # Production environment config
    ├── backend.tfvars       # Backend config (gitignored)
    ├── terraform.tfvars     # Production-specific values
    └── variables.tf         # Environment variables
```

### Backend Configuration

This is a step 0. Don’t forget to create a dedicated bucket for your Terraform state. Each environment (staging, production) has its own `backend.tfvars` file:

```rb
# S3 Backend Configuration
bucket  = "" # TODO: Your S3 bucket name for Terraform state
key     = "staging/terraform.tfstate" # ADJUST: Path to state file in S3
region  = "" # TODO: AWS region where the S3 bucket is located
profile = "" # TODO: AWS CLI profile name to use
```

Here’s how the backend is configured in my `staging/main.tf`:

```rb
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend configuration loaded from backend.tfvars
  backend "s3" {}
}

locals {
  environment = "staging"
  region      = "ap-southeast-3" # Must match backend.tfvars region
  profile     = "my-profile"        # Must match backend.tfvars profile
}

provider "aws" {
  profile = local.profile
  region  = local.region

  default_tags {
    tags = {
      Environment = title(local.environment)
      ManagedBy   = "Terraform"
    }
  }
}
```

### Step 1: The S3 Module Core

Here’s my S3 module (`modules/s3/main.tf`) that implements all AWS best practices:

```rb
########## S3 Bucket ##########
################################

resource "aws_s3_bucket" "this" {
  bucket        = var.bucket_name
  force_destroy = var.force_destroy

  tags = merge(
    {
      Name        = var.bucket_name
      Environment = var.environment
    },
    var.tags
  )
}

########## S3 Bucket Versioning ##########
###########################################

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = var.versioning_enabled ? "Enabled" : "Disabled"
  }
}

########## S3 Bucket Encryption ##########
###########################################

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_master_key_id != null ? "aws:kms" : "AES256"
      kms_master_key_id = var.kms_master_key_id
    }
    bucket_key_enabled = var.kms_master_key_id != null ? true : false
  }
}

########## S3 Bucket Public Access Block ##########
####################################################

resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = var.block_public_access
  block_public_policy     = var.block_public_access
  ignore_public_acls      = var.block_public_access
  restrict_public_buckets = var.block_public_access
}

########## S3 Bucket Lifecycle Configuration ##########
########################################################

resource "aws_s3_bucket_lifecycle_configuration" "this" {
  count  = var.lifecycle_rules.enabled ? 1 : 0
  bucket = aws_s3_bucket.this.id

  # Depends on versioning to be configured first
  depends_on = [aws_s3_bucket_versioning.this]

  # Smart Log Lifecycle: Transitions + Expiration + Multipart Cleanup
  rule {
    id     = "smart-log-lifecycle"
    status = "Enabled"

    # Apply to all objects or specific prefix
    filter {
      prefix = var.lifecycle_rules.filter_prefix
    }

    # Transition to Standard-IA after specified days
    transition {
      days          = var.lifecycle_rules.standard_ia_days
      storage_class = "STANDARD_IA"
    }

    # Transition to Glacier Instant Retrieval after specified days
    transition {
      days          = var.lifecycle_rules.glacier_ir_days
      storage_class = "GLACIER_IR"
    }

    # Transition to Deep Archive after specified days
    transition {
      days          = var.lifecycle_rules.deep_archive_days
      storage_class = "DEEP_ARCHIVE"
    }

    # Expire objects after specified days (optional)
    dynamic "expiration" {
      for_each = var.lifecycle_rules.expiration_days != null ? [1] : []

      content {
        days = var.lifecycle_rules.expiration_days
      }
    }

    # Cleanup noncurrent versions (only if versioning enabled AND noncurrent_expiration_days is set)
    dynamic "noncurrent_version_expiration" {
      for_each = var.versioning_enabled && var.lifecycle_rules.noncurrent_expiration_days != null ? [1] : []

      content {
        noncurrent_days = var.lifecycle_rules.noncurrent_expiration_days
      }
    }

    # Abort incomplete multipart uploads
    abort_incomplete_multipart_upload {
      days_after_initiation = var.lifecycle_rules.abort_incomplete_multipart_days
    }
  }
}
```

**Key design decisions:**

1. `**depends_on**` **for versioning**: Ensures versioning is configured before lifecycle rules are applied
2. **Conditional lifecycle**: Uses `count` to make lifecycle rules optional
3. **Separate resources**: Each S3 feature is a separate resource for better control
4. **Encryption flexibility**: Supports both AES256 (free) and KMS (more control)
5. **Dynamic noncurrent version cleanup**: Only applies noncurrent version expiration if versioning is enabled. Without this, Terraform would try to create the rule even for non-versioned buckets, which doesn’t make sense.

### Step 2: Built-in Validations

Here’s what makes this module production-ready with **automatic validations** in `modules/s3/variables.tf`:

```rb
########## Required Variables ##########
#########################################

variable "environment" {
  description = "Environment name (e.g., staging, production)"
  type        = string
}

variable "bucket_name" {
  description = "Name of the S3 bucket (must be globally unique)"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]*[a-z0-9]$", var.bucket_name))
    error_message = "Bucket name must be lowercase alphanumeric with hyphens, cannot start/end with hyphen."
  }
}

########## Bucket Configuration ##########
##########################################

variable "force_destroy" {
  description = "Allow deletion of bucket with objects (use with caution)"
  type        = bool
  default     = false
}

variable "versioning_enabled" {
  description = "Enable versioning on S3 bucket"
  type        = bool
  default     = false
}

variable "block_public_access" {
  description = "Block all public access to the bucket"
  type        = bool
  default     = true
}

########## Encryption Configuration ##########
###############################################

variable "kms_master_key_id" {
  description = "KMS key ID for encryption (leave null for AES256)"
  type        = string
  default     = null
}

########## Lifecycle Configuration ##########
##############################################

variable "lifecycle_rules" {
  description = "Lifecycle configuration for S3 bucket objects"
  type = object({
    enabled                         = bool
    filter_prefix                   = string
    standard_ia_days                = number
    glacier_ir_days                 = number
    deep_archive_days               = number
    expiration_days                 = optional(number, null)
    noncurrent_expiration_days      = optional(number, null)
    abort_incomplete_multipart_days = number
  })

  default = {
    enabled                         = true
    filter_prefix                   = ""
    standard_ia_days                = 30
    glacier_ir_days                 = 90
    deep_archive_days               = 365
    expiration_days                 = null
    noncurrent_expiration_days      = null
    abort_incomplete_multipart_days = 7
  }

  validation {
    condition = (
      var.lifecycle_rules.standard_ia_days < var.lifecycle_rules.glacier_ir_days &&
      var.lifecycle_rules.glacier_ir_days < var.lifecycle_rules.deep_archive_days &&
      (var.lifecycle_rules.expiration_days == null || var.lifecycle_rules.deep_archive_days < var.lifecycle_rules.expiration_days)
    )
    error_message = "Lifecycle transition days must be in ascending order: Standard-IA < Glacier IR < Deep Archive < Expiration (if set)."
  }

  validation {
    condition     = var.lifecycle_rules.standard_ia_days >= 30
    error_message = "Minimum 30 days required before transitioning to Standard-IA (AWS requirement)."
  }

  validation {
    condition     = var.lifecycle_rules.abort_incomplete_multipart_days >= 1
    error_message = "Abort incomplete multipart upload days must be at least 1."
  }

  validation {
    condition     = var.lifecycle_rules.noncurrent_expiration_days == null || var.lifecycle_rules.noncurrent_expiration_days >= 1
    error_message = "Noncurrent version expiration days must be at least 1 (or null to disable)."
  }
}

########## Tags ##########
##########################

variable "tags" {
  description = "Additional tags for the S3 bucket"
  type        = map(string)
  default     = {}
}
```

**These validations are lifesavers**. They prevent me from:

- Violating AWS’s 30-day minimum for Standard-IA
- Creating invalid transition orders that AWS will reject
- Accidentally setting lifecycle rules that cost more than they save

AWS documentation backs this up:

> [“Before you transition objects to S3 Standard-IA or S3 One Zone-IA, you must store them for at least 30 days in Amazon S3.”](https://arc.net/l/quote/mikpmaan)

### Step 3: Using the Module in Staging

Here’s how I configure the S3 module in my `staging/main.tf`:

```rb
########## S3 Bucket ##########
module "s3" {
  source = "../modules/s3"

  environment         = local.environment
  bucket_name         = var.s3_bucket_name
  force_destroy       = var.s3_force_destroy
  versioning_enabled  = var.s3_versioning_enabled
  block_public_access = var.s3_block_public_access
  kms_master_key_id   = var.s3_kms_master_key_id
  lifecycle_rules     = var.s3_lifecycle_rules

  tags = var.s3_tags
}
```

Don’t forget `staging/variables.tf:`

```rb
########## S3 Configuration ##########
#######################################

variable "s3_bucket_name" {
  description = "Name of the S3 bucket (must be globally unique)"
  type        = string
  default     = ""
}

variable "s3_force_destroy" {
  description = "Allow deletion of bucket with objects (use with caution)"
  type        = bool
  default     = false
}

variable "s3_versioning_enabled" {
  description = "Enable versioning on S3 bucket"
  type        = bool
  default     = false
}

variable "s3_block_public_access" {
  description = "Block all public access to the bucket"
  type        = bool
  default     = true
}

variable "s3_kms_master_key_id" {
  description = "KMS key ID for encryption (leave null for AES256)"
  type        = string
  default     = null
}

variable "s3_lifecycle_rules" {
  description = "Lifecycle configuration for S3 bucket objects"
  type = object({
    enabled                         = bool
    filter_prefix                   = string
    standard_ia_days                = number
    glacier_ir_days                 = number
    deep_archive_days               = number
    expiration_days                 = optional(number, null)
    noncurrent_expiration_days      = optional(number, null)
    abort_incomplete_multipart_days = number
  })
  default = {
    enabled                         = true
    filter_prefix                   = ""
    standard_ia_days                = 30
    glacier_ir_days                 = 90
    deep_archive_days               = 365
    expiration_days                 = null
    noncurrent_expiration_days      = null
    abort_incomplete_multipart_days = 7
  }
}

variable "s3_tags" {
  description = "Additional tags for the S3 bucket"
  type        = map(string)
  default     = {}
}
```

And my `staging/terraform.tfvars` with actual values:

```rb
########## S3 Configuration ##########
#######################################

s3_bucket_name         = "my-temporary-bucket-03012026" # TODO: Must be globally unique
s3_force_destroy       = false                          # TODO: true for dev/test (allows deletion with objects)
s3_versioning_enabled  = true                           # TODO: true/false (recommended: true for production)
s3_block_public_access = true                           # Keep true for security
s3_kms_master_key_id   = null                           # OPTIONAL: Specify KMS key ARN for KMS encryption, null for AES256

# Smart Log Lifecycle (includes transitions, expiration, and multipart cleanup)
s3_lifecycle_rules = {
  enabled                         = true # Enable lifecycle rules
  filter_prefix                   = ""   # TODO: Prefix to apply lifecycle ("" = all objects, "logs/" = logs only)
  standard_ia_days                = 30   # TODO: Days to transition to Standard-IA (min: 30)
  glacier_ir_days                 = 90   # TODO: Days to transition to Glacier Instant Retrieval
  deep_archive_days               = 365  # TODO: Days to transition to Deep Archive (cost-optimized: 365)
  expiration_days                 = null # TODO: Days to delete objects (null = keep forever, 2555 = 7 years compliance)
  noncurrent_expiration_days      = 90 # TODO: Days to delete noncurrent versions (null = keep forever, 90 = recommended)
  abort_incomplete_multipart_days = 7    # TODO: Days to cleanup incomplete multipart uploads
}

s3_tags = {
  Project = "MyApp"
  Purpose = "Application Logs"
}
```

### Step 4: Deploying the Configuration

Here’s my actual deployment workflow:

```rb
# Navigate to staging environment
cd staging/

# Initialize Terraform with backend config
terraform init -backend-config=backend.tfvars

# Validate the configuration (runs our validations)
terraform validate

# Preview what will be created
terraform plan -target=module.s3

# Apply only the S3 module first (safer)
terraform apply -target=module.s3

# Verify the lifecycle configuration
aws s3api get-bucket-lifecycle-configuration \
  --bucket my-temporary-bucket-03012026 \
  --profile my-profile
```

### Results

After running `terraform apply`, the S3 bucket is created with lifecycle rules configured:

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*mJ4u7PgHwq-Susl71IkX3g.png)

The bucket lifecycle is created

![](https://miro.medium.com/v2/resize:fit:640/format:webp/1*qo1X4FkWJBbTJyntfKhQGQ.png)

Bucket lifecycle rule details

## Final Thoughts

Creating an S3 bucket is trivial. Governing it cost-effectively at scale is not. With modular Terraform and lifecycle rules, you automate cost optimization, enforce guardrails, and scale across environments without chaos. Set it up once, and thank yourself every month when the AWS bill arrives.

## References:

- [https://aws.amazon.com/s3/storage-classes/](https://aws.amazon.com/s3/storage-classes/)
- [https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)
- [https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-configuration-examples.html](https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-configuration-examples.html)
- [https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-transition-general-considerations.html](https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-transition-general-considerations.html)
- [https://aws.amazon.com/blogs/aws-cloud-financial-management/discovering-and-deleting-incomplete-multipart-uploads-to-lower-amazon-s3-costs/](https://aws.amazon.com/blogs/aws-cloud-financial-management/discovering-and-deleting-incomplete-multipart-uploads-to-lower-amazon-s3-costs/)

[![AWS in Plain English](https://miro.medium.com/v2/resize:fill:96:96/1*6EeD87OMwKk-u3ncwAOhog.png)](https://aws.plainenglish.io/?source=post_page---post_publication_info--ee7e36796441---------------------------------------)

[![AWS in Plain English](https://miro.medium.com/v2/resize:fill:128:128/1*6EeD87OMwKk-u3ncwAOhog.png)](https://aws.plainenglish.io/?source=post_page---post_publication_info--ee7e36796441---------------------------------------)

[Last published 9 hours ago](https://aws.plainenglish.io/how-to-set-up-amazon-route-53-for-custom-domains-and-aws-load-balancers-54fd8060ae97?source=post_page---post_publication_info--ee7e36796441---------------------------------------)

New AWS, Cloud, and DevOps content every day. Follow to join our 3.5M+ monthly readers.

Currently helping engineers provision AWS infrastructure and occasionally scale down their stress levels.

## Responses (3)

gwk

What are your thoughts?

```rb
Great detailed implementation, Qolbi — the modular Terraform setup looks really solid.One question: have you considered using S3 Intelligent-Tiering as an alternative to the Standard → Standard-IA transition? For workloads with unpredictable access…
```

1

## More from Qolbi Nurwandi and AWS in Plain English

## Recommended from Medium

[

See more recommendations

](https://medium.com/?source=post_page---read_next_recirc--ee7e36796441---------------------------------------)
