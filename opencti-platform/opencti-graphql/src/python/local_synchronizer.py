import json
import logging
import sys
import os

from pycti import OpenCTIConnectorHelper, OpenCTIApiClient


class TestLocalSynchronizer:
    def __init__(self, source_url, source_token, target_url, target_token, consuming_count, start_timestamp, live_stream_id=None):
        self.source_url = source_url
        self.source_token = source_token
        self.target_url = target_url
        self.target_token = target_token
        self.live_stream_id = live_stream_id
        self.count_number = 0
        self.consuming_count = consuming_count
        self.start_timestamp = start_timestamp
        self.stream = None
        # Source
        config = {
            "id": "673ba380-d229-4160-9213-ac5afdaabf96",
            "type": "STREAM",
            "name": "Synchronizer",
            "scope": "synchronizer",
            "confidence_level": 15,
            "live_stream_id": self.live_stream_id,
            "log_level": "info",
        }
        self.opencti_source_client = OpenCTIApiClient(source_url, source_token)
        self.opencti_source_helper = OpenCTIConnectorHelper({
            "opencti": {"url": self.source_url, "token": self.source_token},
            "connector": config,
        })
        # Target
        self.opencti_target_client = OpenCTIApiClient(target_url, target_token)
        self.opencti_target_helper = OpenCTIConnectorHelper({
            "opencti": {"url": self.target_url, "token": self.target_token},
            "connector": config,
        })

    def _process_message(self, msg):
        if (
            msg.event == "create"
            or msg.event == "update"
            or msg.event == "merge"
            or msg.event == "delete"
        ):
            logging.info("Processing event " + msg.id)
            self.count_number += 1
            data = json.loads(msg.data)
            if msg.event == "create":
                bundle = {
                    "type": "bundle",
                    "x_opencti_event_version": data["version"],
                    "objects": [data["data"]],
                }
                self.opencti_target_client.stix2.import_bundle(bundle)
            elif msg.event == "update":
                bundle = {
                    "type": "bundle",
                    "x_opencti_event_version": data["version"],
                    "objects": [data["data"]],
                }
                self.opencti_target_client.stix2.import_bundle(bundle, True)
            elif msg.event == "merge":
                sources = data["data"]["x_opencti_context"]["sources"]
                object_ids = list(map(lambda element: element["id"], sources))
                self.opencti_target_helper.api.stix_core_object.merge(
                    id=data["data"]["id"], object_ids=object_ids
                )
            elif msg.event == "delete":
                self.opencti_target_helper.api.stix.delete(id=data["data"]["id"])
            if self.count_number >= self.consuming_count:
                self.stream.stop()

    def sync(self):
        # Reset the connector state if exists
        self.opencti_source_helper.set_state({"connectorLastEventId": self.start_timestamp})
        # Start to listen the stream from start specified parameter
        self.stream = self.opencti_source_helper.listen_stream(
            self._process_message, self.source_url, self.source_token, False, self.start_timestamp
        )
        self.stream.join()


if __name__ == "__main__":
    try:
        source_url = sys.argv[1]
        source_token = sys.argv[2]
        target_url = sys.argv[3]
        target_token = sys.argv[4]
        consuming_count = int(sys.argv[5])
        start_timestamp = sys.argv[6]
        live_stream_id = sys.argv[7] if len(sys.argv) > 7 else None

        testLocalSynchronizer = TestLocalSynchronizer(
            source_url, source_token, target_url, target_token, consuming_count, start_timestamp, live_stream_id
        )
        testLocalSynchronizer.sync()
        os._exit(0)
    except Exception as e:
        logging.exception(str(e))
        exit(1)
