import re

def render(title, msg=''):
    return simple_template(msg_template, {'title': title, 'msg': msg})

def simple_template(string, context):
    def repl(m):
        return context[m.group(1).strip()]
    return re.sub('{{(.*?)}}', repl, string)
    
msg_template = """<html><head>
<title>{{title}}</title>
<style>
    body {font-family: Helvetica, Arial, sans-serif; color: #666; margin: 30px}
    h1 {font-size: 32px; margin-left: -2px; margin-top: 0px;}
    .server { line-height: 1em }
</style>
</head><body>
<div class="server">sovereign</div>
<h1>{{title}}</h1>
<p>{{msg}}</p>
</body></html>"""