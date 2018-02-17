# 接上一天
# day3 

补充：
###### 关于实例化
```python
v1 = ['view.xxx.path.Role','view.xxx.path.']
```
> 回顾
#### 为什么用 django restframework？
关于认证、权限、节流，只需要写类，就可以实现他们的方法返回值就可。
它帮我们实现了一些功能。

#### 设计好的点？
  单独视图配置和全局配置， 它的全局配置类似django中间件(importlib + 反射)。
  动态配置可扩展（用户下单后，通过短信、邮件等提醒）。
  
#### 关于它的原理：
  基于 cbv，和 django 继承的是同一个。
  请求进来之后，先执行 dispatch （ 五大功能，都是在 dispatch 里面实现）。
  - 先执行 as_view()
  - view 函数
    obj = cls()
    。。。
    return self.dispatch()
  - dispatch
    - 封装 request
    - 版本
    - 认证 -> request.user -> 循环对象，执行_authticate
    - 权限
    - 节流

#### 新 request对象(request，认证相关)
  如果新 req 对象里面没有你要的东西，就去旧的 request 里面找。
          request.query_params
          request.POST
          request.Meta  
          
          
> 今日内容
1. 版本，
2. 解析器，
3. 序列化，
4. 分页

版本和解析器一旦配置好，基本可以不用再动。
序列化：
  - QuuerySet 类型 -> list,dict
  - 请求验证
django form 组件也可以用在 restframework。


### 1. 为什么要有版本？ 
  如果是version_1，就返回111
  如果是version_2，就返回22
  如果是version_3，就返回3
  自己可以在 url 里面写，然后 request 获取再判断就可以。
  
  但是d_rfw 已经帮你做好了。
  from rest_framework.versioning
  versioning_class = QueryParameterVersioning  # 这个就是帮你获取 version 的值。
  推荐:
  versioning_class = UrlPathVersioning
  
###### 版本源码执行流程
  ```python
  1. 进来先到 dispatch()
     def dispatch(self, request, *args, **kwargs):
  2. self.initial(request, *args, **kwargs)
  3.  # 处理版本信息
      # 这两句是处理版本信息，点击self.determine_version
        version, scheme = self.determine_version(request, *args, **kwargs)
        request.version, request.versioning_scheme = version, scheme
  4. def determine_version(self, request, *args, **kwargs):
         if self.versioning_class is None:
            return (None, None)
         scheme = self.versioning_class()
         return (scheme.determine_version(request, *args, **kwargs), scheme)
  5. URLPathVersioning.determine_version(self, request, *args, **kwargs):
     return version
  6. 封装到 request 中
     request.version, request.versioning_scheme = version, scheme
  7. 使用
     class URLPathVersion(APIView):
    # 关于 urlpath
    versioning_class = URLPathVersioning

    def get(self,request,*args,**kwargs):
        print(request.version)
        print(request.versioning_scheme)
  ```
  
  
  
### 2. 解析器
  解析器对请求的数据解析
  d_rdw 是针对请求头解析。
  
  request.POST 不一定拿得到值，这个和 Content_Type 有关。
  - Content_Type : application/url-encoding
    - 以这个发送的话，post 和 body 里面都会有值。
    - 弊端：只有在 body 里可以拿到Bytes 类型的变态大叔。

  - d_rdw： parse_classes = [JONParse ,FormDataParse]
  - 最常用的即 JSONParse
  解析器小总结：
    - 何时执行？ 只有执行 request.data/request.FILES/reqeust.POST
      - 根据 content_type头，判断是否支持。
```python
2. rest framework解析器
		请求的数据进行解析：请求体进行解析。表示服务端可以解析的数据格式的种类。
		
			Content-Type: application/url-encoding.....
			request.body
			request.POST
			
			Content-Type: application/json.....
			request.body
			request.POST
		
		客户端：
			Content-Type: application/json
			'{"name":"alex","age":123}'
		
		服务端接收：
			读取客户端发送的Content-Type的值 application/json
			
			parser_classes = [JSONParser,]
			media_type_list = ['application/json',]
		
			如果客户端的Content-Type的值和 application/json 匹配：JSONParser处理数据
			如果客户端的Content-Type的值和 application/x-www-form-urlencoded 匹配：FormParser处理数据
		
		
		配置：
			单视图：
			class UsersView(APIView):
				parser_classes = [JSONParser,]
				
			全局配置：
				REST_FRAMEWORK = {
					'VERSION_PARAM':'version',
					'DEFAULT_VERSION':'v1',
					'ALLOWED_VERSIONS':['v1','v2'],
					# 'DEFAULT_VERSIONING_CLASS':"rest_framework.versioning.HostNameVersioning"
					'DEFAULT_VERSIONING_CLASS':"rest_framework.versioning.URLPathVersioning",
					'DEFAULT_PARSER_CLASSES':[
						'rest_framework.parsers.JSONParser',
						'rest_framework.parsers.FormParser',
					]
				}

```
  
