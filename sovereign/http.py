from template import render

### Http Responses ###
def Response(content='', headers=None, type='text/html', status="200 OK"):
    headers = headers or [('Content-Type', type)]
    def app(environ, start_response):
        start_response(status, headers)
        if isinstance(content, basestring):
            return (content,)
        return content
    return app

def BasicResponse(title, msg=""):
    return Response(content=render(title, msg))

def MovedPermanently(uri, headers=[]):
    return Response(status='301 Moved Permanently', headers=headers + [('Location', uri)])

def NotModified(headers=[]):
    return Response(status='304 Not Modified', headers=headers)

def Forbidden(content=render("403 Forbidden")):
    return Response(status='403 Forbidden', content=content)

def NotFound(content=render("404 Not Found")):
    return Response(status='404 Not Found', content=content)

def MethodNotAllowed(allowed=[]):
    return Response(status='405 Method Not Allowed', headers=[('Allow', " ,".join(allowed))])

def InternalServerError(content=render("500 Internal Server Error")):
    return Response(status="500 Internal Server Error", content=content)

def BadGateway(msg = "Name or service not known, bad domain name.", content=None):
    if content is None:
        content = render('502 Bad Gateway', msg)
    return Response(status="502", content=content)

def ServiceUnavailable(msg = "This service is temporarily unavailable.  Please try again later.", content=None):
    if content is None:
        content = render('503 Service Unavailable', msg)
    return Response(status="503", content=content)
