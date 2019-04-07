from datetime import datetime
import random
from mongoengine.queryset.manager import queryset_manager
from slugify import slugify
from app import db


class User(db.DynamicDocument):
    # required=True 表明此字段必须填写
    email = db.StringField(required=True)
    # max_length 表明字符串字段的最大长度
    first_name = db.StringField(max_length=50)
    last_name = db.StringField(max_length=50)

    def __str__(self):  # 建议: 给每个模型增加 __str__ 方法，它返回一个具有可读性的字符串表示模型，可在调试和测试时使用
        return self.first_name + ' ' + self.last_name


class Category(db.Document):
    name = db.StringField(max_length=64, required=True)
    # unique=True 表明此字段的值必须在整个 collection 中唯一
    slug = db.StringField(max_length=64, unique=True)
    caption = db.StringField()
    # 自引用
    parent = db.ReferenceField('self', reverse_delete_rule=db.DENY)

    meta = {
        'collection': 'classes',  # 更改数据库中默认的 collection 名称
        'indexes': ['parent'],
        'ordering': ['slug']
    }

    def __str__(self):
        return self.name


class Tag(db.Document):
    name = db.StringField(max_length=64, required=True)
    slug = db.StringField(max_length=64, unique=True)

    def __str__(self):
        return self.name


class Comment(db.EmbeddedDocument):
    '''EmbeddedDocument 表明它是一个可被嵌入其它文档的对象，比如嵌套到下面的 Post 中'''
    content = db.StringField()
    name = db.StringField(max_length=120)

    def __str__(self):
        return self.name


class Post(db.Document):
    title = db.StringField(max_length=120, required=True)
    slug = db.StringField(max_length=64, unique=True)
    # ReferenceField 是引用字段，在数据库中真正存储的是 ObjectID
    # reverse_delete_rule=db.CASCADE 定义了，author 这个引用字段当被引用的对象删除时，它如何处理
    # 比如 author 引用了用户 ross，当我们删除 ross 时，由于定义了 db.CASCADE，所以会 [级联删除] ross 用户所发表过的所有 Post 文章
    author = db.ReferenceField(User, reverse_delete_rule=db.CASCADE)
    category = db.ReferenceField(Category, reverse_delete_rule=db.NULLIFY)
    # ListField 表明它是一个列表，可以保存多个其它类型的字段值，比如 StringField、ReferenceField、EmbeddedDocumentField 都可以
    tags = db.ListField(db.ReferenceField(Tag, reverse_delete_rule=db.PULL))
    comments = db.ListField(db.EmbeddedDocumentField(Comment))
    # 创建的时间，建议在数据库中全部存储 UTC 时间
    # default=datetime.utcnow 表明不指定此字段的值时，它会默认保存当前的时间
    created_at = db.DateTimeField(default=datetime.utcnow)
    # 价格。需要数学计算时，请使用 DecimalField，不要用 FloatField (计算结果不对)
    price = db.DecimalField(default='0.00')
    # 是否发布
    published = db.BooleanField(default=True)

    meta = {
        'allow_inheritance': True,  # 允许被继承，比如下面的 TextPost 就继承自 Post
        'indexes': ['title', 'author'],  # 索引字段，后续按这两个字段值查询时可以加快速度
        'ordering': ['-created_at']  # 表示按 created_at 降序排列，没有减号表示升序排列
    }

    @queryset_manager
    def live_posts(doc_cls, queryset):
        '''非默认的objects查询集，此查询集只返回发布状态为True的博客文章'''
        return queryset.filter(published=True)

    def clean(self):
        '''
        MongoEngine allows you to create custom cleaning rules for your documents when calling save().
        By providing a custom clean() method you can do any pre validation / data cleaning.
        '''
        # 如果创建Post对象时没有提供slug，则根据title自动生成；如果提供了slug，用slugify再清理
        if self.slug:
            self.slug = slugify(self.slug)
        else:
            self.slug = slugify(self.title)
        # 判断slug是否唯一
        filters = dict(slug=self.slug)
        if self.id:
            filters['id__ne'] = self.id
        # 不能用 exist = self.__class__.objects(**filters)，因为可能创建 TextPost 对象时，其它子类有相同的 slug
        exist = Post.objects(**filters)
        if exist.count():
            self.slug = "{0}-{1}".format(self.slug, random.getrandbits(32))

    def __str__(self):
        return self.title


class TextPost(Post):  # 继承自 Post 模型，所以它也有 title、author 等字段
    content = db.StringField()


class ImagePost(Post):
    image_path = db.StringField()


class LinkPost(Post):
    link_url = db.StringField()
