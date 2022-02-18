from webob import Request, Response
from parse import parse
from jinja2 import Environment, FileSystemLoader
from requests import Session as RequestsSession
from wsgiadapter import WSGIAdapter as RequestsWSGIAdapter
from urllib.parse import urlparse
import inspect
import os


class API:
    def __init__(self, templates_dir='templates'):
        self.funcs = []
        self.routes = {}
        self.templates_env = Environment(loader=FileSystemLoader(os.path.abspath(templates_dir)))

    def __call__(self, environ, start_response):
        request = Request(environ)
        print('environ = ', environ)
        self.q = environ['QUERY_STRING']
        response = self.handle_request(request)
        return response(environ, start_response)

    def add_route(self, path, handler):
        assert path not in self.routes, "such route already exists"
        self.routes[path] = handler

    def test_session(self, base_url='http://testserver'):
        session = RequestsSession()
        session.mount(prefix=base_url, adapter=RequestsWSGIAdapter(self))
        return session

    def route(self, path):
        if path in self.routes:
            raise AssertionError("Such route already exists")

        def wrapper(handler):
            self.routes[path] = handler
            self.funcs.append(handler)
            return handler

        return wrapper

    def template(self, template_name, context=None):
        if context is None:
            context = {}
        return self.templates_env.get_template(template_name).render(**context)

    @staticmethod
    def default_response(response):
        response.status_code = 404
        response.text = "Not Found"

    def find_handler(self, request_path):
        for path, handler in self.routes.items():
            parse_result = parse(path, request_path)
            if 'q' in inspect.getfullargspec(handler).args:  # Not working
                q = self.q.replace('q=', '')
            else:
                q = None
            if parse_result is not None:
                return handler, q, parse_result.named
        return None, None, None

    def handle_request(self, request):
        response = Response()
        print(f'handle_request: {request.path}')
        handler, q, kwargs = self.find_handler(request_path=request.path)
        if handler is not None:
            if inspect.isclass(handler):
                handler = getattr(handler(), request.method.lower(), None)
            if handler is None:
                raise AttributeError("Method not allowed")
            if q is None:
                handler(request, response, **kwargs)
            else:
                print(q)
                handler(request=request, response=response, q=q, **kwargs)
        else:
            self.default_response(response)
        return response

    def create_docs(self):
        @self.route('/docs')
        def abc(request, resp):
            resp.text = f'{self.routes}'
