'''
a.基本操作:
class UsersSerializer(serializers.Serializer):
    name = serializers.CharField()
    pwd = serializers.CharField()


class UsersView(APIView):
    def get(self, request, *args, **kwargs):
        self.dispatch
        # 方式一：
        # user_list = models.UserInfo.objects.all().values('name','pwd','group__id',"group__title")
        # return Response(user_list)

        # 方式二之多对象
        # user_list = models.UserInfo.objects.all()
        # ser = UsersSerializer(instance=user_list,many=True)
        # return Response(ser.data)

        # 方式二之单对象
        user = models.UserInfo.objects.all().first()
        ser = UsersSerializer(instance=user, many=False)
        return Response(ser.data)


b.跨表


class UsersSerializer(serializers.Serializer):
    name = serializers.CharField()
    pwd = serializers.CharField()
    group_id = serializers.CharField()
    xxxx = serializers.CharField(source="group.title")
    x1 = serializers.CharField(source="group.mu.name")


class UsersView(APIView):
    def get(self, request, *args, **kwargs):
        self.dispatch
        # 方式一：
        # user_list = models.UserInfo.objects.all().values('name','pwd','group__id',"group__title")
        # return Response(user_list)

        # 方式二之多对象
        user_list = models.UserInfo.objects.all()
        ser = UsersSerializer(instance=user_list, many=True)
        return Response(ser.data)


c.复杂序列化
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


解决方案三（ * ）：
class UsersSerializer(serializers.Serializer):
    name = serializers.CharField()  # obj.name
    pwd = serializers.CharField()  # obj.pwd
    group_id = serializers.CharField()  # obj.group_id
    xxxx = serializers.CharField(source="group.title")  # obj.group.title
    x1 = serializers.CharField(source="group.mu.name")  # obj.mu.name
    # x2 = serializers.CharField(source="roles.all") # obj.mu.name
    # x2 = serializers.ListField(child=MyCharField(),source="roles.all") # obj.mu.name
    x2 = serializers.SerializerMethodField()

    def get_x2(self, obj):
        obj.roles.all()
        role_list = obj.roles.filter(id__gt=1)
        data_list = []
        for row in role_list:
            data_list.append({'pk': row.pk, 'name': row.name})
        return data_list


以上三种都是使用相同的视图：
class UsersView(APIView):
    def get(self, request, *args, **kwargs):
        self.dispatch
        # 方式一：
        # user_list = models.UserInfo.objects.all().values('name','pwd','group__id',"group__title")
        # return Response(user_list)

        # 方式二之多对象
        user_list = models.UserInfo.objects.all()
        # [obj1,obj2,obj3]
        ser = UsersSerializer(instance=user_list, many=True)
        return Response(ser.data)


d.基于Model


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserInfo
        fields = "__all__"
        # fields = ['name', 'pwd','group']
        depth = 1


class UsersView(APIView):
    def get(self, request, *args, **kwargs):
        self.dispatch
        # 方式一：
        # user_list = models.UserInfo.objects.all().values('name','pwd','group__id',"group__title")
        # return Response(user_list)

        # 方式二之多对象
        user_list = models.UserInfo.objects.all()
        # [obj1,obj2,obj3]
        ser = UsersSerializer(instance=user_list, many=True)
        return Response(ser.data)


e.生成URL


class UsersSerializer(serializers.ModelSerializer):
    group = serializers.HyperlinkedIdentityField(view_name='detail')

    class Meta:
        model = models.UserInfo
        fields = "__all__"
        fields = ['name', 'pwd', 'group']
        depth = 1


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


f.全局生成URL


class UsersSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.UserInfo
        fields = "__all__"

        # fields = ['id','name','pwd']


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


请求数据验证：

a.


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


b.


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

'''