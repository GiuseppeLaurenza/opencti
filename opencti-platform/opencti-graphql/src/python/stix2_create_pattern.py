import json
import sys

from stix2 import EqualityComparisonExpression, ObjectPath, ObservationExpression, OrBooleanExpression

PATTERN_MAPPING = {
    "Autonomous-System": ["number"],
    "Directory": ["path"],
    "Domain-Name": ["value"],
    "Email-Addr": ["value"],
    "File_name": ["name"],
    "File_md5": ["hashes", "MD5"],
    "File_sha1": ["hashes", "SHA-1"],
    "File_sha256": ["hashes", "SHA-256"],
    "File_sha512": ["hashes", "SHA-512"],
    "Email-Message_body": ["body"],
    "Email-Message_subject": ["subject"],
    "Email-Mime-Part-Type": ["body"],
    "IPv4-Addr": ["value"],
    "IPv6-Addr": ["value"],
    "Mac-Addr": ["value"],
    "Mutex": ["name"],
    "X-OpenCTI-Text": ["value"],
    "Network-Traffic": ["dst_port"],
    "Process": ["command_line"],
    "Process_pid": ["pid"],
    "Software": ["name"],
    "Url": ["value"],
    "User-Account": ["acount_login"],
    "Windows-Registry-Key": ["key"],
    "Windows-Registry-Value-Type": ["name"],
}


def return_data(data):
    print(json.dumps(data))
    sys.stdout.flush()
    exit(0)


def generate_part(observable_type, observable_value):
    if observable_type in PATTERN_MAPPING:
        lhs = ObjectPath(
            observable_type.lower()
            if "_" not in observable_type
            else observable_type.split("_")[0].lower(),
            PATTERN_MAPPING[observable_type],
        )
        return EqualityComparisonExpression(lhs, observable_value)
    return None

def main():
    if len(sys.argv) <= 2:
        return_data(
            {"status": "error", "message": "Missing argument to the Python script"}
        )

    if sys.argv[1] == "check":
        return_data({"status": "success"})

    observable_type = sys.argv[1]
    observable_value = sys.argv[2]
    pattern = None
    if "__" in observable_type:
        observable_types = observable_type.split("__")
        observable_values = observable_value.split("__")
        length = len(observable_types)
        parts = []
        for i in range(length):
            part = generate_part(observable_types[i], observable_values[i])
            if part is not None:
                parts.append(part)
        if len(parts) > 0:
            pattern = ObservationExpression(OrBooleanExpression(parts))
    else:
        ece = generate_part(observable_type, observable_value)
        if ece is not None:
            pattern = ObservationExpression(ece)
    if pattern is not None:
        return_data({"status": "success", "data": str(pattern)})
    else:
        return_data({"status": "unknown", "data": None})


if __name__ == "__main__":
    main()
