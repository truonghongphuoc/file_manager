from flask import Flask, send_from_directory, request, redirect, url_for, render_template, make_response
from werkzeug.utils import secure_filename
from werkzeug import Request, url_decode
from flask_restful import Resource, Api
import os
import shutil
import hashlib


UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') if os.environ.get('UPLOAD_FOLDER') else os.path.abspath('upload_folder')
DELETED_FILES = os.environ.get('DELETED_FILES') if os.environ.get('DELETED_FILES') else os.path.abspath('deleted_files')
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'yml'])

basedir = os.path.abspath(os.path.dirname(__file__))

for folder in (UPLOAD_FOLDER, DELETED_FILES):
    if not os.path.exists(folder):
        os.makedirs(folder)


class MethodRewriteMiddleware(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if 'METHOD_OVERRIDE' in environ.get('QUERY_STRING', ''):
            args = url_decode(environ['QUERY_STRING'])
            method = args.get('__METHOD_OVERRIDE__')
            if method:
                environ['REQUEST_METHOD'] = method
        return self.app(environ, start_response)


app = Flask(__name__)
app.wsgi_app = MethodRewriteMiddleware(app.wsgi_app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DELETED_FILES'] = DELETED_FILES
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

api = Api(app)


class Home(Resource):
    def get(self):
        current_files = get_files(UPLOAD_FOLDER)
        deleted_files = get_files(DELETED_FILES)
        headers = {'Content-Type': 'text/html'}
        return make_response(render_template('files.html', current_files=current_files, deleted_files=deleted_files),
                             200, headers)


class File(Resource):
    def get(self, filename):
        """Retrieve single file with specific name"""
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    def delete(self, filename):
        """Delete a single file with specific name"""
        file = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(file):
            shutil.move(file, os.path.join(app.config['DELETED_FILES'], filename))
            return {"message": "File %s had been deleted, to restore the file, please contact administrator" % filename}
        else:
            return {"message": "Deleted failed.File %s does not exists in the system" % filename}


class Files(Resource):
    def get(self):
        """List files on the server."""
        #current_files = get_files(UPLOAD_FOLDER)
        # deleted_files = get_files(DELETED_FILES)
        # headers = {'Content-Type': 'text/html'}
        # return make_response(render_template('files.html', current_files=current_files, deleted_files=deleted_files),
        #                      200, headers)
        return get_files(UPLOAD_FOLDER)


    def post(self):
        """Upload a new file to server"""
        try:
            file = request.files['file']
        except:
            file = None
            return {"message": "Please select a file to upload"}
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            return redirect(url_for('file', filename=filename))
        else:
            return {"message": "File is not valid"}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_files(folder):
    list = []
    for filename in os.listdir(folder):
        path = os.path.join(folder, filename)
        if os.path.isfile(path):
            list.append({"name": "%s" % filename})
    return list


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


api.add_resource(Home, '/')
api.add_resource(Files, '/files')
api.add_resource(File, '/file/<string:filename>')

app.run(port=5000)
