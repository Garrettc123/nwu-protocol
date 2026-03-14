# 🤖 Quick Automation Reference

## First Time Setup (30 seconds)

```bash
./scripts/setup-automation.sh    # Install all automation
```

## Common Tasks

### Configure Environment

```bash
./configure.sh                    # Interactive wizard
```

### Run Tests

```bash
./test-all.sh                     # Smart tests (with cache)
./test-all.sh --no-cache          # Force all tests
./test-all.sh api                 # Only API tests
```

### Check Services

```bash
make status                       # Service status
make health                       # Health checks
make logs                         # View logs
```

### Deploy

```bash
./deploy.sh                       # Full deployment
make deploy                       # Alternative
```

## Pre-Commit Automation

Runs automatically on `git commit`:

- ✅ Auto-format code
- 🔐 Detect secrets
- ⚠️ Warn about debug code
- 📏 Check file sizes
- 📝 Validate commit message

**Bypass (not recommended):**

```bash
git commit --no-verify
```

## Tips

**Faster tests:** Use cache (default)

```bash
./test-all.sh    # Uses 5-min cache
```

**Full validation:** Skip cache

```bash
./test-all.sh --no-cache
```

**Specific tests:** Choose categories

```bash
./test-all.sh infrastructure api
```

**Help:** Show all options

```bash
./test-all.sh --help
```

## Troubleshooting

**Permission denied:**

```bash
chmod +x scripts/*.sh
```

**Hook not running:**

```bash
./scripts/setup-automation.sh
```

**Clear test cache:**

```bash
rm -rf /tmp/nwu-test-cache
```

## Learn More

📖 Full guide: [AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md)
