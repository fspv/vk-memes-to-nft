sudo docker run \
    -e METAMASK_PASSWORD="${METAMASK_PASSWORD}" \
    -e METAMASK_RECOVERY_PHRASE="${METAMASK_RECOVERY_PHRASE}" \
    -e TWO_CAPTCHA_KEY="${TWO_CAPTCHA_KEY}" \
    -e VK_COMMUNITY="${VK_COMMUNITY}" \
    -e VK_SERVICE_TOKEN="${VK_SERVICE_TOKEN}" \
    -e OPENSEA_COLLECTION="${OPENSEA_COLLECTION}" \
    -e OPENSEA_UPLOADER_DIR="${OPENSEA_UPLOADER_DIR}" \
    -v $(pwd)/test.db:/src/test.db \
    -v $(pwd)/follower:/src/follower \
    -v $(pwd)/uploader:/src/uploader \
    -v $(pwd)/vk:/src/vk \
    -it vkmemes \
    bash