### 3. **序列化** 重点！！！
  这 tm 是什么？
    - 序列化：    对象 --> 字符串，
    - 反序列化：  字符串 --> 对象。
    - 目前学过的：json/pickle

  restful 序列化 存在的意义：
    - 就是为了解决 QuerySet 的序列化问题。

models.py
```python
from django.db import models

# Create your models here.

class Menu(models.Model):
    name = models.CharField(max_length=32)

class Group(models.Model):
    title = models.CharField(max_length=32)
    mu = models.ForeignKey(to="Menu",default=1)

class UserInfo(models.Model):
    name = models.CharField(max_length=32)
    pwd = models.CharField(max_length=32)

    group = models.ForeignKey(to='Group')
    roles = models.ManyToManyField(to='Role')


class Role(models.Model):
    name = models.CharField(max_length=32)
```

复杂序列化
views.py
```python
a. 复杂序列化
解决方案一：
class MyCharField(serializers.CharField):
    def to_representation(self, value):
        data_list = []
        for row in value:
            data_list.append(row.name)
        return data_list


class UsersSerializer(serializers.Serializer):
    name = serializers.CharField()  # obj.name
    pwd = serializers.CharField()  # obj.pwd
    group_id = serializers.CharField()  # obj.group_id
    xxxx = serializers.CharField(source="group.title")  # obj.group.title
    x1 = serializers.CharField(source="group.mu.name")  # obj.mu.name
    # x2 = serializers.CharField(source="roles.all") # obj.mu.name
    x2 = MyCharField(source="roles.all")  # obj.mu.name


解决方案二：
class MyCharField(serializers.CharField):
    def to_representation(self, value):
        return {'id': value.pk, 'name': value.name}


class UsersSerializer(serializers.Serializer):
    name = serializers.CharField()  # obj.name
    pwd = serializers.CharField()  # obj.pwd
    group_id = serializers.CharField()  # obj.group_id
    xxxx = serializers.CharField(source="group.title")  # obj.group.title
    x1 = serializers.CharField(source="group.mu.name")  # obj.mu.name
    # x2 = serializers.CharField(source="roles.all") # obj.mu.name
    x2 = serializers.ListField(child=MyCharField(), source="roles.all")  # obj.mu.name


这是复杂序列化的第三种方法，也是极力推荐的方法   *************
class UserSerializer(serializers.Serializer):
    name = serializers.CharField()     # obj.name
    pwd = serializers.CharField()       # obj.pwd
    group_id = serializers.CharField()  # obj.group_id
    g_title = serializers.CharField(source='group.title')   # obj.group.title
    g_mu_name = serializers.CharField(source='group.mu.name') # obj.group.name

    # M2M，这样写的话，只能拿到 对象
    # roles = serializers.CharField(source='roles.all') # "roles": "<QuerySet [<Role: Role object>]>"
    roles = serializers.CharField(source='roles.all') # "roles": "<QuerySet [<Role: Role object>]>"

    xx = serializers.SerializerMethodField()
    def get_xx(self,obj):
        role_list = obj.roles.all()
        data_list = []
        for role_obj in role_list:
            data_list.append({'pk':role_obj.pk,'name':role_obj.name,})
        return data_list


不管哪种方法，都走这个视图
class UserView(APIView):
    def get(self,request,*args,**kwargs):
        self.dispatch
        # 方式一：用我们之前最简单粗暴的方法。
        # user_list = models.UserInfo.objects.all().values('name','pwd','group_id','group__title','group__mu__name')
        # return Response(user_list)

        # 方式二：多对象
        user_list = models.UserInfo.objects.all()
        # print(user_list)
        # obj = user_list.first()
        # o_name = obj.roles.all()
        # for i in o_name:
        #     print(i.name)
        ser = UserSerializer(instance=user_list,many=True)
        return Response(ser.data)

b. 基于 model。   在序列化里面继承了 ModelSerializer类
class PasswordValidator(object):
    def __init__(self, base):
        self.base = base

    def __call__(self, value):
        if value != self.base:
            message = '用户输入的值必须是 %s.' % self.base
            raise serializers.ValidationError(message)

    def set_context(self, serializer_field):
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        # 执行验证之前调用,serializer_fields是当前字段对象
        pass

#  注意这里继承的类：ModelSerializer
class UsersSerializer(serializers.ModelSerializer):
    x = serializers.CharField(source='name')
    class Meta:
        model = models.UserInfo
        # fields = "__all__"
        fields = ['name', 'pwd', 'x', 'group'] # 自定义字段时候要注意指定 source，source里面的数据必须是数据库有的。
        extra_kwargs = {
            'name': {'min_length': 6},
            'pwd': {'validators': [PasswordValidator(666), ]}}



# 使用
class UsersView(APIView):
    def get(self,request,*args,**kwargs):
        # self.dispatch
        user_list = models.UserInfo.objects.all()
        # [obj1,obj2,obj3]
        # 序列化。
        ser = UsersSerializer(instance=user_list,many=True,context={'request':request})
        return Response(ser.data)

    def post(self,request,*args,**kwargs):
        # 验证：对请求发来的数据进行验证。
        ser = UsersSerializer(data=request.data)
        if ser.is_valid():
            print(ser.validated_data)
        else:
            print(ser.errors)
        return Response('...')



c. 生成 url
class Users_Serializer(serializers.ModelSerializer):
    group = serializers.HyperlinkedIdentityField(view_name='detail')
    class Meta:
        model = models.UserInfo
        fields = '__all__'
        extra_kwargs = {
            'user': {'min_length': 6},
            'pwd': {'validators': [PasswordValidator(666),]}
        }

class Users_View(APIView):
    def get(self, request, *args, **kwargs):
        # 序列化，将数据库查询字段序列化为字典
        data_list = models.UserInfo.objects.all()
        ser = Users_Serializer(instance=data_list, many=True, context={'request': request})
        # 或
        # obj = models.UserInfo.objects.all().first()
        # ser = UserSerializer(instance=obj, many=False)
        return Response(ser.data)

    def post(self, request, *args, **kwargs):
        # 验证，对请求发来的数据进行验证
        print(request.data)
        ser = Users_Serializer(data=request.data)
        if ser.is_valid():
            print(ser.validated_data)
        else:
            print(ser.errors)

        return Response('POST请求，响应内容')



d. 自动生成 url    继承该类: HyperlinkedModelSerializer

class UsersSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.UserInfo
        fields = "__all__"
        # fields = ['id','name','pwd']

    class UsersView(APIView):
        def get(self,request,*args,**kwargs):
            self.dispatch
            # 方式一：
            # user_list = models.UserInfo.objects.all().values('name','pwd','group__id',"group__title")
            # return Response(user_list)

            # 方式二之多对象
            user_list = models.UserInfo.objects.all()
            # [obj1,obj2,obj3]
            ser = UsersSerializer(instance=user_list,many=True,context={'request':request})
            return Response(ser.data)



e. 关于请求数据验证
# 第一种：
class PasswordValidator(object):
    def __init__(self, base):
        self.base = base

    def __call__(self, value):
        if value != self.base:
            message = '用户输入的值必须是 %s.' % self.base
            raise serializers.ValidationError(message)

    def set_context(self, serializer_field):
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        # 执行验证之前调用,serializer_fields是当前字段对象
        pass


class UsersSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=6)
    pwd = serializers.CharField(error_messages={'required': '密码不能为空'}, validators=[PasswordValidator('666')])


# 第二种
class PasswordValidator(object):
    def __init__(self, base):
        self.base = base

    def __call__(self, value):
        if value != self.base:
            message = '用户输入的值必须是 %s.' % self.base
            raise serializers.ValidationError(message)

    def set_context(self, serializer_field):
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        # 执行验证之前调用,serializer_fields是当前字段对象
        pass


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserInfo
        fields = "__all__"
        extra_kwargs = {
            'name': {'min_length': 6},
            'pwd': {'validators': [PasswordValidator(666), ]}
        }


使用：
class UsersView(APIView):
    def get(self, request, *args, **kwargs):
        self.dispatch
        # 方式一：
        # user_list = models.UserInfo.objects.all().values('name','pwd','group__id',"group__title")
        # return Response(user_list)

        # 方式二之多对象
        user_list = models.UserInfo.objects.all()
        # [obj1,obj2,obj3]
        ser = UsersSerializer(instance=user_list, many=True, context={'request': request})
        return Response(ser.data)

    def post(self, request, *args, **kwargs):
        ser = UsersSerializer(data=request.data)
        if ser.is_valid():
            print(ser.validated_data)
        else:
            print(ser.errors)
        return Response('...')
```
