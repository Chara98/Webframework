from api import API

app = API()


@app.route('/co')
class Co:
    @staticmethod
    def get(req, resp):
        resp.text = 'Books Page'


@app.route('/home/{name}')
def home(request, response, name, q):
    response.body = app.template("index.html", context={"query": f'{q}', "name": f"{name}", "title": "Best Framework"}).encode()


@app.route('/about')
def about(request, response):
    if request.method == 'POST':
        response.text = 'hola'
    else:
        response.text = "Hello from the ABOUT page"
