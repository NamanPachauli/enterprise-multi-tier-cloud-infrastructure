
import urllib.error
import urllib.request

BASE_URL = "http://localhost:8086"


def check_endpoint(path, expected_status):
    request = urllib.request.Request(BASE_URL + path)

    try:
        response = urllib.request.urlopen(request, timeout=10)
        status = response.status
    except urllib.error.HTTPError as error:
        status = error.code

    assert status == expected_status, (
        f"{path}: expected {expected_status}, received {status}"
    )


def test_home_endpoint():
    check_endpoint("/", 200)


def test_application_health():
    check_endpoint("/health", 200)


def test_database_health():
    check_endpoint("/db-health", 200)


def test_metrics_blocked_by_nginx():
    check_endpoint("/metrics", 404)


def test_unknown_endpoint():
    check_endpoint("/this-endpoint-does-not-exist", 404)
