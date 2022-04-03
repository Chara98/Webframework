from webob import Request, Response
from parse import parse
from jinja2 import Environment, FileSystemLoader
from requests import Session as RequestsSession
from wsgiadapter import WSGIAdapter as RequestsWSGIAdapter
import inspect
import os


class API:
    def __init__(self, templates_dir='templates'):
        self.funcs = []
        self.routes = {}
        self.templates_env = Environment(loader=FileSystemLoader(os.path.abspath(templates_dir)))

    def __call__(self, environ, start_response):
        request = Request(environ)
        self.query = environ['QUERY_STRING']
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
            q = self.query
            if parse_result is not None:
                if q != '':
                    return handler, q, parse_result.named
                else:
                    return handler, parse_result.named
        return None, None

    def handle_request(self, request):
        response = Response()
        if self.query != '':
            handler, *kwargs = self.find_handler(request_path=request.path)
            query = kwargs[0].split('&')
            query = {i.split('=')[0]: i.split('=')[1] for i in query}
            query.update(kwargs[1])
            kwargs = query

            for key in set(query).difference(inspect.getfullargspec(handler).args):
                del query[key]
        else:
            handler, kwargs = self.find_handler(request_path=request.path)

        if handler is not None:
            if inspect.isclass(handler):
                handler = getattr(handler(), request.method.lower(), None)
            if handler is None:
                raise AttributeError("Method not allowed")
            handler(request, response, **kwargs)
        else:
            self.default_response(response)
        return response
