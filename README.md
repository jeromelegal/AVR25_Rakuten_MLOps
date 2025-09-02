Rakuten MLOps
==============================

## How to use
### Build the services
```bash
docker-compose up --build
```

### Start services
```bash
docker-compose up --force-recreate
```
The `--force-recreate` option is required for vault to be able to initialize
