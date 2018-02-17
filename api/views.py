from django.shortcuts import render

# Create your views here.

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import BasePermission
from rest_framework.authentication import BaseAuthentication
from rest_framework.renderers import JSONRenderer,BrowsableAPIRenderer
from rest_framework.request import Request
from rest_framework import serializers
from rest_framework.versioning import URLPathVersioning
from . import models

#  a. 复杂序列化
# 解决方案一：
# class MyCharField(serializers.CharField):
#     def to_representation(self, value):
#         data_list = []
#         for row in value:
#             data_list.append(row.name)
#         return data_list
#
#
# class UsersSerializer(serializers.Serializer):
#     name = serializers.CharField()  # obj.name
#     pwd = serializers.CharField()  # obj.pwd
#     group_id = serializers.CharField()  # obj.group_id
#     xxxx = serializers.CharField(source="group.title")  # obj.group.title
#     x1 = serializers.CharField(source="group.mu.name")  # obj.mu.name
#     # x2 = serializers.CharField(source="roles.all") # obj.mu.name
#     x2 = MyCharField(source="roles.all")  # obj.mu.name
#
#
# 解决方案二：
# class MyCharField(serializers.CharField):
#     def to_representation(self, value):
#         return {'id': value.pk, 'name': value.name}
#
#
# class UsersSerializer(serializers.Serializer):
#     name = serializers.CharField()  # obj.name
#     pwd = serializers.CharField()  # obj.pwd
#     group_id = serializers.CharField()  # obj.group_id
#     xxxx = serializers.CharField(source="group.title")  # obj.group.title
#     x1 = serializers.CharField(source="group.mu.name")  # obj.mu.name
#     # x2 = serializers.CharField(source="roles.all") # obj.mu.name
#     x2 = serializers.ListField(child=MyCharField(), source="roles.all")  # obj.mu.name
#
#
# 这是复杂序列化的第三种方法，也是极力推荐的方法   *************
# class UserSerializer(serializers.Serializer):
#     name = serializers.CharField()     # obj.name
#     pwd = serializers.CharField()       # obj.pwd
#     group_id = serializers.CharField()  # obj.group_id
#     g_title = serializers.CharField(source='group.title')   # obj.group.title
#     g_mu_name = serializers.CharField(source='group.mu.name') # obj.group.name
#
#     # M2M，这样写的话，只能拿到 对象
#     # roles = serializers.CharField(source='roles.all') # "roles": "<QuerySet [<Role: Role object>]>"
#     roles = serializers.CharField(source='roles.all') # "roles": "<QuerySet [<Role: Role object>]>"
#
#     xx = serializers.SerializerMethodField()
#     def get_xx(self,obj):
#         role_list = obj.roles.all()
#         data_list = []
#         for role_obj in role_list:
#             data_list.append({'pk':role_obj.pk,'name':role_obj.name,})
#         return data_list
#
#
# 不管哪种方法，都走这个视图
# class UserView(APIView):
#     def get(self,request,*args,**kwargs):
#         self.dispatch
#         # 方式一：用我们之前最简单粗暴的方法。
#         # user_list = models.UserInfo.objects.all().values('name','pwd','group_id','group__title','group__mu__name')
#         # return Response(user_list)
#
#         # 方式二：多对象
#         user_list = models.UserInfo.objects.all()
#         # print(user_list)
#         # obj = user_list.first()
#         # o_name = obj.roles.all()
#         # for i in o_name:
#         #     print(i.name)
#         ser = UserSerializer(instance=user_list,many=True)
#         return Response(ser.data)


#  b. 基于 model。   在序列化里面继承了 ModelSerializer类
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



#  c. 生成 url
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



#  d. 自动生成 url    继承该类: HyperlinkedModelSerializer

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



#  e. 请求数据验证
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


# 使用：
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