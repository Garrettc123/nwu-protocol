terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "github_org"     { type = string }
variable "github_repo"    { type = string; default = "nwu-protocol" }
variable "aws_region"     { type = string; default = "us-east-1" }
variable "secret_prefix"  { type = string; default = "/garcar" }

provider "aws" { region = var.aws_region }

data "aws_caller_identity" "current" {}

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

resource "aws_iam_role" "github_actions" {
  name = "github-actions-nwu-protocol"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = aws_iam_openid_connect_provider.github.arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:${var.github_org}/${var.github_repo}:*"
        }
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })
}

resource "aws_iam_policy" "ssm_read" {
  name = "nwu-protocol-ssm-read"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ssm:GetParameter", "ssm:GetParametersByPath"]
      Resource = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter${var.secret_prefix}/prod/nwu-protocol/*"
    }, {
      Effect   = "Allow"
      Action   = ["kms:Decrypt"]
      Resource = "*"
      Condition = {
        StringEquals = { "kms:ViaService" = "ssm.${var.aws_region}.amazonaws.com" }
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.github_actions.name
  policy_arn = aws_iam_policy.ssm_read.arn
}

output "role_arn" {
  value = aws_iam_role.github_actions.arn
}
