import os
from dotenv import load_dotenv
from flask import Flask
from flask_mongoengine import MongoEngine


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

app = Flask(__name__)

# 配置项
app.config['MONGODB_DB'] = 'test'
app.config['MONGODB_HOST'] = '127.0.0.1'
app.config['MONGODB_PORT'] = 27017
app.config['MONGODB_USERNAME'] = None
app.config['MONGODB_PASSWORD'] = None

# 初始化插件
db = MongoEngine(app)


@app.shell_context_processor
def make_shell_context():
    '''Flask Shell上下文'''
    return dict(db=db, User=User, Category=Category, Tag=Tag,
                Comment=Comment, Post=Post, TextPost=TextPost,
                ImagePost=ImagePost, LinkPost=LinkPost)


@app.route("/")
def hello():
    return "Hello World!"


# 写在最后是为了防止循环导入，因为 models.py 文件也会导入当前文件 app.py 中的 db
from models import User, Category, Tag, Comment, Post, TextPost, ImagePost, LinkPost
