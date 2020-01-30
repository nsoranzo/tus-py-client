import base64
import hashlib

import responses

from tusclient import request
from tests import mixin


class TusRequestTest(mixin.Mixin):
    def setUp(self):
        super(TusRequestTest, self).setUp()
        self.request = request.TusRequest(self.uploader)

    def test_perform(self):
        with open('LICENSE', 'rb') as stream, responses.RequestsMock() as resps:
            size = stream.tell()
            resps.add(responses.PATCH, self.url,
                      adding_headers={'upload-offset': f'{size}'},
                      status=204)

            self.request.perform()
            self.assertEqual(f'{size}', self.request.response_headers['upload-offset'])

    def test_perform_checksum(self):
        self.uploader.upload_checksum = True
        tus_request = request.TusRequest(self.uploader)

        with open('LICENSE', 'r') as stream, responses.RequestsMock() as resps:
            license_ = stream.read()
            encoded_file = license_.encode('utf-8')
            expected_checksum = "sha1 " + \
                base64.standard_b64encode(hashlib.sha1(
                    encoded_file).digest()).decode("ascii")

            sent_checksum = ''
            def validate_headers(req):
                nonlocal sent_checksum
                sent_checksum = req.headers['upload-checksum']
                return (204, {}, None)

            resps.add_callback(responses.PATCH, self.url, callback=validate_headers)
            tus_request.perform()
            self.assertEqual(sent_checksum, expected_checksum)
