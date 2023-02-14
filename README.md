GCP:

1. Go to GCP and create an account.
1. Create a repo in registry.
1. Get the repo tag
1. Build docker

```bash
docker build -t earwise .
```

5. Tag and deploy docker

```bash
docker tag earwise:latest us-east1-docker.pkg.dev/earwise-377812/earwise/earwise:latest
docker push us-east1-docker.pkg.dev/earwise-377812/earwise/earwise:latest
```

6. Create the app

```bash
gcloud run deploy --image us-east1-docker.pkg.dev/earwise-377812/earwise/earwise:latest --cpu 4 --concurrency 2 --memory 16Gi --platform managed --min-instances 0 --max-instances 5 --timeout 5m --port 8005
```
