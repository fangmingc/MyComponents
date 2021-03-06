## Django权限管理
- 必须会的技能
- 开发成组件(单独app)，不为某个特定的需求写功能

### 需求分析
- 独立app--rbac，与业务逻辑分开
	- 权限管理存放在数据库
	- 使用时验证请求的权限
- 分配权限
	- 按照URL分

### 设计
#### 初版设计
- 需要有数据库存放权限和URl关系
	- 权限表(Permission)
		- ID
		- url，URL，最长64字符
		- title，URL别名，最长32字符
- 需要用户
	- 用户表(User)
		- ID
		- username，用户名，最长32字符
		- password，密码，最长64字符
		- permission，与权限表多对多
- 权限表和用户表是多对多关系（自动生成）
	- 权限--用户
		- ID
		- UserID
		- PermissionID
- 这样的设计没有问题，但是用起来很麻烦，因为每个用户单独分配权限，人多了旧非常繁琐

#### 第二版设计
- 增加角色表,角色和权限多对多关系，用户和角色多对多关系
- 权限表添加字段判断是否是菜单，通常一个组中菜单会作为组的跳转url
	- 用户表(User)
		- ID
		- username，用户名，最长32字符
		- password，密码，最长64字符
	- 角色表(Role)
		- ID
		- title，角色名，最长32字符
		- user，与用户表多对多
	- 权限表(Permission)
		- ID
		- url，URL，最长64字符
		- title，URL别名，最长32字符
		- is_menu，是否是菜单，布尔值
		- role，与角色表多对多
	- 角色--权限（自动生成）
		- ID
		- RoleID
		- PermissionID
	- 角色--用户（自动生成）
		- ID
		- RoleID
		- UserID
- 通过django自带的admin填充用户数据流程：
	- 设置超级用户：python manage.py createsuperuser
	- 启动项目，进入admin管理后台
	- 添加权限数据
- 编写好测试用的url与相应的视图函数
- 登录认证
	- 编写中间件
		- 判断当前请求是否是白名单如（login,admin...）
		- 判断是否登录
		- 验证权限

	```python
	def process_request(self, request):
	    # 白名单路径
	    for url in settings.VALID_URLS:
	        if match("^{0}".format(url), request.path_info):
	            return None
	    # 检测是否登录
	    if not request.session.get(settings.PERMISSION):
	        return redirect("/login/")
	    # 验证权限
	    flag = False
	    for url in request.session.get("permission_url_list"):
	        if match("^{0}$".format(url), request.path_info):
	            flag = True
	            break
	    if flag:
	        # 通过权限验证
	        return None
	    else:
	        # 未通过权限验证
	        return HttpResponse("无权访问")
	```

	- 新增sevices文件夹，在其中新建rbac.py，编写初始化权限函数，并存入session

	```python
	def init_permission(user, request):
	    """
	    初始化权限信息，获取权限url列表放置在session中
	    """
	    url_list = []
	    for row in user.first().role.all().values_list("permission__url").distinct():
	        url_list.append(row[0])
	    request.session["permission_url_list"] = url_list
	```
	- 编写登录视图函数，初始化用户权限数据
- 文件结构

	```
	│  admin.py
	│  apps.py
	│  models.py
	│  __init__.py
	├─middleware
	│      rbac.py
	│      __init__.py
	└─services
	       init_permission.py
	       __init__.py
	```

#### 第三版设计
- 增加组，多个权限url隶属于一个组，通常一个组意味着同一个页面上的一些url
- 增加菜单，多个组隶属一个菜单，通常需要组中的菜单url生成页面上的二级菜单
- 权限表新增code字段，申明在组中的功能
	- 用户表(User)
		- ID
		- username，用户名，最长32字符
		- password，密码，最长64字符
	- 角色表(Role)
		- ID
		- title，角色名，最长32字符
		- user，与用户表多对多
	- 权限表(Permission)
		- ID
		- url，URL，最长64字符
		- title，URL别名，最长32字符
		- is_menu，是否是菜单，布尔值
		- role，与角色表多对多
		- code，申明在组中的功能，最长32字符
		- group，所属组，外键权限组
	- 权限组(Group)
		- ID
		- title，权限组名，最长16字符
		- menu，所属菜单，外键菜单表
	- 菜单(Menu)
		- ID
		- title，菜单名，最长16字符
	- 角色--权限（自动生成）
		- ID
		- RoleID
		- PermissionID
	- 角色--用户（自动生成）
		- ID
		- RoleID
		- UserID
