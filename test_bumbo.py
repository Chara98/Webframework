import pytest

from api import API


def test_basic_route(api):
    @api.route('/home')
    def home(request, response):
        response.text = 'YOLO'


def test_route_overlap_throws_exception(api):
    @api.route('/home')
    def home2(request, response):
        response.text = 'YOLO'

    with pytest.raises(AssertionError):
        @api.route('/home')
        def home2(request, response):
            response.text = 'YOLO'


def test_class_route(api):
    @api.route('/home')
    class Home:
        def get(self, request, response):
            response.text = 'YOLO'


def test_bumbo_client_can_send_requests(api, client):
    RESPONSE_TEXT = 'THIS IS COOL'

    @api.route('/hey')
    def cool(request, response):
        response.text = RESPONSE_TEXT

    assert client.get('http://testserver/hey').text == RESPONSE_TEXT


def test_parameterized_route(api, client):
    @api.route('/{name}')
    def hello(request, response, name):
        response.text = f'hey {name}'

    assert client.get('http://testserver/mat').text == 'hey mat'
    assert client.get('http://testserver/ash').text == 'hey ash'


def test_default_404_response(client):
    response = client.get('http://testserver/doesnotexist')
    assert response.status_code == 404
    assert response.text == "Not Found"


def test_alternate_route(api, client):
    response_text = 'Al'

    def home(request, response):
        response.text = response_text

    api.add_route('/alter', home)
    assert client.get('http://testserver/alter').text == response_text


def test_query_param(api, client):
    @api.route('/abc')
    def abc(request, response, q):
        response.text = q

    assert client.get('http://testserver/abc?q=hello').text == 'hello'
