#!/usr/bin/env python3
"""
Garcar SecretOps CLI for GAR-399.

Stores/retrieves encrypted secrets in AWS SSM Parameter Store.

Path:
    /garcar/{env}/{service}/{KEY}

GAR-399 target services:
    defender-os
    revenue-intelligence-engine
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List

try:
    import boto3
    from botocore.exceptions import ClientError
except Exception:
    print("Missing dependency: boto3. Install with: pip install boto3 botocore", file=sys.stderr)
    raise

SAFE_KEY = re.compile(r"^[A-Z][A-Z0-9_]{1,127}$")
DEFAULT_MANIFEST = "manifests/gar399.secrets.json"


def die(message: str, code: int = 1) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(code)


def region() -> str:
    return os.getenv("AWS_REGION", "us-east-1")


def ssm():
    return boto3.client("ssm", region_name=region())


def normalize_prefix(prefix: str) -> str:
    prefix = prefix.strip()
    if not prefix:
        die("prefix cannot be empty")
    if not prefix.startswith("/"):
        prefix = "/" + prefix
    return prefix.rstrip("/")


def validate_part(label: str, value: str) -> str:
    if not value or "/" in value or " " in value:
        die(f"invalid {label}: {value!r}")
    return value


def validate_key(key: str) -> str:
    key = key.strip()
    if not SAFE_KEY.match(key):
        die(f"invalid secret key {key!r}; expected uppercase env-var style name")
    return key


def base_path(prefix: str, env: str, service: str) -> str:
    return f"{normalize_prefix(prefix)}/{validate_part('env', env)}/{validate_part('service', service)}"


def param_path(prefix: str, env: str, service: str, key: str) -> str:
    return f"{base_path(prefix, env, service)}/{validate_key(key)}"


def load_manifest(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if "repos" not in data:
        die("manifest missing repos[]")
    return data


def github_mask(value: str) -> None:
    if os.getenv("GITHUB_ACTIONS", "").lower() == "true" and value:
        print(f"::add-mask::{value}")


def put_parameter(name: str, value: str, kms_key_id: str | None = None) -> None:
    if not value:
        die(f"refusing to store empty value for {name}")

    kwargs = {
        "Name": name,
        "Value": value,
        "Type": "SecureString",
        "Overwrite": True,
        "Tier": "Standard",
        "Tags": [
            {"Key": "managed-by", "Value": "garcar-secretops"},
            {"Key": "gar-ticket", "Value": "GAR-399"}
        ],
    }
    if kms_key_id:
        kwargs["KeyId"] = kms_key_id

    try:
        ssm().put_parameter(**kwargs)
    except ClientError as exc:
        die(str(exc))


def get_parameter(name: str, decrypt: bool = True) -> str:
    try:
        resp = ssm().get_parameter(Name=name, WithDecryption=decrypt)
    except ClientError as exc:
        die(str(exc))
    value = resp["Parameter"]["Value"]
    if decrypt:
        github_mask(value)
    return value


def get_by_path(prefix: str, env: str, service: str, decrypt: bool = True) -> Dict[str, str]:
    client = ssm()
    path = base_path(prefix, env, service)
    token = None
    out: Dict[str, str] = {}
    while True:
        kwargs = {
            "Path": path,
            "Recursive": False,
            "WithDecryption": decrypt,
            "MaxResults": 10,
        }
        if token:
            kwargs["NextToken"] = token
        try:
            resp = client.get_parameters_by_path(**kwargs)
        except ClientError as exc:
            die(str(exc))

        for item in resp.get("Parameters", []):
            key = item["Name"].split("/")[-1]
            out[key] = item["Value"]
            if decrypt:
                github_mask(item["Value"])

        token = resp.get("NextToken")
        if not token:
            return out


def cmd_put(args):
    key = validate_key(args.key)
    name = param_path(args.prefix, args.env, args.service, key)

    if args.stdin:
        value = sys.stdin.read()
        if value.endswith("\n"):
            value = value[:-1]
    else:
        value = getpass.getpass(f"Enter value for {name}: ")

    put_parameter(name, value, args.kms_key_id)
    print(json.dumps({"stored": name, "region": region()}, indent=2))


def cmd_get(args):
    name = param_path(args.prefix, args.env, args.service, args.key)
    value = get_parameter(name, decrypt=True)
    if args.json:
        print(json.dumps({"key": args.key, "path": name, "value": value}, indent=2))
    else:
        print(value)


def cmd_list(args):
    values = get_by_path(args.prefix, args.env, args.service, decrypt=False)
    for key in sorted(values):
        print(key)


def cmd_export_github_env(args):
    github_env = os.getenv("GITHUB_ENV")
    if not github_env:
        die("GITHUB_ENV not set; export-github-env is for GitHub Actions")

    secrets = get_by_path(args.prefix, args.env, args.service, decrypt=True)
    required = args.required or []
    missing = [k for k in required if k not in secrets]
    if missing:
        die(f"missing required secrets for {args.service}: {', '.join(missing)}")

    with open(github_env, "a", encoding="utf-8") as fh:
        for key in sorted(secrets):
            value = secrets[key]
            if "\n" in value:
                marker = f"EOF_SECRETOPS_{key}"
                fh.write(f"{key}<<{marker}\n{value}\n{marker}\n")
            else:
                fh.write(f"{key}={value}\n")

    print(json.dumps({"exported_keys": sorted(secrets), "service": args.service}, indent=2))


def cmd_export_dotenv(args):
    secrets = get_by_path(args.prefix, args.env, args.service, decrypt=True)
    for key in sorted(secrets):
        value = secrets[key].replace("\\", "\\\\").replace("\n", "\\n").replace("'", "'\"'\"'")
        print(f"{key}='{value}'")


def cmd_run(args):
    if args.command[:1] == ["--"]:
        args.command = args.command[1:]
    if not args.command:
        die("missing command after --")

    secrets = get_by_path(args.prefix, args.env, args.service, decrypt=True)
    env = os.environ.copy()
    env.update(secrets)
    raise SystemExit(subprocess.run(args.command, env=env).returncode)


def load_values_file(path: str) -> Dict[str, Dict[str, str]]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def cmd_activate_gar399(args):
    manifest = load_manifest(args.manifest)
    prefix = args.prefix or manifest.get("prefix", "/garcar")
    env = args.env or manifest.get("environment", "prod")
    values_by_service = load_values_file(args.values_file) if args.values_file else {}

    stored = []
    for repo_cfg in manifest["repos"]:
        service = repo_cfg["service"]
        for key in repo_cfg["required_secrets"]:
            key = validate_key(key)
            name = param_path(prefix, env, service, key)

            if service in values_by_service and key in values_by_service[service]:
                value = values_by_service[service][key]
            else:
                value = getpass.getpass(f"Enter value for {service}/{key}: ")

            put_parameter(name, value, args.kms_key_id)
            stored.append({"service": service, "key": key, "path": name})

    print(json.dumps({
        "ticket": manifest.get("ticket", "GAR-399"),
        "environment": env,
        "stored_count": len(stored),
        "stored": stored
    }, indent=2))


def cmd_audit_gar399(args):
    manifest = load_manifest(args.manifest)
    prefix = args.prefix or manifest.get("prefix", "/garcar")
    env = args.env or manifest.get("environment", "prod")

    missing = []
    present = []
    for repo_cfg in manifest["repos"]:
        service = repo_cfg["service"]
        existing = get_by_path(prefix, env, service, decrypt=False)
        for key in repo_cfg["required_secrets"]:
            if key in existing:
                present.append({"service": service, "key": key})
            else:
                missing.append({"service": service, "key": key, "path": param_path(prefix, env, service, key)})

    print(json.dumps({
        "ticket": manifest.get("ticket", "GAR-399"),
        "environment": env,
        "ok": not missing,
        "present_count": len(present),
        "missing_count": len(missing),
        "missing": missing
    }, indent=2))

    if missing:
        raise SystemExit(2)


def build_parser():
    parser = argparse.ArgumentParser("secretops")
    parser.add_argument("--prefix", default=os.getenv("SECRETOPS_PREFIX", "/garcar"))
    parser.add_argument("--env", default=os.getenv("SECRETOPS_ENV", "prod"))
    parser.add_argument("--service", default=os.getenv("SECRETOPS_SERVICE", "defender-os"))
    parser.add_argument("--kms-key-id", default=os.getenv("SECRETOPS_KMS_KEY_ID"))
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("put")
    p.add_argument("key")
    p.add_argument("--stdin", action="store_true")
    p.set_defaults(func=cmd_put)

    p = sub.add_parser("get")
    p.add_argument("key")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_get)

    p = sub.add_parser("list")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("export-github-env")
    p.add_argument("--required", nargs="*", default=[])
    p.set_defaults(func=cmd_export_github_env)

    p = sub.add_parser("export-dotenv")
    p.set_defaults(func=cmd_export_dotenv)

    p = sub.add_parser("run")
    p.add_argument("command", nargs=argparse.REMAINDER)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("activate-gar399")
    p.add_argument("--manifest", default=DEFAULT_MANIFEST)
    p.add_argument("--values-file")
    p.set_defaults(func=cmd_activate_gar399)

    p = sub.add_parser("audit-gar399")
    p.add_argument("--manifest", default=DEFAULT_MANIFEST)
    p.set_defaults(func=cmd_audit_gar399)

    return parser


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