- 通过django自带的admin填充用户数据
- 编写好测试url与视图函数
- 登录验证
	- 修改中间件

	```python
	def process_request(self, request):
	    # 白名单路径
	    for url in settings.VALID_URLS:
	        if match("^{0}$".format(url), request.path_info):
	            return None
	
	    # 检测是否登录
	    if not request.session.get(settings.PERMISSION_URL_DICT_KEY):
	        return redirect("/login/")
	
	    # 验证权限
	    flag = False
	    for group_id, group_dict in request.session.get(settings.PERMISSION_URL_DICT_KEY).items():
	        for url in group_dict["urls"]:
	            if match("^{0}$".format(url), request.path_info):
	                flag = True
	                request.code_list = group_dict["code"]
	                break
	    if flag:
	        # 通过权限验证
	        return None
	    else:
	        # 未通过权限验证
	        return HttpResponse("无权访问")
	```
	- 修改初始化权限函数

	```python
	def init_permission(user, request):
	    """
	    初始化权限信息，获取权限url列表放置在session中
	    """
	    permission_list = user.first().role.all().values(
	        "permission__title",
	        "permission__url",
	        "permission__code",
	        "permission__is_menu",
	        "permission__group_id",
	        "permission__group__menu_id",
	        "permission__group__menu__title",
	    ).distinct()
	
	    menu_list = []
	    group_dict = {}
	    for row in permission_list:
	        """
	权限组字典结构
	
	{
	    组id: {
	        "code": ["list", "add", "del", "edit", ...],
	        "urls": ["/index/", "/add/(\d+)/", ...],
	    }
	    ...
	}
	        """
	        if row["permission__is_menu"]:
	            menu_list.append({
	                "menu_id": row["permission__group__menu_id"],
	                "menu_title": row["permission__group__menu__title"],
	                "title": row["permission__title"],
	                "url": row["permission__url"],
	                "is_menu": row["permission__is_menu"],
	            })
	        group_dict.setdefault(row["permission__group_id"], {}).setdefault("code", []).append(row["permission__code"])
	        group_dict.setdefault(row["permission__group_id"], {}).setdefault("urls", []).append(row["permission__url"])
	
	    request.session[settings.PERMISSION_MENU_LIST_KEY] = menu_list
	    request.session[settings.PERMISSION_URL_DICT_KEY] = group_dict
	```
	- 编写模板自定义标签，用于生成菜单HTML，其中inclusion_tag指向的html为菜单模板，并配置相应静态文件
		- django会自动寻找所有的static，同时项目层级的static优先级最高，只要和项目层级的static区分开就可以使用

	```python
	@register.inclusion_tag("menu.html")
	def menu_html(request):
	    """
	    生成菜单HTML
	    """
	    menu_dict = {}
	    for item in request.session.get(settings.PERMISSION_MENU_LIST_KEY):
	        """
	菜单字典结构
	
	{
	    菜单id: {
	        "menu_id": 菜单id,
	        "menu_title": 菜单名,
	        "active": 是否展开,
	        "children": [
	            {"title": 二级菜单名, "url": 菜单url, "active": 是否突出显示},
	            ...
	            ]
	    }
	    ...
	}
	        """
	        temp_dict = menu_dict.setdefault(item["menu_id"], {})
	        temp_dict.setdefault("menu_id", item["menu_id"])
	        temp_dict.setdefault("menu_title", item["menu_title"])
	
	        # 匹配到符合当前url则设置初始状态
	        active = False
	        if re.match("^{0}$".format(item["url"]), request.path_info):
	            active = True
	            temp_dict.setdefault("active", active)
	
	        temp_dict.setdefault("children", []).append({"title": item["title"], "url": item["url"], "active": active})
	    return {"menu_dict": menu_dict}
	```
- 文件结构

```
│  admin.py
│  apps.py
│  models.py
│  tests.py
│  views.py
│  __init__.py
├─middleware
│      rbac.py
│      __init__.py
├─services
│      init_permission.py
│      __init__.py
├─static
│  └─rbac
│          rbac.css
│          rbac.js
└─templatetags
        rbac.py
```

