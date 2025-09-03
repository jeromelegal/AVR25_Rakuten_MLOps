from api.config.s3 import get_client


class TestS3:
    def test_s3_get_client(self, mock_settings):
        client = get_client(settings=mock_settings)

        assert client is not None

    def test_s3_get_buckets(self, mock_settings):
        client = get_client(settings=mock_settings)

        response = client.list_buckets(MaxBuckets=10)

        assert len(response["Buckets"]) == 1
        assert response["Buckets"][0]["Name"] == "images"


#         # # Create a bucket
# # s3.create_bucket(Bucket="mybucket")

# # Upload a file to the bucket
# s3.upload_file("myfile.txt", "mybucket", "myfile.txt")
# # List objects in the bucket
# response = s3.list_objects(Bucket="mybucket")
# for obj in response.get("Contents", []):
#     print(obj["Key"])

#         assert client is not None


# # # # Create a bucket
# # # s3.create_bucket(Bucket="mybucket")

# # # Upload a file to the bucket
# # s3.upload_file("myfile.txt", "mybucket", "myfile.txt")
# # # List objects in the bucket
# # response = s3.list_objects(Bucket="mybucket")
# # for obj in response.get("Contents", []):
# #     print(obj["Key"])
