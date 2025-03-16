# 自定义主题目录

这个目录用于存放自定义主题。

## 如何使用自定义主题

1. 在 `themes` 目录下创建一个新的文件夹，作为您的主题名称，例如 `mytheme`
2. 在主题文件夹中创建以下文件：
   - `index.html` - 首页模板
   - `post.html` - 文章页模板
   - `tags.html` - 标签列表页模板
   - `tag.html` - 单个标签页模板
   - `rss.xml` - RSS订阅模板
   - `css/style.css` - 样式文件

3. 在 `config.yml` 中设置主题：
   ```yaml
   # 主题设置
   theme: 'mytheme'
   ```

您可以参考 `custom` 目录中的示例文件，或者查看内置主题的源代码作为参考。
内置主题位于 Python 安装目录下的：
```
site-packages/cato/templates/themes/
```

可用的内置主题有：default, pink, sticky
