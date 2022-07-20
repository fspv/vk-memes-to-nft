This app follows vk public and emits events with the post data as new posts are created

# Run
Set secrets

```
export METAMASK_PASSWORD="xxx"
export METAMASK_RECOVERY_PHRASE="yyy"
export TWO_CAPTCHA_KEY="zzz"
# Community to get memes from
export VK_COMMUNITY=""
export VK_SERVICE_TOKEN=""
# Collection to upload memes to (slug from the url is to be put here)
export OPENSEA_COLLECTION=""
# Uploader location within the docker container
export OPENSEA_UPLOADER_DIR="/src/opensea-automatic-bulk-upload-and-sale/"
```

```
sudo docker build -t vkmemes .
sudo docker run -e METAMASK_PASSWORD="${METAMASK_PASSWORD}" -e METAMASK_RECOVERY_PHRASE="${METAMASK_RECOVERY_PHRASE}" -e TWO_CAPTCHA_KEY="${TWO_CAPTCHA_KEY}" -e VK_COMMUNITY="${VK_COMMUNITY}" -e VK_SERVICE_TOKEN="${VK_SERVICE_TOKEN}" -e OPENSEA_COLLECTION="${OPENSEA_COLLECTION}" -e OPENSEA_UPLOADER_DIR="${OPENSEA_UPLOADER_DIR}" -it vkmemes bash

cd /src/
. ~/.venv/bin/activate

ipython uploader/scheduler.py
ipython uploader/processor.py
```