- [第三版文件](https://github.com/fangmingc/Python/tree/master/Frame/Django/rbac_version_0.3))

#### 第四版--完善设计
- 到第三版已经基本完成权限的管理和应用，不过实际中仍有问题
	- 示例：active效果是增加--OK--

	```
	用户管理 <--OK-->
	---- 用户列表 <--OK-->
	---- 订单列表 <>
	订单管理 <>
	---- 报   表 <>
	```
	- 问题：当用户停留在二级菜单用户列表(/userinfo/)，此页面上有增加(/userinfo/add/)编辑(/userinfo/edit/)/删除(/userinfo/del/)链接，在点击链接后，二级菜单用户列表的active显示不会出现
	- 原因：在自定义标签的函数中匹配当前请求的url时，只能匹配二级菜单的url(/userinfo/)，如果是/userinfo/add/就无法给二级菜单添加上active属性
- 解决方案一：
	- 在现有基础上修改，在自定义标签函数中对所有权限url判断，当符合某一条时，给该条权限所属组/组所属菜单增加active
	- 修改初始化权限函数，增加组ID；修改自定义标签函数；

	```python
	@register.inclusion_tag("menu.html")
	def menu_html(request):
	    """
	    生成菜单HTML
	    """
		# 初步处理，给url所属组添加active
		"""
	menu_dict = {
	    菜单ID: {
	        组1ID: {
	            "menu": {'title': .., 'url': .., 'is_menu': .., 'group_id': .., 'menu_id': .., 'menu_title': .., "active": ..},
	            "urls": ['/userinfo/','/userinfo/add/','/userinfo/del/(\d+)/','/userinfo/edit/(\d+)/'...]
	        },
	        组2ID: {
	            "menu": {'title': '...', 'url': '...', 'is_menu': .., 'group_id': .., 'menu_id': .., 'menu_title': "..."},
	            "urls": ['/order/','/order/add/','/order/del/(\d+)/','/order/edit/(\d+)/'...]
	        }
	        ...
	    }
	    ...
	}
		"""
	    menu_dict = {}
	    for item in request.session.get(settings.PERMISSION_MENU_LIST_KEY):
	        tpd1 = menu_dict.setdefault(item["menu_id"], {})
	
	        tpd2 = tpd1.setdefault(item["group_id"], {})
	        tpd2.setdefault("menu", item)
	        if re.match("^{0}$".format(item["url"]), current_url):
	            tpd2.setdefault("menu", item).setdefault("active", True)
	    # 二次处理，与之前模板处理契合
	    """
	menu_dict = {
	    菜单ID: {
	        "menu_title": "",
	        "active": ""
	        "children": [
	            {'title': '用户列表', 'url': '/userinfo/', "active": True},
	            {'title': '用户列表', 'url': '/userinfo/', "active": True},
	            ...
	        ]
	    }
	}
	    """
	
	    sub_menu_dict = {}
	    for k, item in menu_dict.items():
	        tpd = sub_menu_dict.setdefault(k, {})
	
	        for value in item.values():
	            tpd.setdefault("title", value["menu"]["menu_title"])
	            if value["menu"].get("active"):
	                tpd.setdefault("active", value["menu"].get("active"))
	            tpd.setdefault("urls", []).append({"title": value["menu"]["title"], "url": value["menu"]["url"], "active": value["menu"].get("active")})
	
	    return {"menu_dict": sub_menu_dict}
	```
	- 优点：在原有基础上直接修改，无需修改其他地方
- 解决方案二
	- 修改权限表结构，去掉is_menu字段，增加组内菜单字段menu_group，外键权限表本身，当为空时该url为二级菜单
		- 权限表(Permission)
			- ID
			- url，URL，最长64字符
			- title，URL别名，最长32字符
			- menu_group，组内菜单，外键自身，允许为空
			- role，与角色表多对多
			- code，申明在组中的功能，最长32字符
			- group，所属组，外键权限组
	- 修改初始化权限函数，替换is_menu为组内ID，获取所有url；

	```python
	def init_permission(request, user):
	    """
	    初始化权限信息，并添加到session
	    """
	    permission_list = user.role.all().values(
	        "permission__title",
	        "permission__url",
	        "permission__code",
	        "permission__group_menu_id",
	        "permission__group_id",
	        "permission__group__title",
	        "permission__group__menu_id",
	        "permission__group__menu__title",
	    ).distinct()
	
	    # 分类处理权限信息
	    group_dict = {}
	    menu_dict = {}
	    for item in permission_list:
	        """
	权限组字典结构
	
	{
	    组ID: {
	        "code": ["", "", "", ...]
	        "urls": ["url", "url2", "url3", ...]
	    }
	    ...
	}
	        """
	        group_dict.setdefault(item["permission__group_id"], {}).setdefault("code", []).append(item["permission__code"])
	        group_dict.setdefault(item["permission__group_id"], {}).setdefault("urls", []).append(item["permission__url"])
	
	        """
	菜单字典结构
	
	{
	    组ID: {
	        "menu": {"url": 组内菜单url, "menu_title": "所属组名", "menu_title": "所属菜单名", "menu_id": "所属菜单ID"},
	        "urls": ["组url", "组url2", "组url3", ...]
	    }
	    ...
	}
	        """
	        # tpd = menu_dict.setdefault(item["permission__group__menu_id"], {})
	        tpd = menu_dict.setdefault(item["permission__group_id"], {})
	        tpd.setdefault("urls", []).append(item["permission__url"])
	        # 给每个组设置组内菜单
	        if not item["permission__group_menu_id"]:
	            tpd.setdefault("menu", {"title": item["permission__title"], "url": item["permission__url"],
	                                    "group_title": item["permission__group__title"],
	                                    "menu_title": item["permission__group__menu__title"],
	                                    "menu_id": item["permission__group__menu_id"]})
	    request.session[settings.PERMISSION_GROUP] = group_dict
	    request.session[settings.PERMISSION_MENU] = menu_dict
	```
	- 修改自定义标签函数；

	```
	@register.inclusion_tag("menu.html")
	def menu_html(request):
	    """
	    自动生成菜单HTML
	    """
	    for k, group in request.session.get(settings.PERMISSION_MENU).items():
	        for url in group["urls"]:
	            if match("^{0}$".format(url), request.path_info):
	                group["menu"]["active"] = True
	                break
	        else:
	            continue
	        break
	    """
	    # 抛出异常法
	    class TempError(Exception):
	        pass
	    try:
	        for k, group in request.session.get(settings.PERMISSION_MENU).items():
	            for url in group["urls"]:
	                if match("^{0}$".format(url), request.path_info):
	                    group["menu"]["active"] = True
	                    raise TempError
	    except TempError:
	        pass
	    # 函数法
	    def temp(temp_dict, current_url):
	        for k, group in temp_dict:
	            for url in group["urls"]:
	                if match("^{0}$".format(url), current_url):
	                    group["menu"]["active"] = True
	                    return
	    temp()
	    """
	    menu_dict = {}
	    for k, group in request.session.get(settings.PERMISSION_MENU).items():
	        """
	菜单字典结构
	
	{
	    菜单ID: {
	        "title": 菜单名,
	        "active": 是否默认展开,
	        "children": [
	            {"title": 组内菜单名, "url": 组内菜单url, "active": 是否默认选中},
	            ...
	        ]
	    }
	    ...
	}
	        """
	        tpd = menu_dict.setdefault(group["menu"]["menu_id"], {})
	        tpd.setdefault("title", group["menu"]["menu_title"])
	        if group["menu"].get("active"):
	            tpd.setdefault("active", True)
	        tpd.setdefault("children", []).append({
	            "title": group["menu"]["title"], "url": group["menu"]["url"], "active": group["menu"].get("active", False)
	        })
	
	    return {"menu_dict": menu_dict}
	```
	- 文件结构

	```
	│  admin.py
	│  apps.py
	│  models.py
	│  tests.py
	│  views.py
	│  __init__.py
	├─middleware
	│  └─ rbac.py
	├─migrations
	│  └─ __init__.py
	├─services
	│  └─ rbac.py
	├─static
	│  └─ rbac
	│          rbac.css
	│          rbac.js
	└─templatetags
	   └─ rbac.py
	```









